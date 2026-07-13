import { app } from "../../../scripts/app.js";

app.registerExtension({
    name: "ZN.Lora_Helper",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "ZN_Lora_Helper") return;

        const onExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function(msgs) {
            onExecuted?.apply(this, arguments);
            
            if (msgs?.lora_names) {
                // Salva stato per usi futuri (es. timer, riconnessioni)
                this._loraNames = msgs.lora_names;
                
                // ── RINOMINA LABEL OUTPUT PATH ──
                for (let i = 0; i < 5; i++) {
                    const pathIdx = (i * 2) + 1;
                    const fileName = msgs.lora_names[i];
                    
                    if (fileName) {
                        this.outputs[pathIdx].label = fileName.replace(/\.[^/.]+$/, "");
                    } else {
                        this.outputs[pathIdx].label = `lora_path_${i+1}`;
                    }
                }
                
                // ── AUTO BYPASS DEI LORA LOADERS ──
                const autoBypassWidget = this.widgets?.find(w => w.name === "auto_bypass");
                if (autoBypassWidget?.value !== false) {
                    const graph = this.graph ?? app.graph;
                    if (!graph) return;
                    
                    let dirty = false;
                    
                    for (let i = 0; i < 5; i++) {
                        const pathIdx = (i * 2) + 1;
                        const hasLora = msgs.lora_names[i] != null;
                        
                        const output = this.outputs[pathIdx];
                        if (!output || !output.links || output.links.length === 0) continue;
                        
                        for (const linkId of output.links) {
                            const link = graph.links[linkId];
                            if (!link) continue;
                            
                            const targetNode = graph.getNodeById(link.target_id);
                            if (!targetNode) continue;
                            
                            // Evita loop o modifiche a nodi dello stesso tipo
                            if (targetNode.type === "ZN_Lora_Helper") continue;
                            
                            // 0 = ACTIVE (verde), 4 = BYPASS (viola)
                            const desiredMode = hasLora ? 0 : 4;
                            if (targetNode.mode !== desiredMode) {
                                targetNode.mode = desiredMode;
                                dirty = true;
                            }
                        }
                    }
                    
                    if (dirty) graph.setDirtyCanvas(true, true);
                }
            }
        };
    }
});
