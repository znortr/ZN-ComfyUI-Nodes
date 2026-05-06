import os
import json
import math
import torch
import comfy.model_management as mm

from aiohttp import web
from server import PromptServer

class ZN_Opt_Resolution:
    """
    Advanced resolution manager with model-specific presets and MP scaling.
    """

    DESCRIPTION = (
        "A smart resolution manager that handles optimal resolutions based on the selected model. "
        "Automatically calculates the correct latent size, ensures dimensions follow model requirements "
        "(e.g., multiples of 8 or 16), and allows scaling by Megapixel targets. "
        "All additions to 'resolution_preset.json' are automatically managed and updated in the UI."
    )

    NAME = "ZN Optimal Resolutions (by Model)"
    FUNCTION = "Opt_Resolution"
    CATEGORY = "Znort/Util"

    RETURN_TYPES = ("INT", "INT", "LATENT", "STRING")
    RETURN_NAMES = ("width", "height", "latent", "info")


    @staticmethod
    def _load_json(filename):
        base = os.path.dirname(os.path.realpath(__file__))
        path = os.path.join(base, "presets", filename)
        if not os.path.exists(path):
            return {"settings": {"mp_map": {}, "rounding_modes": [], "device_options": []}}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"settings": {"mp_map": {}, "rounding_modes": [], "device_options": []}}

    @classmethod
    def INPUT_TYPES(cls):
        presets = cls._load_json("resolution_preset.json")
        model_names = [k for k in presets.keys() if k != "settings"]
        
        return {
            "required": {
                "model_name": (model_names if model_names else ["None"], {"tooltip": "Select the model architecture (Flux, SDXL, etc.)"}),
                "resolution": ("STRING", {"default": "Manual", "tooltip": "Choose a preset aspect ratio or 'Manual' for custom sizing"}), 
                "target_megapixels": (["Preset", "1.0 MP", "2.0 MP"], {"tooltip": "Scale the resolution to a specific Megapixel target"}),
                "width": ("INT", {"default": 1024, "min": 64, "max": 8192, "tooltip": "Input width (automatically set by presets)"}),
                "height": ("INT", {"default": 1024, "min": 64, "max": 8192, "tooltip": "Input height (automatically set by presets)"}),
                "batch_size": ("INT", {"default": 1, "min": 1, "max": 64, "tooltip": "Number of latent samples"}),
                "rounding_mode": (["nearest", "floor", "ceil"], {"tooltip": "How to round dimensions to the model's multiple"}),
                "device": (["cuda", "default", "cpu"], {"tooltip": "Hardware device for latent generation"}),
            }
        }

    def Opt_Resolution(self, model_name, resolution, target_megapixels, width, height, batch_size, rounding_mode, device):
        presets = self._load_json("resolution_preset.json")
        settings = presets.get("settings", {})
        mp_map = settings.get("mp_map", {})
        model = presets.get(model_name)

        if not model:
            raise ValueError(f"Modello non trovato: {model_name}")

        selected_res = None
        if resolution and resolution != "Manual":
            for r in model["resolutions"]:
                if r["name"] == resolution:
                    selected_res = r
                    break

        if selected_res:
            width = int(selected_res["width"])
            height = int(selected_res["height"])
        
        mp = mp_map.get(target_megapixels, 0.0)
        if resolution == "Manual" and mp > 0:
            aspect = width / max(height, 1)
            target_area = mp * 1_000_000
            new_h = math.sqrt(target_area / aspect)
            new_w = new_h * aspect
            max_size = model["max_size"]
            scale = min(max_size / new_w, max_size / new_h, 1.0)
            width = int(new_w * scale)
            height = int(new_h * scale)

        mul = model["resolution_multiple"]
        def round_val(v):
            if rounding_mode == "floor": return (v // mul) * mul
            if rounding_mode == "ceil": return math.ceil(v / mul) * mul
            return int((v + mul / 2) // mul) * mul

        if resolution == "Manual":
            width = round_val(width)
            height = round_val(height)

        down = model["latent_downscale"]
        ch = model["latent_channels"]
        latent_shape = (batch_size, ch, height // down, width // down)

        if device == "default": dev = mm.get_torch_device()
        elif device == "cpu": dev = torch.device("cpu")
        elif device == "cuda": dev = torch.device("cuda")
        else: dev = mm.get_torch_device()

        #latent = {"samples": torch.randn(latent_shape, device=dev)}

        # --- LATENT GENERATION (FULLY JSON-DRIVEN) ---
        # Load dtype mapping from settings
        settings = presets.get("settings", {})
        dtype_map = settings.get("dtype_mapping", {})

        latent_dtype_str = model.get("latent_dtype", "float32")
        latent_dtype_expr = dtype_map.get(latent_dtype_str, "torch.float32")
        latent_dtype = eval(latent_dtype_expr)

        latent_mode = model.get("latent_mode", "random")
        latent_value = float(model.get("latent_value", 0.0))

        if latent_mode == "constant":
            samples = torch.full(
                latent_shape,
                latent_value,
                device=dev,
                dtype=latent_dtype
            )
        else:
            samples = torch.randn(
                latent_shape,
                device=dev,
                dtype=latent_dtype
            )

        latent = {"samples": samples}


        # -----------------------

        info = f"{model_name} | {width}x{height}"
        return (width, height, latent, info)

async def get_presets_handler(request):
    try:
        data = ZN_Opt_Resolution._load_json("resolution_preset.json")
        return web.json_response(data)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

try:
    if hasattr(PromptServer, "instance") and PromptServer.instance is not None:
        routes = PromptServer.instance.routes
        if not any(r.path == "/znodes/resolution_presets" for r in routes):
            PromptServer.instance.routes.get("/znodes/resolution_presets")(get_presets_handler)
except Exception as e:
    print(f"[ZN Nodes] Errore API: {e}")

NODE_CLASS_MAPPINGS = {"ZN_Opt_Resolution": ZN_Opt_Resolution}
NODE_DISPLAY_NAME_MAPPINGS = {"ZN_Opt_Resolution": "⧉ ZN Optimal Resolutions (by Model)"}