import { app } from "../../scripts/app.js";

let ZN_PRESETS = {
    models: {},
    presets: {}
};

// ==============================
// 1. FETCH PRESETS (on load)
// ==============================
async function refreshPresets() {
    try {
        const res = await fetch("/znodes/presets");
        ZN_PRESETS = await res.json();
        console.log("[ZnNodes] Presets aggiornati", ZN_PRESETS);
    } catch (e) {
        console.error("[ZnNodes] Errore fetch presets:", e);
    }
}

// ==============================
// 2. UI LOGIC (NO RESIZE FORZATI)
// ==============================
function applyLogic(node) {
    if (!node || !ZN_PRESETS.models) return;

    const modelWidget = node.widgets.find(w => w.name === "model_version");
    const guidanceWidget = node.widgets.find(w => w.name === "flux_guidance");
    const autoStyleWidget = node.widgets.find(w => w.name === "auto_style");
    const styleWidget = node.widgets.find(w => w.name === "style_stack");

    if (!modelWidget || !guidanceWidget) return;

    // --------------------------
    // A) SHOW/HIDE GUIDANCE
    // --------------------------
    const selectedModel = modelWidget.value;
    const modelData = ZN_PRESETS.models[selectedModel];

    const shouldHide = modelData && modelData.supports_guidance === false;

    if (guidanceWidget._originalHidden === undefined)
        guidanceWidget._originalHidden = guidanceWidget.hidden;

    guidanceWidget.hidden = shouldHide;

    // --------------------------
    // B) DISABLE STYLE STACK
    // --------------------------
    if (autoStyleWidget && styleWidget) {
        const isAuto = autoStyleWidget.value === true;
        styleWidget.disabled = isAuto;
        styleWidget.color = isAuto ? "#444444" : "";
    }

    // --------------------------
    // C) REFRESH CANVAS (NO RESIZE)
    // --------------------------
    node.setDirtyCanvas(true, true);
}

// ==============================
// 3. HOOK NODE + PATCH RESIZE
// ==============================
app.registerExtension({
    name: "ZnNodes.AdvancedPrompt",

    async setup() {
        await refreshPresets();
    },

    nodeCreated(node) {
        if (node.comfyClass !== "ZN_Adv_Prompt") return;

        // ============================
        // PATCH: PRESERVA DIMENSIONE
        // ============================
        const MIN_WIDTH = 350;
        node.__zn_saved_size = null;

        // Intercetta resize manuale
        const origOnResize = node.onResize;
        node.onResize = function(w, h) {
            const finalW = Math.max(w, MIN_WIDTH);
            node.__zn_saved_size = { w: finalW, h };

            if (origOnResize) origOnResize.call(this, finalW, h);
        };

        // Intercetta refresh UI dopo cambi widget
        const origOnPropertyChanged = node.onPropertyChanged;
        node.onPropertyChanged = function(name, value) {
            const r = origOnPropertyChanged
                ? origOnPropertyChanged.call(this, name, value)
                : undefined;

            // Ripristina dimensione manuale
            if (node.__zn_saved_size) {
                this.size[0] = node.__zn_saved_size.w;
                this.size[1] = node.__zn_saved_size.h;
            }

            return r;
        };

        // ============================
        // CALLBACK WIDGETS
        // ============================
        node.widgets.forEach(w => {
            const orig = w.callback;
            w.callback = function (...args) {
                if (orig) orig.apply(this, args);
                applyLogic(node);
            };
        });

        // Primo apply con leggero delay
        setTimeout(() => applyLogic(node), 150);
    }
});
