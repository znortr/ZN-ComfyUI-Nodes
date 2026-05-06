import os
import torch
import numpy as np
import folder_paths
import nodes
from PIL import Image, ImageOps
import hashlib

# -------------------------------------------------------
# Dizionari globali per tenere traccia delle immagini
# -------------------------------------------------------
# _bridge_cache: unique_id -> (images_tensor, ui_image_list, content_hash, new_key)
#   FIX Bug 2: aggiunto content_hash per confronto affidabile
#   FIX Bug 1: aggiunto new_key per pulire le entry obsolete
_bridge_cache  = {}
_bridge_id_map = {}   # image_path_string -> (file_path, ui_item)


def _tensor_hash(t):
    """Hash stabile del contenuto del tensor immagine."""
    arr = t.cpu().numpy().tobytes()
    return hashlib.md5(arr).hexdigest()


class ZN_ImageMask_Bridge:

    """
    This node acts as a central Intermediary Hub for image and mask data management. 
    It is designed to simplify the workflow by receiving a single image input and 
    acting as a distribution point for multiple downstream nodes, reducing "noodle" 
    clutter in ComfyUI.

    Key Functionalities:
    - Image Passthrough: Receives a tensor image and re-transmits it without data loss.
    - Integrated Mask Editor: Allows users to manually define specific areas of interest 
      directly on the input image via the native Mask Editor.
    - Dual Output Stream: Provides simultaneous outputs for both IMAGE and MASK, 
      essential for Inpainting, Regional Prompts, or Targeted Upscaling.
    - Workflow Efficiency: Minimizes VRAM usage by referencing the same tensor 
      across multiple outputs.
    """

    DESCRIPTION = (
    "A multi-purpose routing bridge that transmits images while providing an integrated Mask Editor to create and output masks."
    )

    def __init__(self):
        self.output_dir = folder_paths.get_temp_directory()
        self.type = "temp"

    NAME = "ZN Image & Mask Bridge"
    CATEGORY = "Znort/Utils"
    FUNCTION = "do_bridge"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "image": ("STRING", {"default": ""}),
            },
            "hidden": {
                "unique_id":    "UNIQUE_ID",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES  = ("IMAGE", "MASK")
    RETURN_NAMES  = ("IMAGE", "MASK")
    OUTPUT_NODE   = True

    @staticmethod
    def _load_mask_from_file(file_path):
        img = Image.open(file_path)
        img = ImageOps.exif_transpose(img)
        if 'A' in img.getbands():
            alpha = np.array(img.getchannel('A')).astype(np.float32) / 255.0
            mask = 1.0 - torch.from_numpy(alpha)
            return mask.unsqueeze(0)
        return None

    @staticmethod
    def _resolve_clipspace(image_str):
        clean = image_str.replace(" [input]", "").replace("[input]", "")
        input_dir = folder_paths.get_input_directory()
        candidates = [
            clean,
            os.path.join(input_dir, clean),
            os.path.join(input_dir, "clipspace", os.path.basename(clean)),
            os.path.abspath(clean),
        ]
        for p in candidates:
            if os.path.isfile(p):
                return p
        return None

    @staticmethod
    def _make_ui_key(ui_item):
        """
        Ricostruisce la chiave che JS imposterà in imageWidget.value dopo onExecuted.
        JS fa: `${subfolder}/${filename} [${type}]` oppure `${filename} [${type}]`
        """
        sub   = ui_item.get("subfolder", "")
        fname = ui_item["filename"]
        ftype = ui_item["type"]
        return f"{sub}/{fname} [{ftype}]" if sub else f"{fname} [{ftype}]"

    def do_bridge(self, images, image, unique_id, extra_pnginfo=None):
        # FIX Bug 2: usa content hash invece dell'identità oggetto
        current_hash = _tensor_hash(images)

        need_refresh = False
        if unique_id not in _bridge_cache:
            need_refresh = True
        elif _bridge_cache[unique_id][2] != current_hash:   # [2] = stored hash
            need_refresh = True

        is_clipspace = bool(image) and (
            "clipspace" in image.lower() or "[input]" in image
        )

        # --- Caso A: clipspace (stessa immagine) ---
        if not need_refresh and is_clipspace:
            if image not in _bridge_id_map:
                file_path = self._resolve_clipspace(image)
                if file_path:
                    ui_item = {
                        "filename": os.path.basename(file_path),
                        "subfolder": "clipspace",
                        "type": "input",
                    }
                    _bridge_id_map[image] = (file_path, ui_item)
                else:
                    need_refresh = True

            if image in _bridge_id_map:
                file_path, ui_item = _bridge_id_map[image]
                mask = self._load_mask_from_file(file_path)
                if mask is None:
                    mask = torch.zeros((1, images.shape[1], images.shape[2]))

                if mask.shape[-2] != images.shape[1] or mask.shape[-1] != images.shape[2]:
                    mask = torch.nn.functional.interpolate(
                        mask.unsqueeze(1).float(),
                        size=(images.shape[1], images.shape[2]),
                        mode="nearest",
                    ).squeeze(1)

                return {
                    "ui": {
                        "images": [ui_item],
                        "image_hash": current_hash,
                    },
                    "result": (images, mask),
                }

        # --- Caso B: immagine già registrata (temp) ---
        if not need_refresh and image in _bridge_id_map:
            file_path, ui_item = _bridge_id_map[image]
            if os.path.isfile(file_path):
                mask = self._load_mask_from_file(file_path)
                if mask is None:
                    mask = torch.zeros((1, images.shape[1], images.shape[2]))

                return {
                    "ui": {
                        "images": [ui_item],
                        "image_hash": current_hash,
                    },
                    "result": (images, mask),
                }
            else:
                need_refresh = True

        # --- Caso C: nuova immagine / refresh ---
        mask = torch.zeros((1, images.shape[1], images.shape[2]))

        res = nodes.PreviewImage().save_images(
            images,
            filename_prefix="ZnBridge/ZB-",
            prompt=None,
            extra_pnginfo=extra_pnginfo,
        )
        ui_images = res["ui"]["images"]

        saved_path = os.path.join(
            folder_paths.get_temp_directory(),
            "ZnBridge",
            ui_images[0]["filename"],
        )

        # FIX Bug 1: usa la chiave che JS imposterà DOPO onExecuted, non la vecchia
        new_key = self._make_ui_key(ui_images[0])

        # Rimuovi la vecchia chiave temp dal cache per evitare entry obsolete
        old_cache = _bridge_cache.get(unique_id)
        if old_cache and len(old_cache) > 3 and old_cache[3]:
            _bridge_id_map.pop(old_cache[3], None)

        _bridge_id_map[new_key] = (saved_path, ui_images[0])
        # FIX Bug 2 + Bug 1: salva hash e new_key nel cache
        _bridge_cache[unique_id] = (images, ui_images, current_hash, new_key)

        return {
            "ui": {
                "images": ui_images,
                "image_hash": current_hash,
            },
            "result": (images, mask),
        }


NODE_CLASS_MAPPINGS = {
    "ZN_ImageMask_Bridge": ZN_ImageMask_Bridge,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ZN_ImageMask_Bridge": "ZN Image & Mask Bridge ⧉",
}
