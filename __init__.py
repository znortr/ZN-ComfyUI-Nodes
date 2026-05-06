
from .ZN_Adv_Prompt import ZN_Adv_Prompt
from .ZN_ImagePreviewSaveAdv import ZN_ImagePreviewSaveAdv
from .ZN_ImageMask_Bridge import ZN_ImageMask_Bridge
from .ZN_Opt_Resolution import ZN_Opt_Resolution
from .ZN_Nearest_Resolution import ZN_Nearest_Resolution
from .ZN_Smart_Bypasser import ZN_Smart_Bypasser
from .ZN_Lora_Helper import ZN_Lora_Helper
from .ZN_SeedVR2_Controller import ZN_SeedVR2_Controller
from .ZN_Wan_Video_Settings import ZN_Wan_Video_Settings

NODE_CLASS_MAPPINGS = {
    "ZN_Adv_Prompt": ZN_Adv_Prompt,
    "ZN_ImagePreviewSaveAdv": ZN_ImagePreviewSaveAdv,
    "ZN_ImageMask_Bridge" : ZN_ImageMask_Bridge,
    "ZN_Opt_Resolution" : ZN_Opt_Resolution,
    "ZN_Nearest_Resolution" : ZN_Nearest_Resolution,
    "ZN_Smart_Bypasser" : ZN_Smart_Bypasser,
    "ZN_Lora_Helper" : ZN_Lora_Helper,
    "ZN_SeedVR2_Controller" : ZN_SeedVR2_Controller,
    "ZN_Wan_Video_Settings" : ZN_Wan_Video_Settings,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ZN_Adv_Prompt": "⧉ ZN Advanced Prompt (by Model)",
    "ZN_ImagePreviewSaveAdv": "⧉ ZN Image Preview & Save ADV",
    "ZN_ImageMask_Bridge" : "⧉ ZN Image & Mask Bridge",
    "ZN_Opt_Resolution" : "⧉ ZN Optimal Resolutions (by Model)",
    "ZN_Nearest_Resolution" : "⧉ ZN Nearest Resolution (by Model)",
    "ZN_Smart_Bypasser" : "⧉ ZN Smart Bypasser",
    "ZN_Lora_Helper" : "⧉ ZN LoRA Helper",
    "ZN_SeedVR2_Controller" : "⧉ ZN SeedVR2 Smart Controller (VRAM Aware)",
    "ZN_Wan_Video_Settings" : "⧉ Zn Wan Video Settings",
}

# Questo è sufficiente per caricare i tuoi file .js
WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]