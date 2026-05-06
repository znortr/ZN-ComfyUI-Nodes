import { app } from "../../../scripts/app.js";

app.registerExtension({
    name: "ZNodes.SmartBypasser",

    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name !== "ZN_Smart_Bypasser") return;

        // ─────────────────────────────────────────────
        // CACHE
        // ─────────────────────────────────────────────
        const maskCache = new Map();
        const imageAlphaCache = new Map();
        const sharedCanvas = document.createElement("canvas");
        const activeNodes = new WeakSet();
        
        let globalCursorResetTimer = null;
        let cleanupTimeout = null;

        // ─────────────────────────────────────────────
        // TOOLTIP HTML MANAGER (posizionato a DESTRA)
        // ─────────────────────────────────────────────
        const tooltips = new Map();
        let observer = null;
        
        const updateTooltipPosition = (node, canvasX, canvasY) => {
            const tooltipData = tooltips.get(node.id);
            if (!tooltipData) return;

            const canvas = app.canvas?.canvas;
            if (!canvas) return;

            const rect = canvas.getBoundingClientRect();
            const ds = app.canvas.ds;
            const scale = ds.scale;

            const screenX = rect.left + (canvasX + ds.offset[0]) * scale;
            const screenY = rect.top + (canvasY + ds.offset[1]) * scale;

            tooltipData.element.style.left = `${screenX}px`;
            tooltipData.element.style.top = `${screenY}px`;
            
            // Usa transform scale - scalerà TUTTO il contenuto (titolo + descrizioni)
            tooltipData.element.style.transform = `scale(${scale})`;
            tooltipData.element.style.transformOrigin = 'top left';
        };
        
        const showTooltip = (node, text, canvasX, canvasY) => {
            hideTooltip(node);
            
            const tooltip = document.createElement("div");
            tooltip.className = "zn-smart-bypass-tooltip";
            tooltip.innerHTML = text;
            
            tooltip.style.cssText = `
                position: fixed;
                background: #1e1e1e;
                color: #e0e0e0;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 11px;
                padding: 8px 12px;
                border-radius: 6px;
                border-left: 3px solid #d4a828;
                box-shadow: 0 4px 12px rgba(0,0,0,0.4);
                pointer-events: none;
                z-index: 999999;
                white-space: nowrap;
                backdrop-filter: blur(2px);
                letter-spacing: 0.3px;
                line-height: 1.4;
                transition: none;
            `;
            
            document.body.appendChild(tooltip);
            
            tooltips.set(node.id, {
                element: tooltip,
                canvasX: canvasX,
                canvasY: canvasY
            });
            
            updateTooltipPosition(node, canvasX, canvasY);
        };
        
        const hideTooltip = (node) => {
            const tooltipData = tooltips.get(node.id);
            if (tooltipData) {
                tooltipData.element.remove();
                tooltips.delete(node.id);
            }
        };
        
        const hideAllTooltips = () => {
            for (const tooltipData of tooltips.values()) {
                tooltipData.element.remove();
            }
            tooltips.clear();
        };
        
        const updateAllTooltips = () => {
            for (const [nodeId, tooltipData] of tooltips.entries()) {
                const node = app.graph?.nodes?.find(n => n.id === nodeId);
                if (node && tooltipData) {
                    updateTooltipPosition(node, tooltipData.canvasX, tooltipData.canvasY);
                }
            }
        };
        
        const setupCanvasTransformObserver = () => {
            const canvas = app.canvas?.canvas;
            if (!canvas) return;
            
            if (observer) observer.disconnect();
            
            observer = new MutationObserver(() => {
                updateAllTooltips();
            });
            
            observer.observe(canvas, {
                attributes: true,
                attributeFilter: ['style']
            });
            
            const ds = app.canvas?.ds;
            if (ds) {
                const originalSetScale = ds.setScale;
                if (originalSetScale) {
                    ds.setScale = function(...args) {
                        const result = originalSetScale.apply(this, args);
                        setTimeout(() => updateAllTooltips(), 0);
                        return result;
                    };
                }
            }
        };

        // ─────────────────────────────────────────────
        // GRAPH HELPER
        // ─────────────────────────────────────────────
        const getGraph = (node) => node.graph ?? app.graph;

        const getNodeName = (origin) =>
            origin?.title?.trim?.() ||
            origin?.properties?.name ||
            origin?.type ||
            "?";

        // ─────────────────────────────────────────────
        // RESET CURSORE GLOBALE
        // ─────────────────────────────────────────────
        const resetGlobalCursor = () => {
            const canvas = app.canvas?.canvas;
            if (canvas && canvas.style.cursor === "pointer") {
                canvas.style.cursor = "";
            }
        };

        // ─────────────────────────────────────────────
        // APPLY TARGET MODE
        // ─────────────────────────────────────────────
        const applyToTargets = (node, desiredMode) => {
            const graph = getGraph(node);
            
            if (app.canvas?.ds?.status === 1) {
                setTimeout(() => applyToTargets(node, desiredMode), 50);
                return;
            }
            
            let dirty = false;

            for (let i = 1; i < node.inputs.length; i++) {
                const input = node.inputs[i];
                if (!input?.link) continue;

                const link = graph.links?.[input.link];
                if (!link) continue;

                const target = graph.getNodeById?.(link.origin_id);
                if (!target || target.mode === desiredMode) continue;
                if (target.type === "ZN_Smart_Bypasser") continue;

                target.mode = desiredMode;
                dirty = true;
            }

            if (dirty) graph.setDirtyCanvas(true, true);
        };

        // ─────────────────────────────────────────────
        // ADD TARGET
        // ─────────────────────────────────────────────
        const addTarget = (node) => {
            const idx = node.inputs.length;
            node.addInput(`target_node_${idx}`, "*");
            node.setDirtyCanvas(true, true);
        };

        // ─────────────────────────────────────────────
        // CLEANUP
        // ─────────────────────────────────────────────
        const cleanup = (node) => {
            if (!node.inputs || !activeNodes.has(node)) return;

            const toRemove = [];
            
            for (let i = 1; i < node.inputs.length; i++) {
                if (!node.inputs[i]?.link) toRemove.push(i);
            }

            if (toRemove.length === 0) return;
            
            for (const i of toRemove.reverse()) {
                node.removeInput(i);
            }
            
            node.setDirtyCanvas(true, true);
        };

        // ─────────────────────────────────────────────
        // LABEL UPDATE
        // ─────────────────────────────────────────────
        const updateLabels = (node) => {
            if (!activeNodes.has(node)) return;
            
            const graph = getGraph(node);
            let needsRepaint = false;
            
            const trigger = node.inputs?.[0];
            if (trigger) {
                const oldLabel = trigger.label;
                let newLabel;
                
                if (trigger.link != null) {
                    const link = graph.links?.[trigger.link];
                    const origin = link ? graph.getNodeById?.(link.origin_id) : null;
                    newLabel = origin ? "Trigger: " + getNodeName(origin) : "trigger_input";
                } else {
                    newLabel = "trigger_input";
                }
                
                if (oldLabel !== newLabel) {
                    trigger.label = newLabel;
                    needsRepaint = true;
                }
            }

            for (let i = 1; i < node.inputs.length; i++) {
                const input = node.inputs[i];
                if (!input) continue;

                let newLabel;
                if (!input.link) {
                    newLabel = `target_node_${i}`;
                } else {
                    const link = graph.links?.[input.link];
                    const origin = link ? graph.getNodeById?.(link.origin_id) : null;
                    if (!origin) continue;
                    newLabel = getNodeName(origin);
                }
                
                if (input.name !== newLabel || input.label !== newLabel) {
                    input.name = newLabel;
                    input.label = newLabel;
                    needsRepaint = true;
                }
            }

            if (needsRepaint) {
                node.setDirtyCanvas(true);
            }
        };

        // ─────────────────────────────────────────────
        // MASK CHECK
        // ─────────────────────────────────────────────
        const checkImageAlpha = (filename) =>
            new Promise((resolve) => {
                if (imageAlphaCache.has(filename)) {
                    resolve(imageAlphaCache.get(filename));
                    return;
                }
                
                const lastSlash = filename.lastIndexOf("/");
                const subfolder = lastSlash >= 0 ? filename.slice(0, lastSlash) : "";
                const fname = lastSlash >= 0 ? filename.slice(lastSlash + 1) : filename;

                const url = `/view?filename=${encodeURIComponent(fname)}&subfolder=${encodeURIComponent(subfolder)}&type=input`;

                const img = new Image();
                img.onload = () => {
                    try {
                        const max = 512;
                        const scale = Math.min(1, max / Math.max(img.width, img.height));
                        const w = Math.max(1, (img.width * scale) | 0);
                        const h = Math.max(1, (img.height * scale) | 0);

                        sharedCanvas.width = w;
                        sharedCanvas.height = h;

                        const ctx = sharedCanvas.getContext("2d");
                        ctx.drawImage(img, 0, 0, w, h);

                        const data = ctx.getImageData(0, 0, w, h).data;
                        let hasAlpha = false;
                        
                        for (let i = 3; i < data.length; i += 4) {
                            if (data[i] < 255) {
                                hasAlpha = true;
                                break;
                            }
                        }

                        imageAlphaCache.set(filename, hasAlpha);
                        resolve(hasAlpha);
                    } catch {
                        imageAlphaCache.set(filename, false);
                        resolve(false);
                    }
                };
                img.onerror = () => {
                    imageAlphaCache.set(filename, false);
                    resolve(false);
                };
                img.src = url;
            });

        // ─────────────────────────────────────────────
        // MASK TRIGGER
        // ─────────────────────────────────────────────
        const triggerMaskCheck = async (node, filename) => {
            if (!activeNodes.has(node)) return;
            
            const invertMask = node._invertMaskLogic ?? false;
            
            const entry = maskCache.get(node.id);
            
            if (entry?.filename === filename && !entry.checking) {
                const shouldActivate = invertMask ? !entry.hasMask : entry.hasMask;
                applyToTargets(node, shouldActivate ? 0 : 4);
                return;
            }
            
            if (entry?.filename === filename && entry.checking) {
                return;
            }

            maskCache.set(node.id, {
                filename,
                hasMask: false,
                checking: true,
            });

            const hasMask = await checkImageAlpha(filename);

            const current = maskCache.get(node.id);
            if (current?.filename !== filename || !activeNodes.has(node)) return;

            maskCache.set(node.id, {
                filename,
                hasMask,
                checking: false,
            });

            const shouldActivate = invertMask ? !hasMask : hasMask;
            applyToTargets(node, shouldActivate ? 0 : 4);
        };

        // ─────────────────────────────────────────────
        // NORMALIZE
        // ─────────────────────────────────────────────
        const normalize = (v) => {
            if (typeof v === "boolean") return v;
            if (typeof v === "number") {
                if (v === 0) return true;
                if (v === 1) return true;
            }
            if (typeof v === "string") {
                const s = v.trim().toLowerCase();
                if (s === "0") return true;
                if (s === "1") return true;
                if (s === "true") return true;
                if (s === "false") return false;
            }
            return null;
        };

        // ─────────────────────────────────────────────
        // LEGGI VALORE DAL NODO SORGENTE
        // ─────────────────────────────────────────────
        const getValueFromOrigin = (origin, slotIndex) => {
            if (!origin?.widgets?.length) return null;
            
            let widget = null;
            
            if (origin.widgets[slotIndex]?.value !== undefined) {
                widget = origin.widgets[slotIndex];
            }
            
            if (!widget || widget.value === undefined) {
                widget = origin.widgets.find(w => w.value !== undefined) || origin.widgets[0];
            }
            
            return widget?.value ?? widget?.options?.value ?? null;
        };

        // ─────────────────────────────────────────────
        // LOGICA PRINCIPALE
        // ─────────────────────────────────────────────
        const applyLogic = (node) => {
            if (!activeNodes.has(node)) return;
            
            const graph = getGraph(node);
            const trigger = node.inputs?.[0];
            if (!trigger?.link) return;

            const link = graph.links?.[trigger.link];
            if (!link) return;

            const origin = graph.getNodeById?.(link.origin_id);
            if (!origin) return;

            const isImage = origin.type === "LoadImage" || origin.type === "zn_ImageMask_Bridge";

            if (isImage && link.origin_slot === 1) {
                const widget = origin.widgets?.find(w => w.name === "image") || origin.widgets?.[0];
                const filename = typeof widget?.value === "string" ? widget.value : null;

                if (filename) {
                    const clean = filename.replace(/\s\[.*\]$/, "");
                    triggerMaskCheck(node, clean);
                }
                return;
            }

            let val = getValueFromOrigin(origin, link.origin_slot);
            const norm = normalize(val);
            const mode = norm === true ? 4 : 0;

            applyToTargets(node, mode);
        };

        // ─────────────────────────────────────────────
        // CUSTOM CHECKBOX (con tooltip a DESTRA)
        // ─────────────────────────────────────────────
        const createCustomCheckbox = (node) => {
            node._invertMaskLogic = false;
            
            const checkboxSize = 14;
            const checkboxY = 38;
            let isHovering = false;
            
            const drawCustomCheckbox = (ctx) => {
                const isChecked = node._invertMaskLogic;
                const checkboxX = node.size[0] - 30;
                
                // Sfondo
                ctx.fillStyle = isChecked ? "#4a8" : "#444";
                ctx.fillRect(checkboxX, checkboxY, checkboxSize, checkboxSize);
                
                // Bordo
                ctx.strokeStyle = "#888";
                ctx.lineWidth = 1;
                ctx.strokeRect(checkboxX, checkboxY, checkboxSize, checkboxSize);
                
                // Checkmark
                if (isChecked) {
                    ctx.fillStyle = "#fff";
                    ctx.font = "10px sans-serif";
                    ctx.fillText("✓", checkboxX + 3, checkboxY + 11);
                }
                
                // Label
                ctx.fillStyle = "#aaa";
                ctx.font = "10px sans-serif";
                ctx.textAlign = "right";
                ctx.textBaseline = "middle";
                ctx.fillText("Invert Mask Logic", checkboxX - 5, checkboxY + checkboxSize / 2);
                
                // Gestione tooltip a DESTRA del nodo
                const mouseOver = node._mouse && 
                    node._mouse[0] >= checkboxX - 30 && 
                    node._mouse[0] <= checkboxX + checkboxSize && 
                    node._mouse[1] >= checkboxY && 
                    node._mouse[1] <= checkboxY + checkboxSize;
                
                if (mouseOver && !isHovering) {
                    isHovering = true;
                    
                    // Tooltip posizionato a DESTRA del nodo
                    const tooltipCanvasX = node.pos[0] + node.size[0] + 10;
                    const tooltipCanvasY = node.pos[1] + checkboxY - 15;
                    
                    // RIMOSSI I fontSize FISSI - ora usano tutti lo scale ereditato
                    const tooltipHtml = `
                        <div style="font-weight: bold; margin-bottom: 4px;">⚡ Invert Mask Logic</div>
                        <div>✓ <span style="color: #a8d8a8;">Checked</span>: No mask → <span style="color: #ff9999;">NO BYPASS</span></div>
                        <div>✗ <span style="color: #ff9999;">Unchecked</span>: No mask → <span style="color: #a8d8a8;">BYPASS</span></div>
                    `;
                    
                    showTooltip(node, tooltipHtml, tooltipCanvasX, tooltipCanvasY);
                } else if (!mouseOver && isHovering) {
                    isHovering = false;
                    hideTooltip(node);
                } else if (mouseOver && isHovering) {
                    // Aggiorna posizione durante pan/zoom
                    const tooltipCanvasX = node.pos[0] + node.size[0] + 10;
                    const tooltipCanvasY = node.pos[1] + checkboxY - 15;
                    updateTooltipPosition(node, tooltipCanvasX, tooltipCanvasY);
                }
            };
    
            const handleClick = (e, pos) => {
                const checkboxX = node.size[0] - 30;
                if (pos[0] >= checkboxX && pos[0] <= checkboxX + checkboxSize &&
                    pos[1] >= checkboxY && pos[1] <= checkboxY + checkboxSize) {
                    
                    node._invertMaskLogic = !node._invertMaskLogic;
                    node.setDirtyCanvas(true);
                    
                    const cached = maskCache.get(node.id);
                    if (cached && cached.filename) {
                        triggerMaskCheck(node, cached.filename);
                    } else {
                        applyLogic(node);
                    }
                    return true;
                }
                return false;
            };
            
            return { drawCustomCheckbox, handleClick };
        };
        // ─────────────────────────────────────────────
        // UI HELPERS
        // ─────────────────────────────────────────────
        const getPlusPos = (size) => ({
            x: size[0] - 30,
            y: size[1] - 50,
            s: 14,
        });

        const isOverPlus = (pos, size) => {
            const p = getPlusPos(size);
            return pos[0] >= p.x - 120 && pos[0] <= p.x + p.s && pos[1] >= p.y && pos[1] <= p.y + p.s;
        };

        const drawPlus = function (ctx) {
            const { x, y, s } = getPlusPos(this.size);
            const hover = !!(this._mouse && isOverPlus(this._mouse, this.size));

            ctx.fillStyle = hover ? "#3c3" : "#2a2";
            ctx.fillRect(x, y, s, s);

            ctx.strokeStyle = "#fff";
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(x + s / 2, y + 3);
            ctx.lineTo(x + s / 2, y + s - 3);
            ctx.moveTo(x + 3, y + s / 2);
            ctx.lineTo(x + s - 3, y + s / 2);
            ctx.stroke();

            ctx.fillStyle = hover ? "#fff" : "#aaa";
            ctx.font = "12px sans-serif";
            ctx.textAlign = "right";
            ctx.textBaseline = "middle";
            ctx.fillText("add target node", x - 6, y + s / 2);
        };

        // ─────────────────────────────────────────────
        // NODE LIFECYCLE
        // ─────────────────────────────────────────────
        const onNodeCreated = nodeType.prototype.onNodeCreated;

        nodeType.prototype.onNodeCreated = function () {
            onNodeCreated?.apply(this, arguments);

            this._cleanupTimeout = null;
            this._cursorResetTimer = null;

            activeNodes.add(this);

            if (!this.inputs || this.inputs.length === 0) {
                this.addInput("trigger_input", "*");
            } else if (this.inputs[0]?.name !== "trigger_input") {
                this.inputs[0].name = "trigger_input";
            }

            const { drawCustomCheckbox, handleClick } = createCustomCheckbox(this);
            this._drawCustomCheckbox = drawCustomCheckbox;
            this._handleCheckboxClick = handleClick;

            this.size = [260, 110];
            this._mouse = null;
            this._hoverPlus = false;
            this._lastHoverState = false;
            this._lastInputCount = this._lastInputCount ?? 0;

            this.onDrawForeground = function (ctx) {
                const canvas = app.canvas?.canvas;
                
                if (this._hoverPlus) {
                    canvas.style.cursor = "pointer";
                } else if (canvas?.style.cursor === "pointer") {
                    canvas.style.cursor = "";
                }

                if (this._drawCustomCheckbox) {
                    this._drawCustomCheckbox(ctx);
                }

                const slotH = 20;
                const inputsCount = this.inputs?.length ?? 1;
                
                const targetsCount = Math.max(0, inputsCount - 1);
                const newHeight = 35 + (targetsCount * slotH) + 40;

                if (inputsCount !== this._lastInputCount || this.size[1] !== newHeight) {
                    this._lastInputCount = inputsCount;
                    this.size[1] = Math.max(newHeight, 110);
                }

                drawPlus.call(this, ctx);
            };

            this.onResize = function (size) {
                const newWidth = Math.max(size[0], 260);
                const newHeight = Math.max(size[1], this.size[1]);
                
                if (this.size[0] !== newWidth) this.size[0] = newWidth;
                if (this.size[1] !== newHeight) this.size[1] = newHeight;
            };

            this.onMouseMove = function (e, pos) {
                this._mouse = pos;
                const newHoverState = isOverPlus(pos, this.size);
                
                if (newHoverState !== this._lastHoverState) {
                    this._hoverPlus = newHoverState;
                    this._lastHoverState = newHoverState;
                    this.setDirtyCanvas(true);
                } else {
                    this.setDirtyCanvas(true);
                }
            };

            this.onMouseLeave = function () {
                this._mouse = null;
                if (this._lastHoverState) {
                    this._hoverPlus = false;
                    this._lastHoverState = false;
                    this.setDirtyCanvas(true);
                }
                if (this._cursorResetTimer) clearTimeout(this._cursorResetTimer);
                this._cursorResetTimer = setTimeout(resetGlobalCursor, 100);
            };

            this.onMouseDown = function (e, pos) {
                if (this._handleCheckboxClick && this._handleCheckboxClick(e, pos)) {
                    return true;
                }
                
                if (isOverPlus(pos, this.size)) {
                    addTarget(this);
                    return true;
                }
            };

            this.onConnectionsChange = () => {
                if (this._cleanupTimeout) clearTimeout(this._cleanupTimeout);
                this._cleanupTimeout = setTimeout(() => {
                    if (activeNodes.has(this)) {
                        cleanup(this);
                    }
                }, 10);
            };

            if (this.timer) clearInterval(this.timer);
            this.timer = setInterval(() => {
                if (!this.graph || !activeNodes.has(this)) {
                    if (this.timer) {
                        clearInterval(this.timer);
                        this.timer = null;
                    }
                    return;
                }
                applyLogic(this);
                updateLabels(this);
            }, 200);
        };

        const onRemoved = nodeType.prototype.onRemoved;

        nodeType.prototype.onRemoved = function () {
            if (this.timer) {
                clearInterval(this.timer);
                this.timer = null;
            }

            if (this._cleanupTimeout) {
                clearTimeout(this._cleanupTimeout);
                this._cleanupTimeout = null;
            }

            if (this._cursorResetTimer) {
                clearTimeout(this._cursorResetTimer);
                this._cursorResetTimer = null;
            }
            
            hideTooltip(this);
            
            activeNodes.delete(this);
            maskCache.delete(this.id);
            
            resetGlobalCursor();

            onRemoved?.apply(this, arguments);
        };
        
        setTimeout(() => {
            setupCanvasTransformObserver();
        }, 1000);
        
        window.addEventListener('beforeunload', () => {
            hideAllTooltips();
        });
    }
});