# ZN_ComfyUI_Nodes
A collection of essential, lightweight nodes designed for efficiency and streamlined workflows

## 📜 Disclaimer & Philosophy
**Please read before using:**
* **Not a Coder:** I am not a professional developer. I created these nodes primarily for my personal use to solve specific problems in my own workflows.
* **As-Is:** I'm sharing them because I think they might be useful to others, but I offer **no guarantees, no formal support, and no assistance.** Use them at your own risk.
* **Why these nodes?** I was tired of installing massive node suites just to use a single node. This repository follows a "less is more" philosophy: it contains only the essentials I actually use, keeping the workflow clean and avoiding unnecessary bloat.

## 🛠️ Installation
---

Choose one of the following methods:

### Method 1: Using Git (Recommended)
1. Open a terminal/command prompt.
2. Navigate to your ComfyUI custom nodes folder:
   ```bash
   cd ComfyUI/custom_nodes/
4. Clone the repository:
    ```bash
   git clone https://github.com/znortr/ZN_ComfyUI_Nodes.git
5. Restart ComfyUI.

### Method 2: Manual Download (Full Suite)
1. Download this repository as a **ZIP file** from the green **Code** button above.
2. Extract the contents into `ComfyUI/custom_nodes/`.
3. **Crucial:** Ensure the folder is named `ComfyUI-Zn-Nodes` and that the `__init__.py` file is located directly inside it (not in a double subfolder).
4. Restart ComfyUI.

### Method 3: Selective Manual Installation (Individual Nodes)
If you only want to install specific nodes from this suite:
1. Create a folder named `ComfyUI-Zn-Nodes` in your `custom_nodes/` directory.
2. Download the `__init__.py` and only the specific `.py` files of the nodes you wish to use.
3. Download the `web` and `presets` folders:
   * **Web files:** Each `.js` file has the same name as its corresponding `.py` node; you can easily pick only the ones you need.
   * **Presets:** It is highly recommended to keep all `.json` files within this folder to ensure everything works correctly.
4. **Edit __init__.py:** Open the file and **comment out** (add a `#` at the start of the line) or delete the references to the nodes you did not download to prevent startup errors.
5. Restart ComfyUI
---
## 💡 Tips:
* **JSON Configs:** The nodes will automatically create/read configuration files in the `presets/` folder. Do not delete this folder!
* **UI Updates:** If you don't see the new UI features (like the resolution buttons), clear your browser cache and refresh the page.
* **Requirements:** These nodes use standard ComfyUI libraries. No additional `pip install` is required.
---
---
<a name="the-essential-suite"></a>
## 🚀 The Essentials Suite
---

### 🎨 Prompt & LoRA Handling

[**Zn Adv Prompt**](#zn-adv-prompt)<br>is a dynamic prompt engineering engine designed to automate the creation of complex descriptions. It optimizes syntax for generative models by transforming simple ideas into high-quality, structured instructions.<br><br>
[**Zn Lora Helper**](#zn-lora-helper)<br>acts as an automated, high-compatibility bridge for the LoRA management. It allows to leverage the organizational power of the **LoraManager (Lora Stacker)** while routing the actual data through standard or specialized loaders (like Nunchaku or official ComfyUI loaders).

---

---
<a name="zn-adv-prompt"></a>
## 🧠 Zn Adv Prompt

**Zn Adv Prompt** is a dynamic prompt engineering engine designed to automate the creation of complex descriptions. It optimizes syntax for generative models (such as Flux, SDXL, and WanVideo) by transforming simple ideas into high-quality, structured instructions.

| Feature | Description |
| :--- | :--- |
| **Smart Style Engine** | Automatically detects the best visual style by analyzing keywords in your text or applies manual presets defined via JSON. |
| **Natural Language (NL) V6** | Converts technical tag lists into fluid, natural sentences (e.g., *"A, B, C"* → *"A, B and C"*) using dynamic connectors to maximize model comprehension. |
| **Cross-Block Deduplication** | A deep cleaning pipeline that prevents redundancies between user text, LoRA tags, and style presets, keeping the prompt focused and efficient. |
| **Automated Quality & Lens** | Automatically injects "Base Quality" settings for sharpness and "Lens Presets" based on real-world cinematography. |
| **Conflict Resolution** | Intelligently manages semantic contrasts, ensuring that Negative Prompts do not cancel out explicitly requested Positive elements. |
| **Token Optimization** | Features semantic compression and token-limit management to ensure the prompt fits perfectly within CLIP encoder constraints without losing essential details. |

### ⚖️ The Logic
Unlike standard nodes that simply "stack" words, this system applies a strict **logical hierarchy**. The **LoRA + User Prompt** always retains absolute priority. Styles, framing fixes, and anti-artifact rules are dynamically fused as supporting layers to enhance the original concept without overpowering it.

### ⚡ Built-in Workflow Optimization
The node is designed to replace multiple utility nodes, significantly streamlining your ComfyUI graph:

* **Integrated Flux Guidance:** The `flux_guidance` parameter is baked directly into the positive conditioning output. You don't need an extra "FluxGuidance" node.
* **Automatic Zero-Out Conditioning:** For models that do not require a negative prompt, the node automatically handles the **Zero-out conditioning** logic. The `negative` output is already optimized, eliminating the need for manual "ConditioningZeroOut" nodes.
* **Plug-and-Play Output:** The node outputs both the encoded **Conditioning** (ready for the Sampler) and the raw **String** (for debugging or display), acting as a bridge between complex logic and clean execution.

### ⚙️ Full Customization
All logic—including weights, NL connectors, styles, and limits—is decoupled from the Python code. Everything is stored in the `presets/` JSON files, allowing you to update the node's behavior **on the fly** without ever touching a line of code.

### 🛠️ Technical Pipeline
1. **Normalization:** Standardizes all input terms (lowercase, hyphen removal, etc.).
2. **Deduplication:** Compares the "Bible" blocks against style blocks to prune repeated adjectives.
3. **NL Construction:** Applies specific connectors (e.g., *"shot on"*, *"featuring"*, *"with"*) based on the active style's grammar rules.
4. **Final Cleanup:** Removes double commas, extra spaces, and trailing punctuation for a "ready-to-generate" string.

---

> [!TIP]
> To expand the node's capabilities, simply edit `prompt_presets.json`. You can add new styles, modify the "framing_fix" tags, or adjust the "anti_artifacts" intensity levels to suit your specific workflow needs.

[↑ Top](#the-essential-suite)
---
