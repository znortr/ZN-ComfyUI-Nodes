import json
import os
import torch
import numpy as np
from PIL import Image, ImageOps

# -------------------------
# Utils
# -------------------------

def tensor_to_pil(t):
    if t.dim() == 4:
        t = t[0]

    if t.dim() != 3:
        raise ValueError(f"Unsupported image tensor shape: {t.shape}")

    arr = (t.cpu().numpy() * 255).clip(0, 255).astype(np.uint8)
    return Image.fromarray(arr)

def mask_to_pil(m):
    if m.dim() == 3:
        m = m[0]
    arr = (m.cpu().numpy() * 255).clip(0, 255).astype(np.uint8)
    return Image.fromarray(arr, mode="L")

def pil_to_tensor(img):
    arr = np.array(img).astype(np.float32) / 255.0
    return torch.from_numpy(arr)[None, ...]

def pil_to_mask(img):
    arr = np.array(img.convert("L")).astype(np.float32) / 255.0
    return torch.from_numpy(arr)[None, ...]


# -------------------------
# Node
# -------------------------

class ZN_Nearest_Resolution:
    """
    ZN Nearest Resolution (Enhanced)

    - Stable scoring (aspect ratio + megapixel)
    - Resolution ID support (pipeline-safe)
    - Robust JSON handling
    - Improved resize logic
    - Optional Mask support
    """

    DESCRIPTION = (
        "Matches an image (single image only) to the closest resolution defined in the selected model preset.\n\n"
        "Selection is based on aspect ratio, megapixels, and priority weight.\n"
        "Each model provides its own optimized resolution set.\n\n"
        "Supports multiple resize strategies: fill, fit, crop, pad, letterbox, stretch.\n"
        "If a mask is connected, it will be resized with the same parameters."
    )

    NAME = "ZN Nearest Resolution (by Model)"
    FUNCTION = "process"
    CATEGORY = "Znort/Util"
        
    @classmethod
    def INPUT_TYPES(s):
        json_path = os.path.join(os.path.dirname(__file__), "presets", "resolution_preset.json")

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            model_names = [k for k in data.keys() if k != "settings"]
        except Exception:
            model_names = ["None"]

        return {
            "required": {
                "image": ("IMAGE", {
                    "tooltip": "The image to be adapted to the model's target resolution."
                }),
                "model_name": (model_names, {
                    "tooltip": (
                        "Select the target model.\n"
                        "Available resolutions are defined in:\n"
                        "presets/resolution_preset.json"
                    )
                }),
                "method": ([
                    "fill",
                    "fit",
                    "crop",
                    "pad",
                    "letterbox",
                    "stretch"
                ], {
                    "tooltip": (
                        "Resize method:\n"
                        "• fill → fills entire frame, crops excess\n"
                        "• fit → preserves aspect ratio, adds borders\n"
                        "• crop → centered crop\n"
                        "• pad → adds padding around image\n"
                        "• letterbox → symmetric padding (cinematic bars)\n"
                        "• stretch → deforms image to fit"
                    )
                }),
                "interpolation": ([
                    "lanczos",
                    "bicubic",
                    "bilinear",
                    "nearest"
                ], {
                    "tooltip": (
                        "Interpolation algorithm:\n"
                        "• lanczos → highest quality\n"
                        "• bicubic → best quality/performance balance\n"
                        "• bilinear → faster, medium quality\n"
                        "• nearest → pixel art / no smoothing"
                    )
                }),
            },
            "optional": {
                "mask": ("MASK", {"tooltip": "Optional mask to resize alongside the image."}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK", "INT", "INT", "STRING")
    RETURN_NAMES = ("image", "mask", "width", "height", "debug")

    def process(self, image, model_name, method, interpolation, mask=None):

        # --- LOAD & VALIDATE PRESET (CACHED) ---
        if not hasattr(self, "_cached_presets"):
            json_path = os.path.join(os.path.dirname(__file__), "presets", "resolution_preset.json")
            if not os.path.exists(json_path):
                raise FileNotFoundError(f"Missing preset file: {json_path}")
            with open(json_path, "r", encoding="utf-8") as f:
                self._cached_presets = json.load(f)

        presets = self._cached_presets

        if model_name not in presets:
            raise ValueError(f"Model '{model_name}' not found in preset file")

        model_preset = presets[model_name]

        if "resolutions" not in model_preset or not isinstance(model_preset["resolutions"], list):
            raise ValueError(f"Preset for model '{model_name}' is missing a valid 'resolutions' list")

        resolutions = model_preset["resolutions"]


        pil = tensor_to_pil(image)
        # --- SINGLE IMAGE ONLY ENFORCEMENT ---
        if image.dim() == 4 and image.shape[0] != 1:
            raise ValueError(f"ZN_Nearest_Resolution supports only single-image input. Received batch size: {image.shape[0]}")


        w_in, h_in = pil.size
        ar_in = w_in / h_in
        mp_in = (w_in * h_in) / 1_000_000

        interp = {
            "lanczos": Image.LANCZOS,
            "bicubic": Image.BICUBIC,
            "bilinear": Image.BILINEAR,
            "nearest": Image.NEAREST
        }[interpolation]

        # color priority weights
        color_weight = {"🟩": 1, "🟨": 2, "🟥": 4}

        best = None
        best_score = float("inf")

        # -------------------------
        # Resolution selection
        # -------------------------
        for r in resolutions:
            w, h = r["width"], r["height"]

            ar = w / h
            mp = (w * h) / 1_000_000

            # safe color extraction
            color = r["name"][0] if r.get("name") else "⬜"
            weight = color_weight.get(color, 3) * 0.5  # softened impact

            d_ar = min(abs(ar - ar_in), 1.0)  # clamp outliers
            d_mp = abs(mp - mp_in)

            # balanced scoring
            score = (d_ar * 0.7) + (d_mp * 0.3) + weight

            if score < best_score:
                best_score = score
                best = r

        if best is None:
            raise RuntimeError("No valid resolution found")

        target_w = best["width"]
        target_h = best["height"]
        res_name = best.get("name", "unknown")
        res_id = best.get("id", res_name)

        # -------------------------
        # Unified Resize Logic
        # -------------------------
        def apply_resize_logic(source_pil, is_mask=False):
            # Per le maschere usiamo bilinear se l'utente ha scelto qualcosa di troppo pesante,
            # o nearest se l'utente ha scelto nearest.
            current_interp = interp
            # Masks should not use high-quality filters (avoid gray edges)
            if is_mask:
                current_interp = Image.NEAREST if interpolation == "nearest" else Image.BILINEAR

            
            # Parametri di compatibilità Pillow
            FIT_USES_RESAMPLE = "resample" in ImageOps.fit.__code__.co_varnames
            PAD_USES_RESAMPLE = "resample" in ImageOps.pad.__code__.co_varnames
            
            fill_color = 0 if is_mask else (0, 0, 0)

            if method in ["fill", "crop"]:
                if FIT_USES_RESAMPLE:
                    return ImageOps.fit(source_pil, (target_w, target_h), resample=current_interp)
                else:
                    return ImageOps.fit(source_pil, (target_w, target_h), method=current_interp)

            elif method in ["fit", "pad"]:
                img_copy = source_pil.copy()
                img_copy.thumbnail((target_w, target_h), current_interp)
                out = Image.new(source_pil.mode, (target_w, target_h), fill_color)
                out.paste(
                    img_copy,
                    ((target_w - img_copy.width) // 2, (target_h - img_copy.height) // 2)
                )
                return out

            elif method == "letterbox":
                if PAD_USES_RESAMPLE:
                    return ImageOps.pad(source_pil, (target_w, target_h), resample=current_interp, color=fill_color)
                else:
                    return ImageOps.pad(source_pil, (target_w, target_h), method=current_interp, color=fill_color)

            elif method == "stretch":
                return source_pil.resize((target_w, target_h), current_interp)

            else:
                return source_pil.resize((target_w, target_h), current_interp)

        # Esegui resize Immagine
        out_image_pil = apply_resize_logic(pil, is_mask=False)
        
        # Esegui resize Maschera (se presente)
        if mask is not None:
            mask_pil = mask_to_pil(mask)
            out_mask_pil = apply_resize_logic(mask_pil, is_mask=True)
            out_mask_tensor = pil_to_mask(out_mask_pil)
        else:
            # Ritorna maschera vuota se non collegata
            out_mask_tensor = torch.zeros(
                (1, target_h, target_w),
                dtype=image.dtype,
                device=image.device
            )

        # -------------------------
        # Debug output (ORIGINAL SMART LOGIC)
        # -------------------------

        def describe_delta(value):
            if value < 0.05: return "Very Low"
            elif value < 0.15: return "Low"
            elif value < 0.35: return "Medium"
            else: return "High"

        def describe_weight(w):
            if w <= 0.5: return "Preferred (🟩)"
            elif w <= 1.0: return "Allowed (🟨)"
            else: return "Discouraged (🟥)"

        def describe_score(score):
            if score < 0.6: return "Excellent match"
            elif score < 1.0: return "Good match"
            elif score < 1.5: return "Acceptable match"
            else: return "Poor match"

        sel_w, sel_h = target_w, target_h
        sel_ar = sel_w / sel_h
        sel_mp = (sel_w * sel_h) / 1_000_000
        sel_d_ar = abs(sel_ar - ar_in)
        sel_d_mp = abs(sel_mp - mp_in)

        color = res_name[0] if res_name else "⬜"
        weight = color_weight.get(color, 3) * 0.5
        score = (min(sel_d_ar, 1.0) * 0.7) + (sel_d_mp * 0.3) + weight

        debug_lines = [
            "=== Resolution Match ===",
            f"Model: {model_name}",
            "",
            "Input Image:",
            f"  • Size            : {w_in} x {h_in}",
            f"  • Aspect Ratio    : {ar_in:.3f}",
            f"  • Megapixels      : {mp_in:.3f}",
            "",
            "Selected Resolution:",
            f"  • Name            : {res_name}",
            f"  • ID              : {res_id}",
            f"  • Size            : {target_w} x {target_h}",
            "",
            "Match Analysis:",
            f"  • Match Quality   : {describe_score(score)}",
            f"  • Aspect Ratio    : {describe_delta(sel_d_ar)} (Δ {sel_d_ar:.3f})",
            f"  • Size Difference : {describe_delta(sel_d_mp)} (Δ {sel_d_mp:.3f} MP)",
            f"  • Model Priority  : {describe_weight(weight)}",
            "",
            "Notes:",
            "  • Lower aspect ratio difference = less cropping or distortion",
            "  • Lower size difference = less scaling artifacts",
            "  • Model priority influences preferred resolutions",
            f"  • Mask processed: {'Yes' if mask is not None else 'No'}"
        ]

        debug_str = "\n".join(debug_lines)

        return (
            pil_to_tensor(out_image_pil),
            out_mask_tensor,
            target_w,
            target_h,
            debug_str
        )


# -------------------------
# ComfyUI registration
# -------------------------

NODE_CLASS_MAPPINGS = {
    "ZN_Nearest_Resolution": ZN_Nearest_Resolution
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ZN_Nearest_Resolution": "⧉ ZN Nearest Resolution (by Model)"
}