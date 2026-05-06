import { app } from "../../../scripts/app.js";

app.registerExtension({
    name: "ZN.Lora_Helper",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name === "ZN_Lora_Helper") {
            
            const onExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function(msgs) {
                onExecuted?.apply(this, arguments);
                
                if (msgs?.lora_names) {
                    // Indice 0: trigger_words
                    // Indici 1, 3, 5, 7, 9: lora_path_1...5
                    for (let i = 0; i < 5; i++) {
                        const pathIdx = (i * 2) + 1;
                        const fileName = msgs.lora_names[i];
                        
                        if (fileName) {
                            // Rinominiamo solo l'uscita Path con il nome del file
                            this.outputs[pathIdx].label = fileName.replace(/\.[^/.]+$/, "");
                        } else {
                            this.outputs[pathIdx].label = `lora_path_${i+1}`;
                        }
                    }
                }
            };
        }
    }
});