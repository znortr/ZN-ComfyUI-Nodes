# ZN_ImagePreviewSaveAdv.py

from nodes import PreviewImage

class ZN_ImagePreviewSaveAdv:
    """
    ### ZN_Images_Comparer_Adv

    An interactive visualization tool designed for precise A/B testing and quality control 
    directly within the ComfyUI canvas.

    **Key Features:**
    * **Interactive Side-by-Side Comparison:** Implements a smooth vertical slider 
    (A-Left, B-Right) to analyze pixel-perfect differences between two images.
    * **Dynamic Smart Naming:** - The node uses the input slot labels (e.g., 'Denoised', 'Raw_Latent') to name the saved files.
        - Automatic sanitization: spaces are replaced with underscores and text is converted 
        to UPPERCASE for consistent file management.
    * **Context-Aware UI:** - Save buttons ('Save IMAGE_A', 'Save IMAGE_B') are dynamically generated.
        - Buttons automatically hide when a slot is disconnected to keep the interface clean.
        - Visual feedback: Button colors change from Blue (Ready) to Green (Saved) upon success.
    * **Intelligent Watermarking:** - Overlays uppercase labels on images during comparison mode.
        - Automatically disables watermarks and sliders when viewing a single image for 
        an unobstructed preview.
    * **Integrated Export:** Saves high-quality PNGs to a custom subfolder (default: 'zn_images') 
    within the ComfyUI output directory, appending a unique timestamp to prevent overwriting.
    """

    DESCRIPTION = (
        "Advanced dual-image viewer and slide comparer with integrated save functions, "
        "which allows saving either image individually directly from the UI. Renaming "
        "the input slots makes the images, save buttons, and exported files much more "
        "recognizable, as labels and filenames adapt dynamically. Ideal for upscaling, "
        "A/B testing, or any workflow where organized exporting is essential."
    )

    NAME = "ZN Image Preview & Save ADV"
    CATEGORY = "Znortr/Viewer"
    FUNCTION = "compare_images"
    
    # AGGIUNGI QUESTE DUE RIGHE:
    RETURN_TYPES = ()
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "save_metadata": ("BOOLEAN", {
                    "default": True, 
                    "label_on": "enabled", 
                    "label_off": "disabled",
                    "tooltip": "When enabled, embeds the full generation metadata (Prompt and Extra PNG Info) into the file. This node-level toggle overrides global ComfyUI settings to ensure workflow preservation."
                }),
            },
            "optional": {
                "image_a": ("IMAGE",),
                "image_b": ("IMAGE",),
                "folder_name": ("STRING", {
                    "default": "zn_images",
                    "tooltip": (
                        "Name of the subfolder inside the output directory where "
                        "images will be saved. If the folder does not exist, it "
                        "will be created. Leave empty to save to the output directory."
                    )
                }),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO"
            },
        }
    
    # Metodo helper mancante nel tuo snippet per gestire il salvataggio fisico
    def save_images(self, images, filename_prefix, prompt=None, extra_pnginfo=None):
        # Utilizza la logica di PreviewImage di ComfyUI per generare i file temporanei
        p = PreviewImage()
        return p.save_images(images, filename_prefix, prompt, extra_pnginfo)

    def compare_images(self, save_metadata=True, image_a=None, image_b=None, folder_name="zn_images", filename_prefix="zn.compare.", prompt=None, extra_pnginfo=None):

        result = { "ui": { "a_images": [], "b_images": [] }, "folder_name": folder_name }

        result["ui"]["prompt"] = prompt
        result["ui"]["extra_pnginfo"] = extra_pnginfo

        if image_a is not None and len(image_a) > 0:
            saved = self.save_images(image_a, filename_prefix, prompt, extra_pnginfo)
            result["ui"]["a_images"] = saved["ui"]["images"]

        if image_b is not None and len(image_b) > 0:
            saved = self.save_images(image_b, filename_prefix, prompt, extra_pnginfo)
            result["ui"]["b_images"] = saved["ui"]["images"]

        return result

NODE_CLASS_MAPPINGS = {
    "ZN_ImagePreviewSaveAdv": ZN_ImagePreviewSaveAdv,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ZN_ImagePreviewSaveAdv": "ZN Image Preview & Save ADV ⧉",
}