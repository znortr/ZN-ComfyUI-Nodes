/*
 * ZN Smart Flusher - frontend helper
 *
 * Disables the VRAM threshold widget when the VRAM safety guard is OFF.
 * The Python node remains the authoritative source for the actual behavior;
 * this file only improves the user interface.
 */

import { app } from "../../scripts/app.js";

const NODE_NAME = "ZN_SmartFlusher";
const GUARD_WIDGET = "use_vram_guard";
const THRESHOLD_WIDGET = "vram_threshold_gb";

function findWidget(node, name) {
    return node?.widgets?.find((widget) => widget.name === name) ?? null;
}

function updateThresholdWidget(node) {
    const guardWidget = findWidget(node, GUARD_WIDGET);
    const thresholdWidget = findWidget(node, THRESHOLD_WIDGET);

    if (!guardWidget || !thresholdWidget) {
        return;
    }

    const enabled = Boolean(guardWidget.value);

    // Keep the widget visible, but clearly inactive and impossible to edit.
    thresholdWidget.disabled = !enabled;
    thresholdWidget.__znOriginalType ??= thresholdWidget.type;
    thresholdWidget.type = enabled ? thresholdWidget.__znOriginalType : "hidden";

    // ComfyUI renders widgets differently across versions. These properties
    // cover both the canvas widget and the HTML input used by newer builds.
    thresholdWidget.options ??= {};
    thresholdWidget.options.disabled = !enabled;
    thresholdWidget.__znDisabled = !enabled;

    if (thresholdWidget.inputEl) {
        thresholdWidget.inputEl.disabled = !enabled;
        thresholdWidget.inputEl.style.opacity = enabled ? "1" : "0.45";
        thresholdWidget.inputEl.style.pointerEvents = enabled ? "auto" : "none";
    }

    node.setDirtyCanvas(true, true);
}

app.registerExtension({
    name: "ZN.SmartFlusher.VRAMGuardUI",

    nodeCreated(node) {
        if (node.comfyClass !== NODE_NAME && node.type !== NODE_NAME) {
            return;
        }

        const guardWidget = findWidget(node, GUARD_WIDGET);
        const thresholdWidget = findWidget(node, THRESHOLD_WIDGET);

        if (!guardWidget || !thresholdWidget) {
            return;
        }

        // Preserve ComfyUI's original callback, if present.
        const originalCallback = guardWidget.callback;
        guardWidget.callback = function (...args) {
            const result = originalCallback?.apply(this, args);
            updateThresholdWidget(node);
            return result;
        };

        // Also update when the node is restored from a workflow.
        const originalOnConfigure = node.onConfigure;
        node.onConfigure = function (...args) {
            const result = originalOnConfigure?.apply(this, args);
            setTimeout(() => updateThresholdWidget(node), 0);
            return result;
        };

        // Initial state.
        setTimeout(() => updateThresholdWidget(node), 0);
    },
});
