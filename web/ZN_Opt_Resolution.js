import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

app.registerExtension({
    name: "zn_opt_resolution",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "ZN_Opt_Resolution") return;

        let presetsCache = null;

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            onNodeCreated?.apply(this, arguments);

            const modelWidget = this.widgets.find(w => w.name === "model_name");
            const widthWidget = this.widgets.find(w => w.name === "width");
            const heightWidget = this.widgets.find(w => w.name === "height");
            
            const resIdx = this.widgets.findIndex(w => w.name === "resolution");
            if (resIdx === -1) return;

            // --- TOOLTIPS ---
            if (modelWidget) modelWidget.desc = "Select the model architecture (Flux, Qwen, etc.)";
            if (widthWidget) widthWidget.desc = "Target width (updated by preset)";
            if (heightWidget) heightWidget.desc = "Target height (updated by preset)";

            const oldResValue = this.widgets[resIdx].value;
            this.widgets[resIdx] = {
                name: "resolution",
                type: "combo",
                value: oldResValue || "Manual",
                desc: "Pick a resolution preset or use Manual",
                options: { values: ["Manual"] },
                callback: (v) => {
                    this.widgets[resIdx].value = v;
                    updateValuesFromPreset(false);
                },
                serializeValue: function() { return this.value; }
            };
            const resWidget = this.widgets[resIdx];

            const updateValuesFromPreset = async (isModelChange = false) => {
                if (!presetsCache) {
                    try {
                        const response = await api.fetchApi("/znodes/resolution_presets");
                        presetsCache = await response.json();
                    } catch (e) { return; }
                }

                const modelData = presetsCache[modelWidget.value];
                if (modelData && modelData.resolutions) {
                    const newValues = ["Manual", ...modelData.resolutions.map(r => r.name)];
                    resWidget.options.values = newValues;

                    if (isModelChange) {
                        resWidget.value = "Manual";
                    } else if (!newValues.includes(resWidget.value)) {
                        resWidget.value = "Manual";
                    }

                    if (resWidget.value !== "Manual") {
                        const selected = modelData.resolutions.find(r => r.name === resWidget.value);
                        if (selected) {
                            widthWidget.value = selected.width;
                            heightWidget.value = selected.height;
                        }
                    }
                }
            };

            modelWidget.callback = () => updateValuesFromPreset(true);
            setTimeout(() => updateValuesFromPreset(false), 100);
        };
    }
});