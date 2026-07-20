import hashlib
import logging

import torch
import comfy.model_management as mm
import comfy


class ZN_SmartFlusher:
    """
    ZN Smart Flusher — Auto-clears the model cache when your prompt changes.

    Based on the working ZN_CacheManager, expanded with:
      - Optional VRAM threshold safety check
      - Force flush switch: ON = flush every run; OFF = smart flush on change/low VRAM
      - Aggressive torch.cuda.empty_cache() option
      - Pass-through data input/output (any type)
      - Pass-through conditioning output (positive if available, else negative)

    By default, the VRAM check is disabled so the node behaves like
    ZN_CacheManager and does not unload the model merely because free VRAM is low.
    """

    DESCRIPTION = (
        "Smart cache flusher — clears model cache (and optionally node cache). "
        "When Force Flush is OFF, it flushes only when conditioning changes OR "
        "when the optional VRAM safety guard detects low VRAM. When Force Flush "
        "is ON, it flushes on every run. Keeps the cache hot when nothing changed. "
        "Pass-through any data and conditioning."
    )

    # Class-level state persists across executions in the same ComfyUI session
    _conditioning_state = {}
    _SAMPLES = 500

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "clear_node_cache": ("BOOLEAN", {
                    "default": True,
                    "tooltip": (
                        "Also reset ComfyUI's node execution cache. When enabled, "
                        "this is equivalent to the UI button 'Free model and node cache'."
                    )
                }),
                "force_flush": ("BOOLEAN", {
                    "default": False,
                    "tooltip": (
                        "ON: flush cache on EVERY run (equivalent to 'always' mode). "
                        "OFF: smart flush — only when conditioning changes or the "
                        "optional VRAM guard detects low VRAM."
                    )
                }),
                "use_vram_guard": ("BOOLEAN", {
                    "default": False,
                    "tooltip": (
                        "Enable the VRAM safety check. When OFF, low free VRAM does "
                        "not trigger a flush. Recommended OFF for normal operation "
                        "so the model cache stays hot."
                    )
                }),
                "vram_threshold_gb": ("FLOAT", {
                    "default": 1.5,
                    "min": 0.1,
                    "max": 64.0,
                    "step": 0.1,
                    "tooltip": (
                        "When the VRAM safety check is enabled, cleanup triggers "
                        "when currently free VRAM is below this value, regardless "
                        "of Force Flush."
                    )
                }),
                "aggressive": ("BOOLEAN", {
                    "default": False,
                    "tooltip": (
                        "Also calls torch.cuda.empty_cache() after cleanup. "
                        "Releases unused PyTorch VRAM blocks, but may add ~50–200 ms. "
                        "Enable only when standard cleanup is insufficient."
                    )
                }),
            },
            "optional": {
                "data": ("*", {
                    "tooltip": "Any type. Passed through unchanged to the 'data' output."
                }),
                "positive_conditioning": ("CONDITIONING", {
                    "tooltip": "Changes here trigger smart cleanup. Also passed to the 'conditioning' output if connected."
                }),
                "negative_conditioning": ("CONDITIONING", {
                    "tooltip": "Changes here trigger smart cleanup."
                }),
            },
            "hidden": {"unique_id": "UNIQUE_ID"}
        }

    RETURN_TYPES = ("*", "CONDITIONING", "STRING")
    RETURN_NAMES = ("data", "conditioning", "status")
    FUNCTION = "process"
    CATEGORY = "ZN/Cache"

    # ──────────────────────────────────────────────────────────────────────────
    # Hash utilities (same lightweight approach as ZN_CacheManager)
    # ──────────────────────────────────────────────────────────────────────────

    @classmethod
    def _hash_conditioning(cls, conditioning):
        """Fast hash of the primary conditioning tensor for change detection."""
        if conditioning is None:
            return "disconnected"
        if not isinstance(conditioning, list) or not conditioning:
            return "empty"
        try:
            tensor = conditioning[0][0]
            if not isinstance(tensor, torch.Tensor):
                return "empty"
            flat = tensor.detach().flatten()
            sample_size = min(cls._SAMPLES, flat.numel())
            if sample_size == 0:
                return "empty_tensor"

            indices = torch.linspace(
                0, flat.numel() - 1, sample_size,
                dtype=torch.long, device=flat.device
            )
            sample = flat[indices]
            key = (
                f"{list(tensor.shape)}|{tensor.dtype}|"
                f"{sample.sum().item():.8f}|{sample.std().item():.8f}"
            )
            return hashlib.md5(key.encode("utf-8")).hexdigest()
        except Exception as exc:
            logging.warning("[ZN Smart Flusher] Conditioning fingerprint failed: %s", exc)
            return "hash_error"

    # ──────────────────────────────────────────────────────────────────────────
    # VRAM check
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _get_free_vram_gb():
        try:
            if torch.cuda.is_available():
                free_bytes, _ = torch.cuda.mem_get_info()
                return free_bytes / (1024 ** 3)
        except Exception as exc:
            logging.warning("[ZN Smart Flusher] VRAM query failed: %s", exc)
        return None

    # ──────────────────────────────────────────────────────────────────────────
    # Cache clearing (same as ZN_CacheManager — PROVEN TO WORK)
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _clear_model_cache():
        """Clear model cache (replicates 'Free Model Cache' button)."""
        try:
            mm.unload_all_models()
            mm.soft_empty_cache(True)
            return True
        except Exception:
            return False

    @staticmethod
    def _clear_node_cache():
        """Clear node execution cache (replicates 'Free Node Cache' button)."""
        try:
            if hasattr(comfy, "nodes") and hasattr(comfy.nodes, "cache"):
                comfy.nodes.cache.clear()
            if hasattr(comfy, "prompt_cache"):
                comfy.prompt_cache.clear()
            return True
        except Exception:
            return False

    # ──────────────────────────────────────────────────────────────────────────
    # Main process
    # ──────────────────────────────────────────────────────────────────────────

    def process(self, force_flush, use_vram_guard, vram_threshold_gb,
                clear_node_cache, aggressive, data=None,
                positive_conditioning=None, negative_conditioning=None,
                unique_id=None):

        # ── Validation: at least one input must be connected ──
        if data is None and positive_conditioning is None and negative_conditioning is None:
            raise ValueError(
                "[ZN Smart Flusher] At least one input must be connected: "
                "'data', 'positive_conditioning', or 'negative_conditioning'."
            )

        node_id = str(unique_id) if unique_id is not None else "__unknown_node__"
        threshold = float(vram_threshold_gb if vram_threshold_gb is not None else 1.5)
        reasons = []
        should_flush = False

        # ── Optional VRAM safety check ──
        free_vram = None
        if use_vram_guard:
            free_vram = self._get_free_vram_gb()
            low_vram = free_vram is not None and free_vram < threshold
            if low_vram:
                reasons.append(f"VRAM_LOW:{free_vram:.2f}GB<{threshold:.2f}GB")
                should_flush = True
            elif free_vram is None:
                reasons.append("VRAM_UNAVAILABLE")
            else:
                reasons.append(f"VRAM_OK:{free_vram:.2f}GB")
        else:
            reasons.append("VRAM_GUARD_OFF")

        # ── Decide whether to flush ──
        if force_flush:
            should_flush = True
            reasons.insert(0, "FORCE")
        else:
            # Smart mode: check conditioning changes
            if positive_conditioning is None and negative_conditioning is None:
                reasons.insert(0, "SMART:NO_CONDITIONING")
            else:
                fingerprint = (
                    self._hash_conditioning(positive_conditioning),
                    self._hash_conditioning(negative_conditioning),
                )
                previous = self._conditioning_state.get(node_id)
                if previous is None:
                    reasons.insert(0, "SMART:FIRST_RUN")
                    should_flush = True
                elif fingerprint != previous:
                    reasons.insert(0, "SMART:CONDITIONING_CHANGED")
                    should_flush = True
                else:
                    reasons.insert(0, "SMART:CONDITIONING_UNCHANGED")
                self._conditioning_state[node_id] = fingerprint

        # ── Execute flush if needed ──
        if should_flush:
            ok = self._clear_model_cache()
            reasons.append("MODELS_OK" if ok else "MODELS_FAIL")
            if clear_node_cache:
                ok = self._clear_node_cache()
                reasons.append("NODES_OK" if ok else "NODES_FAIL")
            else:
                reasons.append("NODES_SKIPPED")
            if aggressive:
                try:
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                        reasons.append("AGGRESSIVE_EMPTY_CACHE")
                    else:
                        reasons.append("AGGRESSIVE_NO_CUDA")
                except Exception as exc:
                    logging.warning("[ZN Smart Flusher] aggressive empty_cache failed: %s", exc)
                    reasons.append(f"AGGRESSIVE_FAILED:{type(exc).__name__}")
        else:
            reasons.append("NO_CLEANUP_NEEDED")

        # ── Pass-through logic ──
        output_conditioning = (
            positive_conditioning
            if positive_conditioning is not None
            else negative_conditioning
        )
        return (data, output_conditioning, " | ".join(reasons))


NODE_CLASS_MAPPINGS = {"ZN_SmartFlusher": ZN_SmartFlusher}
NODE_DISPLAY_NAME_MAPPINGS = {"ZN_SmartFlusher": "ZN Smart Flusher"}
