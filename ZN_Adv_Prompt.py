import os
import json
import torch
from server import PromptServer
from aiohttp import web

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
RESOURCES_PATH = os.path.join(BASE_DIR, "presets")


class ZN_Adv_Prompt:

    DESCRIPTION = (
    "Generates a structured prompt using user text, style presets and model settings. "
    "Applies formatting, weights and cleanup rules to produce an optimized prompt. "
    "Tip: edit the JSON config files to customize presets, then reload the page."
    )

    NAME = "ZN Advanced Prompt"
    FUNCTION = "execute"
    CATEGORY = "Znort/Prompt"

    _cache_models = None
    _cache_presets = None

    # =========================================================
    # FORMATTER - FORMATTAZIONE DEI BLOCCHI
    # =========================================================
    def _format_block(self, content, weight, use_nl=False):
        """
        Se use_nl = False → (content:weight)
        Se use_nl = True  → solo content, senza pesi né parentesi
        """
        content = (content or "").strip()
        if not content:
            return ""

        if use_nl:
            # NL mode → niente parentesi, niente pesi
            return ", ".join([t.strip() for t in content.split(",") if t.strip()])

        # modalità tecnica → parentesi + peso
        return f"({content}:{weight})"

    # =========================================================
    # NORMALIZZAZIONE TERMINI
    # =========================================================
    def _normalize_term(self, t):
        return (
            (t or "")
            .lower()
            .replace("-", " ")
            .replace("_", " ")
            .strip()
        )

    # =========================================================
    # NATURALIZZAZIONE LISTE ("A, B, C" → "A, B and C")
    # =========================================================
    def _naturalize_terms(self, content):
        """
        "A, B, C" -> "A, B and C"
        Non tocca:
        - stringhe senza virgole
        - liste con già ' and ' dentro
        - blocchi con un solo termine
        """
        if not content:
            return ""

        if " and " in content:
            return content.strip()

        parts = [t.strip() for t in content.split(",") if t.strip()]
        n = len(parts)

        if n <= 1:
            return content.strip()

        if n == 2:
            return f"{parts[0]} and {parts[1]}"

        return ", ".join(parts[:-1]) + " and " + parts[-1]

    # =========================================================
    # NL CONNECTOR ENGINE (dinamico, da JSON)
    # =========================================================
    def _get_connector_and_mode(self, key, presets, active_styles):
        """
        Ritorna (connector, mode) per un blocco logico:
        - legge prima dai punti NL specifici
        - fallback su settings.nl.default_*
        """
        default_nl = presets.get("settings", {}).get("nl", {}) or {}
        default_connector = default_nl.get("default_connector", "with")
        default_mode = default_nl.get("default_mode", "merge")

        # STYLE
        if key == "style":
            if active_styles:
                style = active_styles[0]
                data = presets.get("style_stacks", {}).get(style, {}) or {}
                nl = data.get("nl", {}) or {}
                return nl.get("connector", default_connector), nl.get("mode", default_mode)

        # STYLE_LENS (lens derivata dallo stile) → usa grammatica lens_presets.nl
        if key == "style_lens":
            nl = presets.get("lens_presets", {}).get("nl", {}) or {}
            return nl.get("connector", default_connector), nl.get("mode", default_mode)

        # BASE QUALITY
        if key == "base_quality":
            nl = presets.get("base_quality", {}).get("nl", {}) or {}
            return nl.get("connector", default_connector), nl.get("mode", default_mode)

        # LENS (manuale)
        if key == "lens":
            nl = presets.get("lens_presets", {}).get("nl", {}) or {}
            return nl.get("connector", default_connector), nl.get("mode", default_mode)

        # FRAMING
        if key == "framing":
            nl = presets.get("framing_fix", {}).get("nl", {}) or {}
            return nl.get("connector", default_connector), nl.get("mode", default_mode)

        # ANTI ARTIFACTS
        if key == "anti_artifacts":
            nl = presets.get("anti_artifacts", {}).get("nl", {}) or {}
            return nl.get("connector", default_connector), nl.get("mode", default_mode)

        # NEG TO POS (PFN)
        if key == "neg_to_pos":
            nl = presets.get("pfn", {}).get("nl", {}) or {}
            return nl.get("connector", default_connector), nl.get("mode", default_mode)

        # DEFAULT
        return default_connector, default_mode

    # =========================================================
    # NL v6 - BUILDER COMPLETO CON CONNETTORI DINAMICI
    # =========================================================
    def _build_nl_prompt_with_connectors(
        self,
        lora_block,
        user_block,
        sorted_extra_blocks_with_keys,
        presets,
        active_styles,
    ):
        """
        NL v6:
        - LoRA + User = Bibbia, sempre primi, senza connettori
        - Blocchi extra in ordine di peso (già ordinati a monte)
        - Connettori dinamici da JSON (settings + style + lens + ecc.)
        - merge  → "<prev>, <connector> <content>"
        - prefix → "<connector> <content>"
        - suffix → "<connector> <content>"  (come da tuo JSON)
        """
        nl_settings = presets.get("settings", {}).get("nl", {}) or {}
        default_connector = nl_settings.get("default_connector", "with")

        final_parts = []

        # 1) Bibbia: LoRA + User (senza connettori)
        for block in [lora_block, user_block]:
            block = (block or "").strip().strip(",")
            if not block:
                continue
            if not final_parts:
                final_parts.append(block)
            else:
                final_parts.append(block)

        # 2) Blocchi extra (già ordinati per peso)
        for key, raw_content in sorted_extra_blocks_with_keys:
            content = (raw_content or "").strip().strip(",")
            if not content:
                continue

            # Naturalizza i termini tecnici
            content = self._naturalize_terms(content)

            connector, mode = self._get_connector_and_mode(key, presets, active_styles)
            connector = (connector or default_connector).strip()
            mode = (mode or "merge").lower().strip()

            # Se non c'è ancora nulla (nessuna Bibbia), metti solo il contenuto
            if not final_parts:
                final_parts.append(content)
                continue

            # MERGE → "<prev>, <connector> <content>"
            if mode == "merge":
                prev = final_parts[-1]
                final_parts[-1] = f"{prev}, {connector} {content}"
                continue

            # PREFIX → "<connector> <content>"
            if mode == "prefix":
                final_parts.append(f"{connector} {content}")
                continue

            # SUFFIX (nel tuo JSON) → anche qui "<connector> <content>"
            if mode == "suffix":
                final_parts.append(f"{connector} {content}")
                continue

            # Fallback → comportamento tipo "with content"
            final_parts.append(f"{connector} {content}")

        return ", ".join([p.strip().rstrip(",") for p in final_parts if p.strip()])


    # =========================================================
    # NL CLEAN - PULIZIA LEGGERA (SENZA HARD-CODED CONNECTORS)
    # =========================================================
    def _nl_clean(self, text):
        """
        NL-clean v6 (connector-aware):
        - NON tocca i connettori dinamici
        - NON spezza connettori multi-parola
        - NON rimuove virgole/spazi davanti ai connettori
        - pulisce solo spazi multipli e virgole doppie fuori dai connettori
        """
        import re

        if not text:
            return ""

        # 1) Recupera i connettori dinamici
        connectors = list(self._nl_connectors) if hasattr(self, "_nl_connectors") else []
        connectors = sorted(connectors, key=len, reverse=True)  # proteggi prima i più lunghi

        # 2) Proteggi i connettori con placeholder temporanei
        protected = {}
        for i, conn in enumerate(connectors):
            placeholder = f"__CONN_{i}__"
            protected[placeholder] = conn
            # sostituisci solo se matcha come parola intera o frase intera
            text = re.sub(rf'\b{re.escape(conn)}\b', placeholder, text)

        # 3) Pulizia generale (NON tocca i placeholder)
        text = text.replace(",,", ",")
        text = text.replace(", ,", ",")
        text = re.sub(r'\s+', ' ', text)
        text = text.replace(" ,", ",")
        text = text.strip().rstrip(",")

        # 4) Ripristina i connettori originali
        for placeholder, conn in protected.items():
            text = text.replace(placeholder, conn)

        return text
    
    # =========================================================
    # DEDUPE v3 - PROTEGGE I CONNETTORI DINAMICI
    # =========================================================
    def _collect_connectors_from_presets(self, presets):
        """
        Estrae dinamicamente TUTTI i connettori NL dal JSON.
        Ritorna un set di frasi normalizzate.
        """
        connectors = set()

        settings_nl = presets.get("settings", {}).get("nl", {}) or {}
        if settings_nl.get("default_connector"):
            connectors.add(settings_nl["default_connector"])

        # blocchi singoli
        single_blocks = ["pfn", "base_quality", "framing_fix", "anti_artifacts"]
        for key in single_blocks:
            nl = presets.get(key, {}).get("nl", {}) or {}
            c = nl.get("connector")
            if c:
                connectors.add(c)

        # lens_presets.nl
        lens_nl = presets.get("lens_presets", {}).get("nl", {}) or {}
        c = lens_nl.get("connector")
        if c:
            connectors.add(c)

        # style_stacks.*.nl
        style_stacks = presets.get("style_stacks", {}) or {}
        for style_data in style_stacks.values():
            if not isinstance(style_data, dict):
                continue
            nl = style_data.get("nl", {}) or {}
            c = nl.get("connector")
            if c:
                connectors.add(c)

        # normalizza
        return {self._normalize_term(c) for c in connectors}

    def _dedupe_with_priority(self, blocks_ordered, priority_reference, presets):
        """
        Dedupe modulare v3:
        - protegge i connettori (dinamici, da JSON)
        - rimuove prefissi duplicati rispetto alla 'Bibbia' (Lora+User)
        - dedupe cross-blocchi
        - non altera user/lora (che non passano qui)
        """
        # 1) Bibbia normalizzata
        ref_norm = self._normalize_term(priority_reference or "")
        ref_words = set(ref_norm.split())

        # 2) Connettori dinamici
        connector_phrases = self._collect_connectors_from_presets(presets)
        connector_words = set()
        for c in connector_phrases:
            connector_words.update(c.split())

        seen = set()
        result_blocks = []

        for block in blocks_ordered:
            if not block:
                result_blocks.append("")
                continue

            block = block.strip()

            # parsing blocco pesato
            has_parens = block.startswith("(") and block.endswith(")")
            content = block
            weight = None

            if has_parens:
                inner = block[1:-1].strip()
                if ":" in inner:
                    before, after = inner.rsplit(":", 1)
                    try:
                        float(after.strip())
                        content = before.strip()
                        weight = after.strip()
                    except Exception:
                        content = inner
                else:
                    content = inner

            terms = [t.strip() for t in content.split(",") if t.strip()]
            new_terms = []

            for t in terms:
                t_norm_full = self._normalize_term(t)

                # protezione connettori (anche se duplicati)
                if t_norm_full in connector_phrases:
                    new_terms.append(t)
                    continue

                orig_words = t.split()
                norm_words = t_norm_full.split()

                # rimozione prefissi duplicati rispetto alla Bibbia
                cut_idx = 0
                for i in range(len(norm_words), 0, -1):
                    prefix = norm_words[:i]

                    # se il prefisso contiene parole di connettori → non tagliare
                    if any(w in connector_words for w in prefix):
                        continue

                    if all(w in ref_words for w in prefix):
                        cut_idx = i
                        break

                if cut_idx > 0:
                    remaining_norm = norm_words[cut_idx:]
                    remaining_orig = orig_words[cut_idx:]
                    if not remaining_norm:
                        # tutto prefisso duplicato → salta
                        continue
                    t_norm_new = " ".join(remaining_norm)
                    t_display = " ".join(remaining_orig)
                else:
                    t_norm_new = " ".join(norm_words)
                    t_display = t

                # dedupe cross-blocchi (ma MAI sui connettori)
                if t_norm_new not in connector_phrases and len(t_norm_new) > 4:
                    if t_norm_new in seen:
                        continue

                seen.add(t_norm_new)
                new_terms.append(t_display)

            if not new_terms:
                result_blocks.append("")
                continue

            new_content = ", ".join(new_terms)

            if has_parens and weight is not None:
                result_blocks.append(f"({new_content}:{weight})")
            else:
                result_blocks.append(new_content)

        return result_blocks

    # =========================================================
    # CONFIG LOAD - Caricamento preset e configurazioni
    # =========================================================
    @classmethod
    def _load_json(cls, filename):
        try:
            path = os.path.join(RESOURCES_PATH, filename)
            if not os.path.exists(path):
                return {}
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[ZnNodes] Errore {filename}: {e}")
            return {}

    @classmethod
    def _load_model_config(cls, model_version):
        if cls._cache_models is None:
            cls._cache_models = cls._load_json("models_presets.json")
        return cls._cache_models.get(model_version, {}) or {}

    @classmethod
    def _load_prompt_presets(cls):
        if cls._cache_presets is None:
            cls._cache_presets = cls._load_json("prompt_presets.json")
        return cls._cache_presets

    @classmethod
    def _load_weights_and_limits(cls, presets):
        settings = presets.get("settings", {}) or {}
        weights = settings.get("weights", {}) or {}
        limits = settings.get("limits", {}) or {}
        return weights, limits

    # =========================================================
    # INPUT TYPES / METADATA
    # =========================================================
    @classmethod
    def INPUT_TYPES(cls):
        #azzero la cache dei preset ad ogni reload pagina
        cls._cache_models = None
        cls._cache_presets = None

        models = cls._load_json("models_presets.json")
        presets = cls._load_json("prompt_presets.json")

        model_list = list(models.keys()) or ["flux"]
        # style_list = sorted(list(presets.get("style_stacks", {}).keys())) or ["disable"]

        style_list = sorted(list(presets.get("style_stacks", {}).keys()))
        if "disable" in style_list:
            style_list.remove("disable")
        style_list = ["disable"] + style_list

        # LENS PRESETS (escludi 'nl')
        lens_list = sorted(
            [k for k in presets.get("lens_presets", {}).keys() if k not in ("nl", "disable")]
        )
        lens_list = ["disable"] + lens_list

        # ANTI ARTIFACT LEVELS (escludi 'nl')
        artifact_list = sorted(
            [k for k in presets.get("anti_artifacts", {}).keys() if k not in ("nl", "disable")]
        )
        artifact_list = ["disable"] + artifact_list

        return {
            "required": {
                "model_version": ( model_list, {"tooltip": "Select the model preset used to build the prompt."} ),

                "clip": ( "CLIP", {"tooltip": "CLIP encoder used to tokenize and process the prompt."} ),

                "positive": ( "STRING", { "multiline": True, "default": "", "tooltip": "Describe what the image should contain." } ),

                "negative": ( "STRING", { "multiline": True, "default": "", "tooltip": "Describe what the image should avoid." } ),

                "lora_tags": ( "STRING", { "default": "", "tooltip": "Optional LoRA tags to refine style or details." } ),

                "auto_style": ( "BOOLEAN", { "default": False, "tooltip": "Automatically detect and apply a matching style." } ),

                "style_stack": ( style_list, { "default": "disable", "tooltip": "Choose a predefined style preset." } ),

                "lens_preset": ( lens_list, { "default": "disable", "tooltip": "Apply a camera or lens profile." } ),

                "framing_fix": ( "BOOLEAN", { "default": False, "tooltip": "Improve subject framing and avoid cut elements." } ),

                "anti_artifact_level": ( artifact_list, { "default": "disable", "tooltip": "Reduce artifacts and improve visual stability." } ),

                "flux_guidance": ( "FLOAT", { "default": 3.5, "min": 0.0, "max": 200.0, "tooltip": "Adjust prompt strength for Flux models." } ),
            }
        }

    RETURN_TYPES = ("CONDITIONING", "CONDITIONING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("positive", "negative", "text_pos", "text_neg", "debug_log")

    # =========================================================
    # MODULO 2: BLOCCHI PRINCIPALI (LORA + USER)
    # =========================================================
    def _build_lora_block(self, lora_tags, weights, use_nl):
        w = weights.get("lora_tags", 1.25)
        return self._format_block(lora_tags, w, use_nl)

    def _build_user_block(self, positive, weights, use_nl):
        w = weights.get("user_prompt", 1.15)
        return self._format_block(positive, w, use_nl)

    # =========================================================
    # MODULO 3: BASE QUALITY
    # =========================================================
    def _build_base_quality_block(self, presets, weights, use_nl):
        bq = presets.get("base_quality", {}) or {}
        pos = bq.get("positive", [])
        neg = bq.get("negative", [])

        # normalizza: se è stringa → split
        if isinstance(pos, str):
            pos = [t.strip() for t in pos.split(",") if t.strip()]
        if isinstance(neg, str):
            neg = [t.strip() for t in neg.split(",") if t.strip()]

        pos_text = ", ".join(pos)
        neg_text = ", ".join(neg)

        w = weights.get("base_quality", 1.15)
        block = self._format_block(pos_text, w, use_nl)

        return block, neg_text

    # =========================================================
    # MODULO 4: AUTO-STYLE / STYLE STACK
    # =========================================================
    def _select_styles(self, presets, positive, auto_style, style_stack):
        style_presets = presets.get("style_stacks", {}) or {}
        auto_keywords = presets.get("auto_style_keywords", {}) or {}
        conflicts = presets.get("conflicts", {}) or {}

        # AUTO-STYLE
        if auto_style:
            positive_lower = positive.lower()
            detected = []

            for style_name, keywords in auto_keywords.items():
                for kw in keywords:
                    if kw.lower() in positive_lower:
                        detected.append(style_name)
                        break

            detected = detected[:3]

            # rimozione conflitti
            final_styles = []
            for s in detected:
                conflict_list = conflicts.get(s, [])
                if any(c in final_styles for c in conflict_list):
                    continue
                final_styles.append(s)

            return final_styles

        # MANUAL STYLE
        if style_stack != "disable":
            return [style_stack]

        return []

    # =========================================================
    # MODULO 4.3: COSTRUZIONE BLOCCO STILE
    # =========================================================
    def _build_style_block(self, presets, active_styles, weights, lens_preset, use_nl):
        style_presets = presets.get("style_stacks", {}) or {}

        style_parts = []
        lens_parts = []
        negative_parts = []
        neg_to_pos_parts = []

        for style in active_styles:
            data = style_presets.get(style, {})
            if not data:
                continue

            style_parts.extend(data.get("lighting", []))
            style_parts.extend(data.get("color", []))
            style_parts.extend(data.get("extra", []))

            # lens derivata dallo stile (solo se lens_preset == disable)
            if lens_preset == "disable":
                lens = data.get("lens", "")
                if isinstance(lens, list):
                    lens = ", ".join([t.strip() for t in lens if t.strip()])
                if lens:
                    lens_parts.append(lens)

            negative_parts.extend(data.get("negative", []))
            neg_to_pos_parts.extend(data.get("neg_to_pos", []))

        w_style = weights.get("style_stack", 1.10)
        w_lens = weights.get("lens_preset", 1.08)

        style_block = self._format_block(", ".join(style_parts), w_style, use_nl) if style_parts else ""
        lens_block = self._format_block(", ".join(lens_parts), w_lens, use_nl) if lens_parts else ""

        negative_text = ", ".join(negative_parts)
        neg_to_pos_text = ", ".join(neg_to_pos_parts)

        return style_block, lens_block, negative_text, neg_to_pos_text

    # =========================================================
    # MODULO 5: LENS PRESET (manuale)
    # =========================================================
    def _build_lens_preset_block(self, presets, lens_preset, weights, use_nl):
        if lens_preset == "disable":
            return ""

        lens_data = presets.get("lens_presets", {}) or {}
        text = lens_data.get(lens_preset, "")

        if isinstance(text, list):
            text = ", ".join([t.strip() for t in text if t.strip()])

        if not text:
            return ""

        w = weights.get("lens_preset", 1.08)
        return self._format_block(text, w, use_nl)

    # =========================================================
    # MODULO 6: FRAMING FIX
    # =========================================================
    def _build_framing_fix_block(self, presets, framing_fix, weights, use_nl):
        if not framing_fix:
            return ""

        data = presets.get("framing_fix", {}) or {}
        text = data.get("positive", "")

        if isinstance(text, list):
            text = ", ".join([t.strip() for t in text if t.strip()])

        if not text:
            return ""

        w = weights.get("framing_fix", 1.12)
        return self._format_block(text, w, use_nl)

    # =========================================================
    # MODULO 7: ANTI ARTIFACTS
    # =========================================================
    def _build_anti_artifacts_block(self, presets, anti_artifact_level, weights, use_nl):
        if anti_artifact_level == "disable":
            return ""

        data = presets.get("anti_artifacts", {}) or {}
        text = data.get(anti_artifact_level, "")

        if isinstance(text, list):
            text = ", ".join([t.strip() for t in text if t.strip()])

        if not text:
            return ""

        w = weights.get("anti_artifacts", 0.95)
        return self._format_block(text, w, use_nl)

    # =========================================================
    # MODULO 9: POSITIVE CONFLICTS
    # =========================================================
    def _remove_positive_conflicts(self, text, presets, active_styles):
        if not text:
            return text

        conflicts = presets.get("positive_conflicts", {}) or {}

        parts = [p.strip() for p in text.split(",") if p.strip()]
        parts_norm = [self._normalize_term(p) for p in parts]

        conflict_terms = []
        for style in active_styles:
            for bad in conflicts.get(style, []):
                conflict_terms.append(self._normalize_term(bad))

        out = []
        for original, norm in zip(parts, parts_norm):
            remove = False

            for bad in conflict_terms:
                if norm == bad:
                    remove = True
                    break
                if bad in norm:
                    remove = True
                    break
                bad_words = bad.split()
                norm_words = norm.split()
                if all(w in norm_words for w in bad_words):
                    remove = True
                    break

            if not remove:
                out.append(original)

        return ", ".join(out)

    # =========================================================
    # MODULO 9.1.1: POS vs NEG CONFLICTS
    # =========================================================
    def _remove_pos_vs_neg_conflicts(self, positive_text, negative_text):
        if not positive_text or not negative_text:
            return negative_text

        pos_terms = [
            self._normalize_term(p)
            for p in positive_text.split(",")
            if p.strip()
        ]

        neg_original = [
            p.strip()
            for p in negative_text.split(",")
            if p.strip()
        ]
        neg_norm = [
            self._normalize_term(p)
            for p in neg_original
        ]

        out = []
        for orig, norm in zip(neg_original, neg_norm):
            remove = False

            for pos in pos_terms:
                if norm == pos:
                    remove = True
                    break
                if pos in norm:
                    remove = True
                    break
                pos_words = pos.split()
                norm_words = norm.split()
                if all(w in norm_words for w in pos_words):
                    remove = True
                    break

            if not remove:
                out.append(orig)

        return ", ".join(out)

    # =========================================================
    # MODULO 9.2: NEGATIVE CONFLICTS
    # =========================================================
    def _remove_negative_conflicts(self, negative_text, presets, active_styles):
        if not negative_text:
            return negative_text

        conflicts = presets.get("negative_conflicts", {}) or {}
        neg_parts = [p.strip() for p in negative_text.split(",") if p.strip()]

        to_remove = set()
        for style in active_styles:
            for bad in conflicts.get(style, []):
                to_remove.add(bad.lower())

        out = []
        for p in neg_parts:
            if p.lower() not in to_remove:
                out.append(p)

        return ", ".join(out)

    # =========================================================
    # MODULO 11: SEMANTIC COMPRESS (term-level)
    # =========================================================
    def _build_active_keyword_map(self, presets, active_styles):
        auto_keywords = presets.get("auto_style_keywords", {}) or {}
        style_presets = presets.get("style_stacks", {}) or {}

        keyword_to_cluster = {}

        for style in active_styles:
            style_data = style_presets.get(style, {})
            if not style_data:
                continue

            style_terms = []
            style_terms.extend(style_data.get("lighting", []))
            style_terms.extend(style_data.get("color", []))
            style_terms.extend(style_data.get("extra", []))

            for term in style_terms:
                term_norm = self._normalize_term(term)

                for cluster, kw_list in auto_keywords.items():
                    for kw in kw_list:
                        kw_norm = self._normalize_term(kw)
                        if kw_norm in term_norm:
                            keyword_to_cluster[kw_norm] = cluster

        return keyword_to_cluster

    def _semantic_compress_block(self, text, keyword_to_cluster):
        if not text:
            return text

        terms = [t.strip() for t in text.split(",") if t.strip()]
        seen_clusters = set()
        result_terms = []

        for term in terms:
            norm = self._normalize_term(term)
            matched_cluster = None

            for kw, cluster in keyword_to_cluster.items():
                if kw in norm.split():
                    matched_cluster = cluster
                    break

            if not matched_cluster:
                result_terms.append(term)
                continue

            if matched_cluster in seen_clusters:
                continue

            seen_clusters.add(matched_cluster)
            result_terms.append(term)

        return ", ".join(result_terms)

    # =========================================================
    # MODULO 11.2: TOKEN LIMIT INTELLIGENTE
    # =========================================================
    def _apply_token_limit(self, block_text, clip, max_tokens):
        """
        Riduce progressivamente i termini del blocco finché non rientra nel limite.
        """
        def estimate_tokens(t):
            return int(len(t) / 4)

        if not block_text:
            return block_text

        terms = [t.strip() for t in block_text.split(",") if t.strip()]
        if len(terms) <= 1:
            return block_text

        # ordina termini per lunghezza (più informativi prima)
        terms = sorted(terms, key=lambda t: len(t), reverse=True)

        # rimuovi termini uno alla volta
        while len(terms) > 1:
            candidate = ", ".join(terms)
            if estimate_tokens(candidate) <= max_tokens:
                return candidate
            terms.pop()  # rimuove il meno informativo

        return ", ".join(terms)

    # =========================================================
    # EXECUTE - PIPELINE COMPLETA CON NL v6
    # =========================================================
    def execute(
        self,
        model_version,
        clip,
        positive,
        negative,
        lora_tags,
        auto_style,
        style_stack,
        lens_preset,
        framing_fix,
        anti_artifact_level,
        flux_guidance,
    ):
        debug = {
            "connectors_used": [],
            "nl_block_order": [],
            "dedupe_removed": [],
            "conflicts_removed": [],
            "semantic_compress": [],
            "token_before": 0,
            "token_after": 0,
        }

         # DEBUG STORAGE
        debug_removed_terms = []
        debug_token_excess = 0
        debug_blocks_snapshot = {}


        # -----------------------------------------------------
        # FASE 1 — CARICAMENTO CONFIG E PRESET
        # -----------------------------------------------------
        model_cfg = self._load_model_config(model_version)
        presets = self._load_prompt_presets()
        weights, _ = self._load_weights_and_limits(presets)

        use_nl = model_cfg.get("use_natural_language", False)
        max_tokens = model_cfg.get("max_prompt_tokens", 512)

        # Prepara connettori dinamici per NL-clean
        self._nl_connectors = self._collect_connectors_from_presets(presets)

        # -----------------------------------------------------
        # FASE 2 — COSTRUZIONE BLOCCHI TECNICI (NO NL)
        # -----------------------------------------------------
        # Bibbia
        lora_block = self._build_lora_block(lora_tags, weights, use_nl=False)
        user_block = self._build_user_block(positive, weights, use_nl=False)

        # Stili
        active_styles = self._select_styles(presets, positive, auto_style, style_stack)

        style_block, style_lens_block, style_negative, style_neg_to_pos = \
            self._build_style_block(presets, active_styles, weights, lens_preset, use_nl=False)

        # Lens override
        if lens_preset != "disable":
            style_lens_block = ""

        # Accessori
        base_quality_block, base_quality_negative = \
            self._build_base_quality_block(presets, weights, use_nl=False)

        lens_preset_block = self._build_lens_preset_block(
            presets, lens_preset, weights, use_nl=False
        )
        framing_fix_block = self._build_framing_fix_block(
            presets, framing_fix, weights, use_nl=False
        )
        anti_artifacts_block = self._build_anti_artifacts_block(
            presets, anti_artifact_level, weights, use_nl=False
        )

        # PFN
        neg_to_pos_block = ""
        if model_cfg.get("negative_to_positive", False) and style_neg_to_pos:
            neg_to_pos_block = self._format_block(
                style_neg_to_pos, weights.get("pfn", 1.05), use_nl=False
            )

        # Snapshot dei blocchi tecnici per debug
        debug_blocks_snapshot = {
            "lora_tags": lora_block,
            "user_prompt": user_block,
            "base_quality": base_quality_block,
            "style": style_block,
            "style_lens": style_lens_block,
            "lens": lens_preset_block,
            "framing": framing_fix_block,
            "anti_artifacts": anti_artifacts_block,
            "neg_to_pos": neg_to_pos_block,
        }

        # Negativo grezzo
        auto_negative_cfg = presets.get("auto_negative", {}) or {}
        auto_negative_terms = auto_negative_cfg.get(anti_artifact_level, [])
        negative_text = ", ".join(
            [negative, base_quality_negative, style_negative, ", ".join(auto_negative_terms)]
        )

        # -----------------------------------------------------
        # FASE 3 — DEDUPE & CONFLICTS
        # -----------------------------------------------------
        bibbia_ref = f"{lora_block}, {user_block}"

        auto_blocks = [
            base_quality_block,
            style_block,
            style_lens_block,
            lens_preset_block,
            framing_fix_block,
            anti_artifacts_block,
            neg_to_pos_block,
        ]

        deduped = self._dedupe_with_priority(auto_blocks, bibbia_ref, presets)

        (
            base_quality_block,
            style_block,
            style_lens_block,
            lens_preset_block,
            framing_fix_block,
            anti_artifacts_block,
            neg_to_pos_block,
        ) = deduped

        # Positive conflicts
        style_block = self._remove_positive_conflicts(style_block, presets, active_styles)

        # Negative conflicts
        negative_text = self._remove_negative_conflicts(negative_text, presets, active_styles)

        # Cross pos-vs-neg
        full_positive_temp = ", ".join(
            [p for p in [lora_block, user_block, style_block, base_quality_block] if p]
        )
        negative_text = self._remove_pos_vs_neg_conflicts(full_positive_temp, negative_text)

        # -----------------------------------------------------
        # FASE 4 — OTTIMIZZAZIONE DIMENSIONALE
        # -----------------------------------------------------
        def count_tokens(txt):
            if not txt:
                return 0
            return len(clip.tokenize(txt).get("l", []))

        blocks = {
            "base_quality": [base_quality_block, weights.get("base_quality", 1.0)],
            "style": [style_block, weights.get("style_stack", 1.0)],
            "lens": [lens_preset_block, weights.get("lens_preset", 1.0)],
            "style_lens": [style_lens_block, weights.get("lens_preset", 1.0)],
            "framing": [framing_fix_block, weights.get("framing_fix", 1.12)],
            "anti_artifacts": [anti_artifacts_block, weights.get("anti_artifacts", 0.95)],
            "neg_to_pos": [neg_to_pos_block, weights.get("pfn", 1.05)],
        }

        def build_full_positive():
            parts = [lora_block, user_block] + [v[0] for v in blocks.values()]
            return ", ".join([p for p in parts if p])

        debug["token_before"] = count_tokens(build_full_positive())

        # 4.1 Semantic compress
        if debug["token_before"] > max_tokens:
            kw_map = self._build_active_keyword_map(presets, active_styles)
            for key in blocks:
                blocks[key][0] = self._semantic_compress_block(blocks[key][0], kw_map)

        # 4.2 Token limit
        if count_tokens(build_full_positive()) > max_tokens:
            for key in blocks:
                before = blocks[key][0]
                if not before:
                    continue

                after = self._apply_token_limit(before, clip, max_tokens)
                blocks[key][0] = after

                # debug: termini tagliati dal token limit
                if (before or "").strip() != (after or "").strip():
                    debug_removed_terms.append(
                        f"{key}: '{before}' -> '{after}'"
                    )

        # token in eccesso
        debug_token_excess = max(0, debug["token_before"] - count_tokens(build_full_positive()))
        debug["token_after"] = count_tokens(build_full_positive())

        # Riassegna blocchi ottimizzati
        base_quality_block = blocks["base_quality"][0]
        style_block = blocks["style"][0]
        lens_preset_block = blocks["lens"][0]
        style_lens_block = blocks["style_lens"][0]
        framing_fix_block = blocks["framing"][0]
        anti_artifacts_block = blocks["anti_artifacts"][0]
        neg_to_pos_block = blocks["neg_to_pos"][0]

        # -----------------------------------------------------
        # FASE 5 — ASSEMBLAGGIO (NL v6 o Weighted)
        # -----------------------------------------------------
        extra_blocks = [
            ("base_quality", base_quality_block, weights.get("base_quality", 1.0)),
            ("style", style_block, weights.get("style_stack", 1.0)),
            ("lens", lens_preset_block, weights.get("lens_preset", 1.0)),
            ("style_lens", style_lens_block, weights.get("lens_preset", 1.0)),
            ("framing", framing_fix_block, weights.get("framing_fix", 1.12)),
            ("anti_artifacts", anti_artifacts_block, weights.get("anti_artifacts", 0.95)),
            ("neg_to_pos", neg_to_pos_block, weights.get("pfn", 1.05)),
        ]

        extra_blocks = [b for b in extra_blocks if b[1]]
        extra_blocks.sort(key=lambda x: x[2], reverse=True)

        # Helper per NL
        def strip_weight(block):
            block = (block or "").strip()
            if block.startswith("(") and block.endswith(")") and ":" in block:
                inner = block[1:-1]
                before, _ = inner.rsplit(":", 1)
                return before.strip()
            return block

        if use_nl:
            lora_nl = (lora_tags or "").strip()
            user_nl = (positive or "").strip()

            sorted_extra = [(key, strip_weight(text)) for key, text, _ in extra_blocks]

            positive_text = self._build_nl_prompt_with_connectors(
                lora_nl, user_nl, sorted_extra, presets, active_styles
            )
            positive_text = self._nl_clean(positive_text)
            negative_text = self._nl_clean(negative_text)

        else:
            sorted_text_parts = [t for (_, t, _) in extra_blocks]
            all_parts = [lora_block, user_block] + sorted_text_parts
            positive_text = ", ".join([p for p in all_parts if p])

        # Dedupe finale di sicurezza
        pos_parts = [p.strip() for p in positive_text.split(",") if p.strip()]
        positive_text = ", ".join(dict.fromkeys(pos_parts))

        # -----------------------------------------------------
        # FASE 6 — CLIP ENCODING & RITORNO
        # -----------------------------------------------------
        pos_tokens = clip.tokenize(positive_text)
        neg_tokens = clip.tokenize(negative_text)

        raw_cond_p, raw_pooled_p = clip.encode_from_tokens(pos_tokens, return_pooled=True)
        raw_cond_n, raw_pooled_n = clip.encode_from_tokens(neg_tokens, return_pooled=True)

        # 2. Inizializzazione variabili finali
        cond_positive = raw_cond_p
        pooled_positive = raw_pooled_p
        
        cond_negative = raw_cond_n
        pooled_negative = raw_pooled_n

        # 3. Applicazione Guidance (solo al positivo finale)
        if model_cfg.get("supports_guidance", False):
            metadata_pos = {"pooled_output": pooled_positive, "guidance": float(flux_guidance)}
        else:
            metadata_pos = {"pooled_output": pooled_positive}

        # 4. Logica Zero Negative (basata sui raw per pulizia)
        if model_cfg.get("zero_negative", False):
            cond_negative = raw_cond_p.clone() * 0.0
            if raw_pooled_p is not None:
                pooled_negative = raw_pooled_p.clone() * 0.0


        debug_log = (
            f"--- DEBUG LOG ---\n"
            f"Model: {model_version}\n"
            f"Method: {'NL' if use_nl else 'Weighted'}\n"
            f"Active Styles -> {active_styles}\n"
            f"Tokens Before: {debug['token_before']}\n"
            f"Tokens After: {debug['token_after']}\n"
            f"Token Excess Removed -> {debug_token_excess}\n"
        )

        # blocchi positivi separati
        debug_log += "Positive Blocks:\n"
        for name, value in debug_blocks_snapshot.items():
            if value:
                debug_log += f"  >> {name} -> {value}\n"

        # termini rimossi dal token limit
        if debug_removed_terms:
            debug_log += "Token-Limit Removed Terms:\n"
            for line in debug_removed_terms:
                debug_log += f"  - {line}\n"

        debug_log += f"\nPositive Preview:\n{positive_text}"

        debug_log += f"\n\nNegative Preview:\n{negative_text}"

        return (
            [[cond_positive, metadata_pos]],
            [[cond_negative, {"pooled_output": pooled_negative}]],
            positive_text,
            negative_text,
            debug_log,
            )


# =========================================================
# API
# =========================================================
@PromptServer.instance.routes.get("/znodes/presets")
async def get_presets(request):
    return web.json_response({
        "models": ZN_Adv_Prompt._load_json("models_presets.json"),
        "presets": ZN_Adv_Prompt._load_json("prompt_presets.json"),
    })


NODE_CLASS_MAPPINGS = {"ZN_Adv_Prompt": ZN_Adv_Prompt}
NODE_DISPLAY_NAME_MAPPINGS = {"ZN_Adv_Prompt": "⧉ ZN Advanced Prompt (by Model)"}
