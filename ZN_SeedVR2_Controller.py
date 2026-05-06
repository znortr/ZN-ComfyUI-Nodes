import torch

class ZN_SeedVR2_Controller:
    """
    SeedVR2 Smart Controller (Full-Frame Quality Mode + VRAM Aware)
    This node DOES NOT perform upscaling.
    It computes the target resolution (short side) for SeedVR2,
    and dynamically adjusts VAE tiling based on available VRAM.
    specific only for SeedVR2.
    """

    DESCRIPTION = (
        "SeedVR2 VAE tilling controller with VRAM-aware tiling.\n\n"
        "Computes target resolution from input image.\n"
        "Does NOT perform upscaling.\n\n"
        "Forces Full-Frame processing and auto-adjusts VAE tiles.\n"
        "ONLY for SeedVR2."
    )

    NAME = "ZN SeedVR2 Smart Controller (VRAM Aware)"
    FUNCTION = "compute"
    CATEGORY = "Znort/Upscale_Logic"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE", {
                    "tooltip": "Input image. Used only to read resolution and proportions."
                }),

                "mode": (["scale_factor", "target_short_side"], {
                    "tooltip": (
                        "How to define target resolution:\n"
                        "- scale_factor: multiply original short side\n"
                        "- target_short_side: set exact short side in pixels"
                    )
                }),

                "scale_factor": ("FLOAT", {
                    "default": 1.0,
                    "min": 1.0,
                    "max": 8.0,
                    "step": 0.1,
                    "tooltip": (
                        "Multiplier for computing target short side.\n\n"
                        "1.0 = original size\n"
                        "2.0 = double resolution\n\n"
                        "NOTE: This does NOT upscale the image.\n"
                        "It only defines the resolution passed to SeedVR2."
                    )
                }),

                "target_short_side": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 8192,
                    "step": 8,
                    "tooltip": (
                        "Target size for the shortest side (in pixels).\n\n"
                        "Overrides scale_factor if > 0."
                    )
                }),

                "vram_profile": (["auto", "8GB", "12GB", "24GB"], {
                    "default": "12GB",
                    "tooltip": (
                        "Controls VAE tile size for VRAM safety.\n\n"
                        "12GB (default) is recommended for most users.\n"
                        "Auto will estimate GPU VRAM (conservative).\n"
                        "Lower VRAM → smaller tiles (safer, slower).\n"
                        "Higher VRAM → larger tiles (better quality)."
                    )
                }),
            }
        }

    RETURN_TYPES = ("FLOAT", "INT", "INT", "INT", "STRING")
    RETURN_NAMES = (
        "final_scale",
        "final_short_side",
        "vae_tile_size",
        "vae_overlap",
        "debug_info"
    )

    def compute(self, image, mode, scale_factor, target_short_side, vram_profile):

        # -------------------------
        # 1. IMAGE SHAPE
        # -------------------------
        if len(image.shape) == 4:
            _, h, w, _ = image.shape
        elif len(image.shape) == 3:
            h, w, _ = image.shape
        else:
            raise ValueError(f"Unexpected image shape: {image.shape}")

        orig_short = max(1, min(w, h))

        # -------------------------
        # 2. TARGET SHORT SIDE
        # -------------------------
        if mode == "target_short_side" and target_short_side > 0:
            requested_short = target_short_side
            requested_scale = requested_short / orig_short
            active_mode = "target_short_side"
        else:
            requested_scale = max(1.0, float(scale_factor))
            requested_short = int(orig_short * requested_scale)
            active_mode = "scale_factor"

        # -------------------------
        # 3. FINAL DIMENSIONS
        # -------------------------
        scaled_w = (int(round(w * requested_scale)) // 8) * 8
        scaled_h = (int(round(h * requested_scale)) // 8) * 8

        final_short = min(scaled_w, scaled_h)
        final_scale = final_short / orig_short

        # -------------------------
        # 4. VRAM PROFILE RESOLUTION
        # -------------------------
        if vram_profile == "auto":
            try:
                total_vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)

                if total_vram < 10:
                    profile = "8GB"
                elif total_vram < 18:
                    profile = "12GB"
                else:
                    profile = "24GB"
            except:
                profile = "12GB"  # safe fallback
        else:
            profile = vram_profile

        # -------------------------
        # 5. BASE TILE BY VRAM
        # -------------------------
        if profile == "8GB":
            base_tile = 512
        elif profile == "12GB":
            base_tile = 768
        else:  # 24GB
            base_tile = 1024

        # -------------------------
        # 6. ADAPT TILE TO RESOLUTION
        # -------------------------
        if final_short <= 1536:
            v_tile = base_tile
        elif final_short <= 2560:
            v_tile = int(base_tile * 0.75)
        else:
            v_tile = int(base_tile * 0.5)

        # clamp minimo sicurezza
        v_tile = max(256, int(v_tile // 8) * 8)

        # overlap dinamico
        v_overlap = min(v_tile // 4, max(32, int(v_tile * 0.1)))

        # -------------------------
        # 7. DEBUG INFO
        # -------------------------
        debug_info = (
            f"mode={active_mode} | "
            f"input={w}x{h} | "
            f"input_short={orig_short} | "
            f"target_short={requested_short} | "
            f"final_res={scaled_w}x{scaled_h} | "
            f"scale={requested_scale:.2f} (actual={final_scale:.2f}) | "
            f"vram_profile={profile} | "
            f"vae_tile={v_tile} | "
            f"vae_overlap={v_overlap} | "
            f"upscale_mode=FULL_FRAME | "
            f"model=SeedVR2_only"
        )

        return (
            float(final_scale),
            int(final_short),
            int(v_tile),
            int(v_overlap),
            debug_info
        )


NODE_CLASS_MAPPINGS = {
    "ZN_SeedVR2_Controller": ZN_SeedVR2_Controller
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ZN_SeedVR2_Controller": "⧉ ZN SeedVR2 Smart Controller (VRAM Aware)"
}