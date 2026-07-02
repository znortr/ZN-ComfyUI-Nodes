import { app } from "/scripts/app.js";

const COLOR = {
    readyBg:     "#2a6496",
    readyBorder: "#1a4f7a",
    readyText:   "#ffffff",
    offBg:       "#444444",
    offBorder:   "#333333",
    offText:     "#777777",
    savedBg:     "#2e7d32",
    savedBorder: "#1b5e20",
    savedText:   "#ffffff",
};

class ZN_ImagePreviewSaveAdv {
    static SLIDER_TOP = 125; // margine top

    constructor(node) {
        this.node = node;
        this.imgA = null;
        this.imgB = null;
        this.savedA = false;
        this.savedB = false;
        this.sliderX = 0.5;
        this.isDragging = false;

        this._labelA = "IMAGE_A";
        this._labelB = "IMAGE_B";
        this._prevSlotAActive = null;
        this._prevSlotBActive = null;

        this._loadToken = null;

        // Memorizza le info originali dei file (per fetch con metadati)
        this._infoA = null;
        this._infoB = null;

        node.resizable = true;
        node.flags = node.flags || {};
        node.flags.allow_resize = true;

        node.size[0] = Math.max(node.size[0], 260);
        node.size[1] = Math.max(node.size[1], 220);

        node.onResize = function (size) {
            size[0] = Math.max(size[0], 260);
            size[1] = Math.max(size[1], 220);
        };

        const SLIDER_TOP = ZN_ImagePreviewSaveAdv.SLIDER_TOP;
        const RESIZE_MARGIN = 10;
        const LEFT_MARGIN = 8;
        const RIGHT_MARGIN = 8;

        // --- PATCH PROTECTION ---
        if (node.__zn_patched) return;
        node.__zn_patched = true;

        // --- MENU CONTESTUALE STANDARD COMFYUI ---
        const origGetExtraMenuOptions = node.getExtraMenuOptions?.bind(node);
        const inst = this; // riferimento per il closure

        node.getExtraMenuOptions = function (_, options) {
            const buildUrl = (info) => {
                if (!info) return null;
                const p = new URLSearchParams({
                    filename: info.filename,
                    subfolder: info.subfolder ?? "",
                    type: info.type,
                });
                return `/view?${p}`;
            };

            const items = [];
            const urlA = buildUrl(inst._infoA);
            const urlB = buildUrl(inst._infoB);
            if (urlA && inst.imgA) items.push({ label: "A", url: urlA });
            if (urlB && inst.imgB) items.push({ label: "B", url: urlB });

            if (items.length) {
                options.push(null); // separatore

                const addStandardItems = (opts, url, prefix = "") => {
                    const pre = prefix ? `${prefix} ` : "";

                    // Open Image
                    opts.push({
                        content: `${pre}Open Image`,
                        callback: () => window.open(url, "_blank"),
                    });

                    // Save Image
                    opts.push({
                        content: `${pre}Save Image`,
                        callback: async () => {
                            try {
                                const res = await fetch(url);
                                const blob = await res.blob();
                                const objUrl = URL.createObjectURL(blob);
                                const a = document.createElement("a");
                                a.href = objUrl;
                                a.download = (url.match(/filename=([^&]+)/)?.[1] || "image.png");
                                document.body.appendChild(a);
                                a.click();
                                setTimeout(() => {
                                    document.body.removeChild(a);
                                    URL.revokeObjectURL(objUrl);
                                }, 0);
                            } catch (e) {
                                console.error(e);
                                app.ui.dialog.show("Failed to save image");
                            }
                        },
                    });

                    // Copy Image
                    opts.push({
                        content: `${pre}Copy Image`,
                        callback: async () => {
                            try {
                                const res = await fetch(url);
                                const blob = await res.blob();
                                if (!navigator.clipboard?.write || !window.ClipboardItem) {
                                    throw new Error("Clipboard API not supported");
                                }
                                await navigator.clipboard.write([
                                    new ClipboardItem({ [blob.type]: blob }),
                                ]);
                                app.ui.dialog.show("Image copied to clipboard");
                            } catch (e) {
                                console.error(e);
                                app.ui.dialog.show("Failed to copy image: " + e.message);
                            }
                        },
                    });
                };

                if (items.length === 1) {
                    // Una sola immagine visibile → menu diretto (identico al PreviewImage standard)
                    addStandardItems(options, items[0].url);
                } else {
                    // Due immagini → sottomenu "Image" con le voci per A e B
                    const submenu = { options: [] };
                    items.forEach((it) => addStandardItems(submenu.options, it.url, `Image ${it.label}`));
                    options.push({
                        content: "🖼 Image",
                        has_submenu: true,
                        submenu: submenu,
                    });
                }
            }

            return origGetExtraMenuOptions?.apply(this, arguments);
        };

        // === ONMOUSEDOWN FIX - Controlla prima i bottoni ===
        const origMouseDown = node.onMouseDown?.bind(node);
        node.onMouseDown = (e, pos, canvas) => {
            const [x, y] = pos;

            // Priorità ai bottoni Save
            if (this.btnRow?.mouse && this.btnRow.mouse(e, pos, node)) {
                return true;
            }

            // Solo se non era un bottone → slider
            const showA = !!(this.isInputActive("image_a") && this.imgA);
            const showB = !!(this.isInputActive("image_b") && this.imgB);

            if (showA && showB &&
                y >= SLIDER_TOP &&
                y <= node.size[1] - RESIZE_MARGIN &&
                x >= LEFT_MARGIN &&
                x <= node.size[0] - RIGHT_MARGIN) {

                this.isDragging = true;
                this.updateSliderFromMouse(x);
                canvas.setDirty(true, true);
                return true;
            }

            return origMouseDown?.(e, pos, canvas);
        };

        const origMouseMove = node.onMouseMove?.bind(node);
        node.onMouseMove = (e, pos, canvas) => {
            const [x, y] = pos;

            // Auto-reset se il tasto sinistro è stato rilasciato fuori dal nodo
            if (this.isDragging && e.buttons === 0) {
                this.isDragging = false;
            }

            // Muove lo slider solo se il tasto sinistro è fisicamente premuto
            if (this.isDragging && e.buttons === 1 && y <= node.size[1] - RESIZE_MARGIN) {
                this.updateSliderFromMouse(x);
                canvas.setDirty(true, true);
                return true;
            }
            return origMouseMove?.(e, pos, canvas);
        };

        const origMouseUp = node.onMouseUp?.bind(node);
        node.onMouseUp = (e, pos, canvas) => {
            if (this.isDragging) {
                this.isDragging = false;
                canvas.setDirty(true, true);
                return true;
            }
            return origMouseUp?.(e, pos, canvas);
        };

        const origDraw = node.onDrawForeground?.bind(node);
        node.onDrawForeground = (ctx) => {
            origDraw?.(ctx);
            this.draw(ctx, SLIDER_TOP);
        };

        const origConnectionsChange = node.onConnectionsChange;
        node.onConnectionsChange = (type, index, connected, link_info, slot) => {
            origConnectionsChange?.call(node, type, index, connected, link_info, slot);

            if (type === 1 && !connected) {
                const inputSlot = node.inputs[index];
                if (inputSlot.name === "image_a") {
                    this.cleanupImage(this.imgA);
                    this.imgA = null;
                    this.savedA = false;
                    this._infoA = null;
                } else if (inputSlot.name === "image_b") {
                    this.cleanupImage(this.imgB);
                    this.imgB = null;
                    this.savedB = false;
                    this._infoB = null;
                }
            }

            this.sliderX = 0.5;
            this.updateButtons();
            app.graph.setDirtyCanvas(true, true);
        };

        // FIX: cleanup immagini quando il nodo viene rimosso dal grafo
        const origRemoved = node.onRemoved?.bind(node);
        node.onRemoved = () => {
            origRemoved?.();
            this.cleanupImage(this.imgA);
            this.cleanupImage(this.imgB);
            this.imgA = null;
            this.imgB = null;
            this._infoA = null;
            this._infoB = null;
            this._loadToken = null;
        };
    }

    cleanupImage(img) {
        if (!img) return;
        img.onload = null;
        img.onerror = null;
    }

    async loadImage(info) {
        try {
            const params = new URLSearchParams({
                filename: info.filename,
                subfolder: info.subfolder ?? "",
                type: info.type,
            });
            const url = `/view?${params}`;

            const img = new Image();
            img.src = url;               // URL server = permanente e valido per menu/link
            await img.decode();
            return img;
        } catch (err) {
            console.error("[zn_comparer] loadImage error:", err);
            return null;
        }
    }

    async updateImages(data) {
        this.cleanupImage(this.imgA);
        this.cleanupImage(this.imgB);

        this.imgA = null;
        this.imgB = null;
        this.savedA = false;
        this.savedB = false;

        // Salva le info originali dei file (usate per il salvataggio con metadati)
        this._infoA = data?.a_images?.length > 0 ? data.a_images[0] : null;
        this._infoB = data?.b_images?.length > 0 ? data.b_images[0] : null;

        // --- FIX RACE CONDITION ---
        const token = Symbol();
        this._loadToken = token;

        try {
            const [imgA, imgB] = await Promise.all([
                this._infoA ? this.loadImage(this._infoA) : Promise.resolve(null),
                this._infoB ? this.loadImage(this._infoB) : Promise.resolve(null),
            ]);
            if (this._loadToken !== token) return;

            this.imgA = imgA;
            this.imgB = imgB;
        } catch (err) {
            console.error("[zn_comparer] updateImages error:", err);
        }

        // Esponi nel formato standard di ComfyUI
        this.node.imgs = [];
        if (this.imgA) this.node.imgs.push(this.imgA);
        if (this.imgB) this.node.imgs.push(this.imgB);
        this.node.imageIndex = 0;

        this.sliderX = 0.5;
        this.updateButtons();
        app.graph.setDirtyCanvas(true, true);
    }

    // Legge il valore corrente del toggle save_metadata dal widget del nodo
    _getSaveMetadata() {
        const w = this.node.widgets?.find(w => w.name === "save_metadata");
        return w ? !!w.value : true; // default true se widget non trovato
    }

    // Renderizza l'immagine su canvas e restituisce un Blob PNG (senza metadati)
    async _blobFromCanvas(img) {
        const canvas = document.createElement("canvas");
        canvas.width = img.width;
        canvas.height = img.height;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(img, 0, 0);
        return new Promise(resolve => canvas.toBlob(resolve, "image/png"));
    }

    // Recupera il file PNG originale da ComfyUI (con metadati già incorporati da Python)
    async _blobFromOriginal(info) {
        const params = new URLSearchParams({
            filename: info.filename,
            subfolder: info.subfolder ?? "",
            type: info.type,
        });
        const response = await fetch(`/view?${params}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.blob();
    }

    async saveImage(slotName) {
        const img = slotName === "image_a" ? this.imgA : this.imgB;
        if (!img) return;

        const slot = this.node.inputs.find(i => i.name === slotName);
        const label = slot?.label || slotName;

        let folder = (this.node.folder_name || "").trim();

        const saveMetadata = this._getSaveMetadata();
        const info = slotName === "image_a" ? this._infoA : this._infoB;

        const cleanLabel = label.replace(/\s+/g, '_');
        const filename = `${cleanLabel}_${Date.now()}.png`;

        try {
            let blob;

            if (saveMetadata && info) {
                // Salva il file originale: i metadati (prompt/workflow) sono già
                // incorporati da Python nel PNG originale — li preserviamo intatti.
                console.log(`[zn_comparer] saveImage ${slotName}: saving WITH metadata (original file)`);
                blob = await this._blobFromOriginal(info);
            } else {
                // Salva dal canvas: nessun metadato incluso.
                console.log(`[zn_comparer] saveImage ${slotName}: saving WITHOUT metadata (canvas render)`);
                blob = await this._blobFromCanvas(img);
            }

            if (!blob) return;

            const form = new FormData();
            form.append("image", blob, filename);
            form.append("subfolder", folder);
            form.append("type", "output");

            const res = await fetch("/upload/image", { method: "POST", body: form });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);

            if (slotName === "image_a") this.savedA = true;
            if (slotName === "image_b") this.savedB = true;
        } catch (err) {
            console.error("[zn_comparer] saveImage error:", err);
        }

        this.updateButtons();
    }

    updateSliderFromMouse(mouseX) {
        if (!this.imgA || !this.imgB) return;
        const node = this.node;
        const SLIDER_TOP = ZN_ImagePreviewSaveAdv.SLIDER_TOP;
        const left = 8, right = 8, bottom = 8;

        const drawW = node.size[0] - left - right;
        const drawH = node.size[1] - SLIDER_TOP - bottom;
        const scale = Math.min(drawW / this.imgA.width, drawH / this.imgA.height);
        const rw = this.imgA.width * scale;

        if (rw <= 0) {
            this.sliderX = 0.5;
            return;
        }

        const ox = left + (drawW - rw) * 0.5;
        const rel = (mouseX - ox) / rw;
        this.sliderX = Math.min(Math.max(rel, 0), 1);
    }

    isInputActive(slotName) {
        const slot = this.node.inputs.find(i => i.name === slotName);
        if (!slot || slot.link === null || slot.link === undefined) return false;

        const linkId = Array.isArray(slot.link) ? slot.link[0] : slot.link;
        const link = app.graph.links?.[linkId];
        if (!link) return false;

        // FIX: usa solo origin_id (nodo sorgente del link).
        // Il fallback a target_id era errato: target_id è il nodo corrente (destinazione),
        // non il nodo upstream — avrebbe controllato il mode del nodo sbagliato.
        const upstreamNode = app.graph.getNodeById?.(link.origin_id);
        if (!upstreamNode) return false;

        // FIX: sicurezza su mode (LiteGraph non sempre garantito)
        const mode = upstreamNode.mode;

        // 4 = bypass, 2 = never (comportamento originale mantenuto)
        if (mode === 4 || mode === 2) return false;

        return true;
    }

    updateButtons() {
        if (!this.btnA || !this.btnB) return;

        const slotAActive = !!(this.isInputActive("image_a"));
        const slotBActive = !!(this.isInputActive("image_b"));

        if (
            this._prevSlotAActive !== null &&
            (
                Boolean(slotAActive) !== Boolean(this._prevSlotAActive) ||
                Boolean(slotBActive) !== Boolean(this._prevSlotBActive)
            )
        ) {
            this.sliderX = 0.5;
        }

        this._prevSlotAActive = slotAActive;
        this._prevSlotBActive = slotBActive;

        this.btnA.type = slotAActive ? "button" : "hidden";
        this.btnB.type = slotBActive ? "button" : "hidden";

        const slotA = this.node.inputs.find(i => i.name === "image_a");
        const slotB = this.node.inputs.find(i => i.name === "image_b");

        const labelA = slotA?.label || "image_a";
        const labelB = slotB?.label || "image_b";

        this._labelA = labelA.toUpperCase();
        this._labelB = labelB.toUpperCase();

        const updateStyle = (btn, img, isSaved, label, isLocked) => {
            if (!img) {
                btn.name = "Hit Run first";
                btn.color = COLOR.offBg;
                btn.borderColor = COLOR.offBorder;
                btn.textColor = COLOR.offText;
                btn.disabled = true;
            } else if (isLocked) { // Aggiunto controllo sul lock
                btn.name = "Saving...";
                btn.color = COLOR.readyBg; // O un colore intermedio
                btn.borderColor = COLOR.readyBorder;
                btn.textColor = COLOR.readyText;
                btn.disabled = true; // Impedisce click extra durante il salvataggio
            } else if (isSaved) {
                btn.name = `Saved ${label}`;
                btn.color = COLOR.savedBg;
                btn.borderColor = COLOR.savedBorder;
                btn.textColor = COLOR.savedText;
                btn.disabled = false;
            } else {
                btn.name = `Save ${label}`;
                btn.color = COLOR.readyBg;
                btn.borderColor = COLOR.readyBorder;
                btn.textColor = COLOR.readyText;
                btn.disabled = false;
            }
        };

        if (!this.imgA) this.savedA = false;
        if (!this.imgB) this.savedB = false;

        updateStyle(this.btnA, this.imgA, this.savedA, labelA, this.btnRow?._lock_A);
        updateStyle(this.btnB, this.imgB, this.savedB, labelB, this.btnRow?._lock_B);
    }

    draw(ctx, SLIDER_TOP = ZN_ImagePreviewSaveAdv.SLIDER_TOP) {
        
        const node = this.node;
        const w = node.size[0], h = node.size[1];

        const left = 8, right = 8, top = SLIDER_TOP;
        const footerH = 18;
        const bottom = 8 + footerH;

        const drawW = w - left - right;
        const drawH = h - top - bottom;

        ctx.save();
        ctx.translate(left, top);

        ctx.save();
        ctx.fillStyle = "#333";
        ctx.fillRect(-left, -top, drawW + left + right, top - 5);
        ctx.restore();

        const showA = !!(this.isInputActive("image_a") && this.imgA);
        const showB = !!(this.isInputActive("image_b") && this.imgB);

        if (!showA && !showB) {
            ctx.fillStyle = "#222";
            ctx.fillRect(0, 0, drawW, drawH);
            ctx.restore();
            return;
        }

        if ((showA && !showB) || (!showA && showB)) {
            const img = showA ? this.imgA : this.imgB;
            const scale = Math.min(drawW / img.width, drawH / img.height);
            const rw = img.width * scale, rh = img.height * scale;
            const ox = (drawW - rw) * 0.5, oy = (drawH - rh) * 0.5;

            ctx.fillStyle = "#222";
            ctx.fillRect(0, 0, drawW, drawH);
            ctx.drawImage(img, ox, oy, rw, rh);

            ctx.save();
            ctx.fillStyle = "#ccc";
            ctx.font = "12px sans-serif";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText(`${img.width}×${img.height}`, drawW * 0.5, drawH + footerH * 0.8);
            ctx.restore();

            ctx.restore();
            return;
        }

        // Comparazione A vs B
        const finalW = Math.max(this.imgA.width, this.imgB.width);
        const finalH = Math.max(this.imgA.height, this.imgB.height);
        const scale = Math.min(drawW / finalW, drawH / finalH);
        const rw = finalW * scale;
        const rh = finalH * scale;
        const ox = (drawW - rw) * 0.5;
        const oy = (drawH - rh) * 0.5;

        const scaleA = Math.min(rw / this.imgA.width, rh / this.imgA.height);
        const scaleB = Math.min(rw / this.imgB.width, rh / this.imgB.height);

        const rwA = this.imgA.width * scaleA, rhA = this.imgA.height * scaleA;
        const rwB = this.imgB.width * scaleB, rhB = this.imgB.height * scaleB;

        const oxA = ox + (rw - rwA) * 0.5;
        const oyA = oy + (rh - rhA) * 0.5;
        const oxB = ox + (rw - rwB) * 0.5;
        const oyB = oy + (rh - rhB) * 0.5;

        const cut = rw * this.sliderX;

        ctx.fillStyle = "#222";
        ctx.fillRect(0, 0, drawW, drawH);

        ctx.drawImage(this.imgA, oxA, oyA, rwA, rhA);

        // Watermark A
        ctx.save();
        ctx.globalAlpha = 0.25;
        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 32px sans-serif";
        ctx.textAlign = "left";
        ctx.fillText(this._labelA, oxA + 10, oyA + 40);
        ctx.restore();

        // Parte B
        ctx.save();
        ctx.fillStyle = "#222";
        ctx.fillRect(ox + cut, oy, rw - cut, rh);

        ctx.beginPath();
        ctx.rect(ox + cut, oy, rw - cut, rh);
        ctx.clip();

        ctx.drawImage(this.imgB, oxB, oyB, rwB, rhB);

        ctx.globalAlpha = 0.25;
        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 32px sans-serif";
        ctx.textAlign = "right";
        ctx.fillText(this._labelB, ox + rw - 10, oy + 40);
        ctx.restore();

        // Slider
        ctx.strokeStyle = "#fff";
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(ox + cut, oy);
        ctx.lineTo(ox + cut, oy + rh);
        ctx.stroke();

        ctx.fillStyle = "#fff";
        ctx.beginPath();
        ctx.arc(ox + cut, oy + rh * 0.5, 5, 0, Math.PI * 2);
        ctx.fill();

        // Footer
        ctx.save();
        ctx.fillStyle = "#ccc";
        ctx.font = "12px sans-serif";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(`${this.imgA.width}×${this.imgA.height}`, drawW * 0.25, drawH + footerH * 0.8);
        ctx.fillText(`${this.imgB.width}×${this.imgB.height}`, drawW * 0.75, drawH + footerH * 0.8);
        ctx.restore();

        ctx.restore();
    }
}

// ====================== EXTENSION ======================
app.registerExtension({
    name: "Zandor.ZN_ImagePreviewSaveAdv",

    async nodeCreated(node) {
        if (node.comfyClass !== "ZN_ImagePreviewSaveAdv") return;

        const inst = new ZN_ImagePreviewSaveAdv(node);

        const folderWidget = node.widgets?.find(w => w.name === "folder_name");
        if (folderWidget) {
            node.folder_name = folderWidget.value;
            folderWidget.callback = (v) => { node.folder_name = v; };
        } else {
            node.folder_name = "zn_images";
        }

        // Bottoni
        inst.btnA = { type: "button" };
        inst.btnB = { type: "button" };

        const WIDGET_NAME = "zn_comparer_buttons";
        let btnRow = node.widgets?.find(w => w.name === WIDGET_NAME);
        if (!btnRow) {
            btnRow = node.addWidget("button", WIDGET_NAME, null, () => {});
        }

        inst.btnRow = btnRow;

        const MARGIN = 20;
        const GAP = 10;
        const RADIUS = 6;

        btnRow.computeSize = () => [0, 36];

        btnRow.draw = function(ctx, node, width, y, height) {
            // updateButtons() chiamata qui ogni frame: necessario perché
            // bypass e rename slot non generano eventi, vanno rilevati a ogni draw.
            inst.updateButtons();

            if (!inst.btnA || !inst.btnB) return;

            const aVis = inst.btnA.type !== "hidden";
            const bVis = inst.btnB.type !== "hidden";
            if (!aVis && !bVis) return;

            const TOP_OFFSET = 5;
            const BTN_HEIGHT = 20;
            const drawY = y + TOP_OFFSET;
            const totalW = width - MARGIN * 2;

            let xA, xB, wA, wB;
            if (aVis && bVis) {
                wA = wB = (totalW - GAP) / 2;
                xA = MARGIN;
                xB = MARGIN + wA + GAP;
            } else {
                wA = wB = totalW;
                xA = xB = MARGIN;
            }

            btnRow._layout = { xA, xB, wA, wB, y, h: height, aVis, bVis };

            const drawBtn = (state, x, w) => {
                ctx.save();
                // FIX: font esplicito per evitare ereditarietà dal contesto canvas
                ctx.font = "12px sans-serif";
                ctx.fillStyle = state.color || "#444";
                ctx.strokeStyle = state.borderColor || "#222";
                ctx.beginPath();
                ctx.roundRect(x, drawY, w, BTN_HEIGHT, RADIUS);
                ctx.fill();
                ctx.stroke();

                ctx.fillStyle = state.textColor || "#fff";
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.fillText(state.name, x + w * 0.5, drawY + BTN_HEIGHT * 0.5);
                ctx.restore();
            };

            if (aVis) drawBtn(inst.btnA, xA, wA);
            if (bVis) drawBtn(inst.btnB, xB, wB);
        };

        btnRow.mouse = function(event, pos, node) {
            if (!inst.btnA || !inst.btnB) return false;

            const l = btnRow._layout;
            if (!l) return false;

            const [x, y] = pos;
            const TIMEOUT = 200; // tempo in ms di timeout tra un click e l'altro

            if (y >= l.y && y <= l.y + l.h) {
                
                // GESTIONE PULSANTE A
                if (l.aVis && x >= l.xA && x <= l.xA + l.wA && !inst.btnA.disabled) {
                    if (btnRow._lock_A) return true; 

                    btnRow._lock_A = true;
                    inst.saveImage("image_a").finally(() => {
                        setTimeout(() => { btnRow._lock_A = false; }, TIMEOUT);
                    });

                    inst.isDragging = false;
                    return true;
                }

                // GESTIONE PULSANTE B
                if (l.bVis && x >= l.xB && x <= l.xB + l.wB && !inst.btnB.disabled) {
                    if (btnRow._lock_B) return true;

                    btnRow._lock_B = true; 
                    inst.saveImage("image_b").finally(() => {
                        setTimeout(() => { btnRow._lock_B = false; }, TIMEOUT);
                     });

                    inst.isDragging = false;
                    return true;
                }
            }
            return false;
        };
        

        const orig = node.onExecuted?.bind(node);
        node.onExecuted = (data) => {
            orig?.(data);
            if (data?.folder_name) {
                node.folder_name = data.folder_name;
                if (folderWidget) folderWidget.value = data.folder_name;
            }
            inst.updateImages(data);
        };
    },
});
