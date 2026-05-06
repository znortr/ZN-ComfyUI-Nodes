import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "ZnNodes.ImageMaskBridge",

    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name !== "ZN_ImageMask_Bridge") return;

        // ---------------------------------------------------------
        // onConfigure — fired when the graph is loaded (page reload)
        // Reset both image widget and hash so neither image nor mask
        // persists across a page reload.
        // ---------------------------------------------------------
        const origOnConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function (info) {
            origOnConfigure?.apply(this, arguments);

            const imageWidget = this.widgets?.find(w => w.name === "image");
            if (imageWidget) {
                imageWidget.value = "";   // reset image → also clears mask reference
            }
            this._lastImageHash = null;   // reset hash tracking
        };

        // ---------------------------------------------------------
        // pasteFromClipspace
        // ---------------------------------------------------------
        nodeType.prototype.pasteFromClipspace = function () {
            const clipspace = app.constructor.clipspace;
            if (!clipspace) return;

            const imageWidget = this.widgets?.find(w => w.name === "image");
            if (!imageWidget) return;

            const imgs = clipspace["images"];
            if (imgs && imgs.length > 0) {
                const img  = imgs[0];
                const sub  = img.subfolder ? img.subfolder + "/" : "";
                imageWidget.value = `${sub}${img.filename} [${img.type}]`;
            }
        };

        // ---------------------------------------------------------
        // onExecuted — with hash check
        // ---------------------------------------------------------
        const origOnExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (message) {
            origOnExecuted?.apply(this, arguments);

            const imageWidget = this.widgets?.find(w => w.name === "image");
            if (!imageWidget) return;

            // --- SE È MASKEDITOR: NON TOCCARE ---
            if (typeof imageWidget.value === "object" && imageWidget.value !== null) {
                // È un MaskEditor → non sovrascrivere mai
                return;
            }

            // --- HASH CHECK ---
            const newHash = message?.image_hash;
            if (newHash) {
                if (this._lastImageHash && this._lastImageHash !== newHash) {
                    // L'immagine è cambiata → resetta il widget
                    imageWidget.value = "";
                }
                this._lastImageHash = newHash;
            }

            // --- LOGICA ESISTENTE ---
            const imgs = message?.images;
            if (!imgs || imgs.length === 0) return;

            const hasClipspace =
                imageWidget.value &&
                (imageWidget.value.includes("clipspace") ||
                imageWidget.value.includes("[input]"));

            if (!hasClipspace) {
                const img = imgs[0];
                const sub = img.subfolder ? img.subfolder + "/" : "";
                imageWidget.value = `${sub}${img.filename} [${img.type}]`;
            }
        };

    },
});
