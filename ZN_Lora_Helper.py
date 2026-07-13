import re
import folder_paths

class ZN_Lora_Helper:

    DESCRIPTION = (
            "⚠️ Requires Lora Stacker (LoraManager) as input.\n\n"
            "This node acts as an automated bridge for the LoRA Stack, designed to extract trigger words "
            "and route up to five LoRA entries to standard loaders. It serves as a dedicated extension "
            "that allows for 'normal' LoRA management outside of the LoraManager environment, "
            "effectively preventing node conflicts while maintaining dynamic output control. "
            "Features include automatic trigger word normalization, dynamic output renaming (path + strength), "
            "UI exposure of active LoRA filenames, and automatic bypass of empty LoRA slots."
        )
    
    NAME = "ZN Lora Helper"
    FUNCTION = "process"
    CATEGORY = "ZN_Nodes"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "lora_stack": ("LORA_STACK",),
                "trigger_words": ("STRING", {"forceInput": True}),
                "auto_bypass": ("BOOLEAN", {"default": True, "label_on": "Enabled", "label_off": "Disabled"}),
            }
        }

    LORA_LIST = folder_paths.get_filename_list("loras")

    RETURN_TYPES = ("STRING",) + (LORA_LIST, "FLOAT") * 5
    
    RETURN_NAMES = ("trigger_words",) + tuple(
        item for i in range(1, 6) for item in (f"lora_path_{i}", f"strength_{i}")
    )
    
    OUTPUT_NODE = True

    def process(self, lora_stack, trigger_words, auto_bypass=True):
        clean_tw = re.sub(r'[\s,]+', ', ', trigger_words).strip().strip(',')

        results = [clean_tw]
        names_to_ui = []

        for i in range(5):
            path = ""
            strength = 0.0
            if lora_stack and i < len(lora_stack):
                path = lora_stack[i][0]
                strength = float(lora_stack[i][1])
                names_to_ui.append(path.split('/')[-1].split('\\')[-1])
            else:
                names_to_ui.append(None)
            
            results.append(path)
            results.append(strength)

        return {"ui": {"lora_names": names_to_ui}, "result": tuple(results)}

NODE_CLASS_MAPPINGS = { "ZN_Lora_Helper": ZN_Lora_Helper }
NODE_DISPLAY_NAME_MAPPINGS = { "ZN_Lora_Helper": "⧉ ZN LoRA Helper" }
