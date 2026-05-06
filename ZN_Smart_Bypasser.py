import torch

class ZN_Smart_Bypasser:
    """
    Zn smart Bypasser Trigger
    Advanced multi-target bypass controller for ComfyUI.
    This node allows you to dynamically enable or disable BYPASS mode on any number of connected target nodes using a single trigger input.

    ─────────────────────────────
    CORE BEHAVIOR
    ─────────────────────────────
    Trigger = TRUE  → Targets are BYPASSED (purple mode)
    Trigger = FALSE → Targets are ACTIVE

    ─────────────────────────────
    SUPPORTED INPUT TYPES
    ─────────────────────────────
    • INT / FLOAT / STRING:
    0, 1, 0.0, 1.0, "0", "1" → TRUE (BYPASS ACTIVE)
    Any other value           → FALSE (BYPASS OFF)

    • BOOLEAN / STRING:
    True, "true"   → BYPASS ACTIVE
    False, "false" → BYPASS OFF

    • IMAGE MASK (from LoadImage / zn_ImageMask_Bridge - mask output):
    Mask PRESENT   → ACTIVE (NO bypass)
    Mask ABSENT    → BYPASSED

    ─────────────────────────────
    INVERT MASK LOGIC (checkbox)
    ─────────────────────────────
    Reverses mask behavior:
    Mask PRESENT   → BYPASSED
    Mask ABSENT    → ACTIVE

    ─────────────────────────────
    FEATURES
    ─────────────────────────────
    • Controls unlimited target nodes
    • Dynamic input slots (add as many targets as needed)
    • Automatic type detection (no manual conversion required)
    • Real-time evaluation
    • Smart label updates based on connected nodes

    The trigger_output is a direct pass-through of the input.
    """

    DESCRIPTION = """
    Advanced universal bypass controller for ComfyUI
    to control the BYPASS state of multiple target nodes.
    ─────────────────────────────
    SUPPORTED INPUT TYPES : • INT / FLOAT / STRING / MASK
 
   Values:
    • 0, 1, 0.0, 1.0, "0", "1", True, "true"    → TRUE = BYPASS ACTIVE
    • False, "false" and Any other value     → FALSE = BYPASS OFF

    IMAGE MASK MODE
    ─────────────────────────────
    (when trigger is a mask output)

    • Mask present   → ACTIVE (no bypass)
    • No mask        → BYPASSED

    Invert option:
    • Mask present   → BYPASSED
    • No mask        → ACTIVE

    NOTES
    ─────────────────────────────
    • Supports unlimited targets
    • trigger_output is a pass-through
    """
    NAME ="ZN Smart Bypasser"
    FUNCTION = "noop"
    CATEGORY = "znort/util"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "optional": {
                "trigger_input": ("*", {"forceInput": True}),
            }
        }

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """Always consider changed to support dynamic inputs"""
        return float("NaN")
    
    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        """Accept ANY input, even dynamic ones created by JavaScript"""
        return True

    RETURN_TYPES = ("*",)
    RETURN_NAMES = ("trigger_output",)
    OUTPUT_NODE = False

    def noop(self, trigger_input=None, **kwargs):
        """
        Pure pass-through that accepts ANY keyword arguments.
        The **kwargs captures all dynamic inputs (target_node_1, target_node_2, etc.)
        """
        return (trigger_input,)


NODE_CLASS_MAPPINGS = {
    "ZN_Smart_Bypasser": ZN_Smart_Bypasser
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ZN_Smart_Bypasser": "⧉ ZN Smart Bypasser"
}