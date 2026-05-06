# ZN_Wan_Video_Settings.py
# Node: Wan Video Settings — video configuration node (clean INT version)

import math

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

def register_node(identifier: str, display_name: str):
    def decorator(cls):
        NODE_CLASS_MAPPINGS[identifier] = cls
        NODE_DISPLAY_NAME_MAPPINGS[identifier] = display_name
        return cls
    return decorator


@register_node("ZN_Wan_Video_Settings", "WanVideoSettings")
class ZN_Wan_Video_Settings:
    """
    Wan Video Settings — nodo di configurazione video per workflow Wan/Video.
    Outputs:
    - width (INT)
    - height (INT)
    - length (INT) → numero totale frame
    - rife_multiply (INT) → 1 = Disabled
    - fps (FLOAT) → fps finale dopo moltiplicatore
    """

    DESCRIPTION = (
            "⭐ Zn Wan Video Settings — Central configuration hub for WanVideo workflows.\n\n"
            "This node acts as a 'Single Point of Truth' for video dimensions, timing, and sampling split, "
            "eliminating manual math and ensuring consistency across the entire pipeline.\n\n"
            "MAIN FEATURES:\n"
            "• Optimal Presets: Quickly switch between WanVideo-optimized resolutions.\n"
            "• Smart Frame Math: Automatically calculates the exact frame count (Length) "
            "required to reach your target duration in seconds.\n"
            "• Interpolation Ready: Includes RIFE multiplier logic to compute the final FPS.\n"
            "• Smart Step Logic: Automatically partitions sampling steps between High-res and Low-res phases\n\n"
            "OUTPUTS:\n"
            "• width/height: Accurate pixel values for latent/sampling nodes.\n"
            "• length: Total frame count calculated as: (Duration × Base FPS) + 1.\n"
            "• fps: The final frame rate after RIFE multiplication (Base FPS × RIFE).\n"
            "• steps_total: The total number of sampling steps to be used in KSamplers.\n"
            "• high_end: The point where the High-resolution (initial) sampling phase ends.\n"
            "• low_start: The point where the Low-resolution (refinement) sampling phase begins (matches high_end)."
        )

    NAME = "Zn Wan Video Settings"
    FUNCTION = "execute"
    CATEGORY = "Znort/Wan_Video"

    VIDEO_SIZES = {
        "🟩 Square Standard   | 512×512    | 1:1":        (512, 512),
        "🟩 Widescreen Light  | 640×360    | 16:9":       (640, 360),
        "🟩 Vertical Social   | 384×640    | 9:16":       (384, 640),
        "🟨 HQ 4:3            | 640×480    | 4:3":        (640, 480),
        "🟥 Extended 720p     | 960×540    | 16:9":       (960, 540),
        "🟥 Full 720p         | 1280×720   | 16:9":       (1280, 720),
    }

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_size": (
                    list(cls.VIDEO_SIZES.keys()),
                    {
                        "default": "🟩 Square Standard   | 512×512    | 1:1",
                        "tooltip": "Select the video resolution.\n"
                                   "The output provides corresponding width and height for your latent/model."
                    }
                ),

                "duration_sec": (
                    "FLOAT",
                    {
                        "default": 4.0,
                        "min": 0.1,
                        "max": 9999.0,
                        "step": 0.1,
                        "tooltip": "Total video duration in seconds.\n"
                                   "Frame calculation: length = round(duration × fps_base) + 1"
                    }
                ),

                "fps_base": (
                    "FLOAT",
                    {
                        "default": 12.0,
                        "min": 1.0,
                        "max": 240.0,
                        "step": 1.0,
                        "tooltip": "Native generation frame rate.\n"
                                   "This is the 'internal' speed the AI model uses to generate motion. "
                                   "Higher values produce more unique AI-generated frames but increase VRAM/Render time. "
                                   "If using RIFE, this serves as the starting point for interpolation."
                    }
                ),

                "rife_multiply": (
                    "INT",
                    {
                        "default": 1,
                        "min": 1,
                        "max": 16,
                        "tooltip": "Frame Interpolation (RIFE) multiplier.\n"
                                   "1 = Disabled: The video stays at the base FPS.\n"
                                   ">1 = Enabled: Artificially increases fluid motion by creating intermediate frames. "
                                   "Example: 12 FPS (base) × 2 (RIFE) = 24 FPS final output."
                    }
                ),
                # SEZIONE STEP
                "total_steps": (
                    "INT", 
                    {
                        "default": 8, "min": 1, "max": 100, "step": 1,
                        "tooltip": "Numero totale di passi di campionamento (es. 6 o 8)."
                    }
                ),
                "split_mode": (
                    ["Balanced (50/50)", "Detail (60/40)", "Motion Clean (40/60)", "Custom %"], 
                    {
                        "default": "Motion Clean (40/60)",
                        "tooltip": "Sceglie come dividere gli step tra la fase High e Low."
                    }
                ),
                "custom_split_pct": (
                    "FLOAT", 
                    {
                        "default": 50.0, "min": 0.0, "max": 100.0, "step": 1.0,
                        "tooltip": "Percentuale di step per la fase High (usato solo in Custom %)."
                    }
                ),
            }
        }

    RETURN_TYPES = (
        "INT",   # width
        "INT",   # height
        "INT",   # length (frame count)
        "INT",   # rife_multiply (always INT)
        "FLOAT", # fps final
        "INT",   # total steps
        "INT",   # hight end
        "INT",   # Low start
    )

    RETURN_NAMES = (
        "width",
        "height",
        "length",
        "rife_multiply",
        "fps",
        "steps_total", 
        "high_end", 
        "low_start",
    )

    def execute(self, video_size, duration_sec, fps_base, rife_multiply, total_steps, split_mode, custom_split_pct):

        # 1. Resolution
        width, height = self.VIDEO_SIZES[video_size]

        # 2. Ensure correct types
        duration = float(duration_sec)
        fps_base_val = float(fps_base)
        rife_val = int(rife_multiply)
        steps_total_val = int(total_steps)

        # 3. Frame count (INT)
        length = int(round(duration * fps_base_val)) + 1

        # 4. Final FPS
        fps_final = fps_base_val * rife_val

        # 5. Step Partitioning Logic (Smart Split)
        if split_mode == "Balanced (50/50)":
            pct = 0.50
        elif split_mode == "Detail (60/40)":
            pct = 0.60
        elif split_mode == "Motion Clean (40/60)":
            pct = 0.40
        else:
            pct = float(custom_split_pct) / 100.0

        # Calcolo del punto di split (intero)
        split_point = int(math.floor(steps_total_val * pct))

        # Safety Check: evita valori 0 o superiori al totale
        if split_point < 1: 
            split_point = 1
        if split_point >= steps_total_val: 
            split_point = steps_total_val - 1

        # 6. Return values (devono essere 8 come definito in RETURN_TYPES)
        return (
            int(width),
            int(height),
            int(length),
            int(rife_val),
            float(fps_final),
            int(steps_total_val),
            int(split_point), # high_end
            int(split_point), # low_start
        )

NODE_CLASS_MAPPINGS = {
"ZN_Wan_Video_Settings": ZN_Wan_Video_Settings
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ZN_Wan_Video_Settings": "⧉ Zn Wan Video Settings"
}