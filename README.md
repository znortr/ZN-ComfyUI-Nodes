# ZN_ComfyUI_Nodes
A collection of essential, lightweight nodes designed for efficiency and streamlined workflows

## 📜 Disclaimer & Philosophy

**Before diving in, a few things worth knowing:**

* **Not a Coder (officially):**  
  I’m not a professional developer — these nodes were created to solve very specific needs in my own workflows.  
  They work beautifully *for me*, which is usually a good sign… but not a contractual guarantee.

* **As‑Is:**  
  I created these nodes for myself, and I’m sharing them because I believe they can be useful to others as well.  
  Everything here is provided *as it is*.  
  I don’t promise support, fixes, or feature requests — but if something is genuinely broken and I notice it, there’s a good chance I’ll fix it.  
  Just don’t treat this place like a customer service desk.

* **Why these nodes?**  
  Because I was tired of installing gigantic, bloated node suites just to use one single useful node.  
  This repo follows a simple philosophy: **clean, essential, zero bloat**.

* **Modular by Design:**  
  Every node is intentionally built as a **standalone module**.  
  Install only what you need — no forced bundles, no dependency jungles, no “all-or-nothing” packages.

* **Work in Progress:**  
  This repository evolves whenever I refine my own workflows.  
  Things may improve, change, or disappear entirely.  
  Consider it a living toolbox rather than a finished product.

---
## 🛠️ How To Install
---

Choose one of the following methods:

### Method 1: Using Git (Recommended)
1. Open a terminal/command prompt.
2. Navigate to your ComfyUI custom nodes folder:
   ```bash
   cd ComfyUI/custom_nodes/
4. Clone the repository:
    ```bash
   git clone https://github.com/znortr/ZN-ComfyUI-Nodes.git
5. Restart ComfyUI.

### Method 2: Manual Download (Full Suite)
1. Download this repository as a **ZIP file** from the green **Code** button above.
2. Extract the contents into `ComfyUI/custom_nodes/`.
3. **Crucial:** Ensure the folder is named `ZN-ComfyUI-Nodes` and that the `__init__.py` file is located directly inside it (not in a double subfolder).
4. Restart ComfyUI.

### Method 3: Selective Manual Installation (Individual Nodes)
If you only want to install specific nodes from this suite:
1. Create a folder named `ZN-ComfyUI-Nodes` in your `custom_nodes/` directory.
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
## 📝 Update History

| Date | Node | Update |
| :--- | :--- | :--- |
| **2026-07-02** | **ZN Image Preview & Save ADV** | Added standard ComfyUI right-click context menu: **Open Image**, **Save Image**, **Copy Image**. Supports both Image A and Image B (submenu grouping when both are active). Fixed image loading to use permanent server URLs for full native compatibility. |
| **2026-07-10** | **ZN Image Preview & Save ADV** | Add methods for persistent image preview state management- |
| **2026-07-13** | **ZN LoRA Helper** | Add automatic bypass of empty LoRA slots.|


---
<a name="the-essential-suite"></a>
## 🚀 The Essentials Suite
---

### 🎨 Prompt & LoRA Handling

[⧉ **ZN Adv Prompt**](#zn-adv-prompt)<br>
is a dynamic prompt engineering engine designed to automate the creation of complex descriptions. It optimizes syntax for generative models by transforming simple ideas into high-quality, structured instructions.<br><br>

[⧉ **ZN Lora Helper**](#zn-lora-helper)<br>
acts as an automated, high-compatibility bridge for the LoRA management. It allows to leverage the organizational power of the **LoraManager (Lora Stacker)** while routing the actual data through standard or specialized loaders (like Nunchaku or official ComfyUI loaders).

### 🖼️ Resolution Management

[⧉ **ZN Opt Resolution**](#zn-opt-resolution)<br>
A smart resolution manager that handles optimal resolutions based on the selected model. It automatically calculates the correct latent size, ensures dimensions follow model requirements (multiples of 8 or 16), and allows scaling by Megapixel targets. All additions to resolution_preset.json are automatically managed and updated in the UI.<br><br>

[⧉ **ZN Nearest Resolution**](#zn-nearest-resolution)<br>
is an intelligent image adaptation node. It takes an input image and automatically snaps it to the **closest optimal resolution** supported by the selected generative model, ensuring the model works on a dimensional base it was specifically trained for.

### 🧠 Logic & Automation

[⧉ **ZN Smart Bypasser**](#zn-smart-bypasser)<br>
is an advanced multi-target automation node for ComfyUI that dynamically controls the bypass state of other nodes using a flexible trigger signal (int, float, string, boolean, or image mask).

[⧉ **ZN SeedVR2 Smart Controller**](#zn-seedvr2-smart-controller)<br>
is a SeedVR2-dedicated controller that computes the target resolution from the input image and dynamically adjusts VAE tiling based on available VRAM. It enforces full-frame processing and does **not** perform upscaling.

[⧉ **ZN Smart Flusher**](#zn-smart-flusher)<br>
is an intelligent cache management node that flushes ComfyUI caches only when truly necessary. It automatically detects conditioning changes, keeping models loaded for maximum performance while remaining ideal for complex workflows, memory management, and resolving the recent Z-Image Nunchaku slowdown caused by prompt change detection.

### 🖼️ Image Tools

[⧉ **ZN ImageMask Bridge**](#zn-imagemask-bridge)<br>
is a multi-purpose routing bridge that transmits images while providing an integrated Mask Editor to create and output masks.

[⧉ **ZN Image Preview & Save ADV**](#zn-image-preview-save-adv)<br>
is an advanced image viewer that supports both dual-image comparison and single-image preview, with integrated save options.

### 🎬 Video (WanVideo)

[⧉ **ZN Wan Video Settings**](#zn-wan-video-settings)<br>
Central configuration hub for WanVideo workflows. Acts as a "Single Point of Truth" for video dimensions and timing.<br>• **Optimal Presets:** Quick resolution switching.<br>• **Smart Frame Math:** Calculates total frames based on duration.<br>• **Interpolation Ready:** Computes final FPS for RIFE multipliers.

---
---
<a name="zn-adv-prompt"></a>
## 🧠 ⧉ ZN Adv Prompt

**ZN Adv Prompt** is a dynamic prompt engineering engine designed to automate the creation of complex descriptions. It optimizes syntax for generative models (such as Flux, SDXL, and WanVideo) by transforming simple ideas into high-quality, structured instructions.

| Feature | Description |
| :--- | :--- |
| **Smart Style Engine** | Automatically detects the best visual style by analyzing keywords in your text or applies manual presets defined via JSON. |
| **Natural Language (NL) V6** | Converts technical tag lists into fluid, natural sentences (e.g., *"A, B, C"* → *"A, B and C"*) using dynamic connectors to maximize model comprehension. |
| **Cross-Block Deduplication** | A deep cleaning pipeline that prevents redundancies between user text, LoRA tags, and style presets, keeping the prompt focused and efficient. |
| **Automated Quality & Lens** | Automatically injects "Base Quality" settings for sharpness and "Lens Presets" based on real-world cinematography. |
| **Conflict Resolution** | Intelligently manages semantic contrasts, ensuring that Negative Prompts do not cancel out explicitly requested Positive elements. |
| **Token Optimization** | Features semantic compression and token-limit management to ensure the prompt fits perfectly within CLIP encoder constraints without losing essential details. |

### ⚖️ The "Bible" Logic

Unlike standard nodes that simply "stack" words, this system applies a strict **logical hierarchy**. The **LoRA + User Prompt (The "Bible")** always retains absolute priority. Styles, framing fixes, and anti-artifact rules are dynamically fused as supporting layers to enhance the original concept without overpowering it.

### ⚡ Built-in Workflow Optimization

The node is designed to replace multiple utility nodes, significantly streamlining your ComfyUI graph:

* **Integrated Flux Guidance:** The flux_guidance parameter is baked directly into the positive conditioning output. You don't need an extra "FluxGuidance" node.
* **Automatic Zero-Out Conditioning:** For models that do not require a negative prompt, the node automatically handles the **Zero-out conditioning** logic. The negative output is already optimized, eliminating the need for manual "ConditioningZeroOut" nodes.
* **Plug-and-Play Output:** The node outputs both the encoded **Conditioning** (ready for the Sampler) and the raw **String** (for debugging or display), acting as a bridge between complex logic and clean execution.

### ⚙️ Full Customization

All logic—including weights, NL connectors, styles, and limits—is decoupled from the Python code. Everything is stored in the presets/ JSON files, allowing you to update the node's behavior **on the fly** without ever touching a line of code.

### 🛠️ Technical Pipeline

1. **Normalization:** Standardizes all input terms (lowercase, hyphen removal, etc.).
2. **Deduplication:** Compares the "Bible" blocks against style blocks to prune repeated adjectives.
3. **NL Construction:** Applies specific connectors (e.g., *"shot on"*, *"featuring"*, *"with"*) based on the active style's grammar rules.
4. **Final Cleanup:** Removes double commas, extra spaces, and trailing punctuation for a "ready-to-generate" string.

---
> [!TIP]
> To expand the node's capabilities, simply edit prompt_presets.json. You can add new styles, modify the "framing_fix" tags, or adjust the "anti_artifacts" intensity levels to suit your specific workflow needs.

[↑ Top](#the-essential-suite)

---
---
<a name="zn-lora-helper"></a>
## 📎 ⧉ ZN Lora Helper

**ZN Lora Helper** acts as an automated, high-compatibility bridge for your LoRA management. It allows you to leverage the organizational power of the **LoraManager (Lora Stacker)** while routing the actual data through standard or specialized loaders (like Nunchaku or official ComfyUI loaders).

| Feature | Description |
| :--- | :--- |
| **Conflict Prevention** | Solves compatibility issues by extracting LoRA data from "Stacks" and converting them into standard outputs. |
| **Trigger Word Sync** | Automatically extracts and cleans trigger words from the stack to pass them directly to prompt encoders. |
| **Multi-Slot Routing** | Supports up to **5 simultaneous LoRA entries**, providing individual path and strength outputs for each. |
| **Dynamic UI Feedback** | Real-time exposure of active LoRA filenames directly in the node interface for better workflow tracking. |
| **Normalization** | Built-in regex engine to clean up trigger word formatting (removing double spaces/commas) on the fly. |

### 🛠️ Why use this instead of a standard Lora Stack?

Many advanced loaders and specialized sampling nodes (e.g., **Nunchaku**, **X-Labs**, or custom **Flux loaders**) are not designed to accept a LORA_STACK type. **ZN Lora Helper** bridges this gap:

1. It reads your easy-to-manage **LoraManager** stack.
2. It breaks it down into individual STRING (path) and FLOAT (strength) outputs.
3. You can then plug these into **any** standard LoRA loader, ensuring 100% compatibility across different custom node suites.

### 📥 Inputs & Outputs

- **Inputs:**
  - lora_stack: The output from any LoraManager/Stacker node.
  - trigger_words: The combined trigger string from your manager.
- **Outputs:**
  - trigger_words: A sanitized, ready-to-use string.
  - lora_path_1 to 5: The file paths for your selected LoRAs.
  - strength_1 to 5: The individual power levels for each LoRA.

> [!WARNING]
> This node requires the **Lora Stacker (LoraManager)** suite to be installed as it is designed to work as its dedicated extension.

[↑ Top](#the-essential-suite)

---
---
<a name="zn-opt-resolution"></a>
## 📏 ⧉ ZN Opt Resolution

**ZN Opt Resolution** is a smart resolution manager designed to ensure your generations always use the optimal latent dimensions. It aligns your workspace with the specific training standards of different architectures (Flux, SDXL, SD1.5), preventing distortions and maximizing image quality.

| Feature | Description |
| :--- | :--- |
| **Model-Specific Presets** | Automatically loads the best resolution sets for the selected model architecture (e.g., 1024x1024 for SDXL/Flux). |
| **Megapixel Scaling** | Scale any custom resolution to a specific target (1MP, 2MP, etc.) while maintaining the desired aspect ratio. |
| **Smart Latent Generation** | Generates the latent noise directly, ensuring dimensions are perfect multiples (8, 16) as required by the model. |
| **Rounding Control** | Choose between *nearest*, *floor*, or *ceil* rounding to handle custom dimensions without breaking the VAE/Sampler. |
| **Live UI Sync** | Fully dynamic: any new resolution or model added to the resolution_preset.json is instantly available in the node's dropdown. |

---
### 🎯 Why it matters: The "Safety Net"

Most generative models (like Flux or SDXL) are extremely sensitive to dimensions. Entering "wrong" resolutions (not multiples of 8 or 16) often leads to **VAE crashes** or **compositional artifacts** (like double heads).

**ZN Opt Resolution** acts as a safety net:

- **Auto-Correction:** Even in **Manual Mode**, if you enter non-standard dimensions (e.g., 1013 x 761), the node instantly recalculates them to the nearest optimal values based on the model's requirements (e.g., 1024 x 768).
- **Aspect Ratio Locking:** When using **Megapixel Scaling**, the node takes your manual dimensions, calculates the aspect ratio, and scales it to the target MP while ensuring the final result is perfectly compatible with the model's architecture.

### ⚙️ Technical Highlights

- **Smart Rounding Logic:** Automatically snaps dimensions to the required multiples (8, 16, or 32) using your preferred rounding_mode. No more manual math.
- **Latent Downscale Awareness:** It knows exactly how the model "sees" pixels. It calculates the latent shape by considering the latent_downscale factor, ensuring the latent noise matches the pixel output perfectly.
- **Hardware Optimized:** Choose where to generate the initial noise (CUDA for speed or CPU for memory saving), preventing OOM (Out of Memory) errors during the first step of the workflow.

> [!IMPORTANT]
> **Forget about "Invalid Resolution" errors.** This node ensures that whatever you input is transformed into the "Best Possible Resolution" that the selected model can handle.

### 📥 Inputs & Outputs

- **Inputs:**
  - model_name: Select architecture (Flux, SDXL, SD1.5, etc.).
  - resolution: Select a preset ratio or "Manual" for custom input.
  - target_megapixels: Force the output to a specific Megapixel area.
- **Outputs:**
  - width / height: The final, rounded dimensions (INT).
  - latent: The ready-to-use latent noise for your Sampler.
  - info: A debug string showing the active configuration.

> [!TIP]
> Use the "Manual" mode combined with "Target Megapixels" to upscale your favorite aspect ratios while keeping them optimized for the model's training limit.

[↑ Top](#the-essential-suite)

---
---
<a name="zn-nearest-resolution"></a>
## 🖼️ ⧉ ZN Nearest Resolution

**ZN Nearest Resolution** is an intelligent image adaptation node. It takes an input image and automatically "snaps" it to the **closest optimal resolution** defined in the model's native training presets.

### 🎯 Native Training Alignment

The core strength of this node lies in its JSON presets: they represent the **exact training buckets** (dimensions and aspect ratios) used to train the generative models. By forcing your input image into these specific "Native" resolutions, you ensure the model works within its absolute **"Sweet Spot"**, drastically reducing composition errors, double heads, and distorted subjects.

### 🧠 Intelligent Matching Logic

Unlike simple resizers, this node uses a **weighted scoring algorithm** to pick the perfect target resolution:

- **Aspect Ratio Priority:** Minimizes cropping or distortion by matching the input's shape to the closest native bucket.
- **Megapixel Alignment:** Ensures the pixel density stays close to the original to avoid upscaling artifacts.
- **Model Priority (🟩/🟨/🟥):** Factors in the "preferred" resolutions defined in your presets (e.g., giving higher priority to 1024x1024 for SDXL as the primary training target).

### 🎨 Advanced Resize Strategies

It supports multiple professional methods to fit your image into the target native bucket:

- **Fill/Crop:** Fills the entire frame (ideal for backgrounds).
- **Fit/Pad:** Preserves the whole image by adding black borders.
- **Letterbox:** Symmetric cinematic padding.
- **Stretch:** Fast deformation to exactly match the target.

| Feature | Description |
| :--- | :--- |
| **Smart Scoring** | A balanced formula: (Aspect Delta * 0.7) + (Size Delta * 0.3) + Priority Weight. |
| **High-Quality Interpolation** | Supports Lanczos, Bicubic, and Bilinear for maximum clarity. |
| **Ultra-Safe Code** | Built-in compatibility layer for different Pillow versions (avoids common resample errors). |
| **Visual Match Debug** | Outputs a detailed text report explaining the "Match Quality" and why that specific resolution was chosen. |

### 🛠️ Technical Highlights

- **Single Image Pipeline:** Optimized for precise control over a single reference or init image.
- **Preset Driven:** Reads directly from presets/resolution_preset.json, allowing for instant updates to model standards.
- **Conformity Check:** The debug output provides a rating (Excellent, Good, Acceptable) to let you know how well the image fits the model's native knowledge.

> [!IMPORTANT]
> Use this node to "conform" any reference image to the model's native training standards. This ensures that the structure of your input image aligns perfectly with the model's internal logic, leading to superior generation results.

[↑ Top](#the-essential-suite)

---
---
<a name="zn-smart-bypasser"></a>
## ⧉ ZN Smart Bypasser

ZN Smart Bypasser is an advanced automation utility for ComfyUI designed to dynamically control the execution state of **multiple target nodes**. It works as a logic-driven controller that can automatically enable or disable **BYPASS (mute mode)** based on a trigger signal, helping you optimize workflow performance and build fully dynamic graphs.

---
## 🤖 Smart Trigger Logic

The node evaluates the input signal and converts it into a BYPASS command:

- **TRUE → BYPASS ACTIVE (target nodes muted / purple)**
- **FALSE → BYPASS OFF (target nodes active)**

### Supported Input Types

**INT / FLOAT / STRING**

- 0, 1, 0.0, 1.0, "0", "1" → **TRUE (BYPASS ACTIVE)**
- Any other value → **FALSE (BYPASS OFF)**

**BOOLEAN / STRING**

- True, "true" → **BYPASS ACTIVE**
- False, "false" → **BYPASS OFF**

---
## 🖼️ Image Mask Detection

When connected to:

- LoadImage
- zn_ImageMask_Bridge (mask output)

The node automatically switches to **mask-based logic**:

- **Mask present (alpha detected)** → Target nodes ACTIVE (NO bypass)
- **No mask detected** → Target nodes BYPASSED

### 🔁 Invert Mask Logic (UI Checkbox)

- Mask present → BYPASSED
- No mask → ACTIVE

---
## 🔗 Multi-Target Control

- Control **unlimited target nodes**
- Dynamically add/remove targets
- Apply the same logic to entire sections of your workflow

---
## 🔄 Signal Pass-Through

- trigger_output is a **perfect pass-through**
- Enables chaining multiple logic nodes
- Allows reuse of the same signal elsewhere

---
## 🎯 Key Use Cases

**Conditional Rendering**

- Skip heavy nodes (Upscalers, Detailers, etc.) when not needed

**Mask-Aware Workflows**

- Automatically disable inpainting steps when no mask is present

**Dynamic Graph Logic**

- Enable/disable entire branches of your workflow

**Performance Optimization**

- Avoid unnecessary computation during batch runs

---
## ⚙️ Features

| Feature | Description |
|--------|------------|
| **Multi-Target Control** | Control an unlimited number of target nodes from a single trigger input. Ideal for enabling/disabling entire workflow branches with one signal. |
| **Universal Input** | Accepts multiple data types (int, float, string, boolean, and image mask) with automatic interpretation—no need for manual conversions or adapters. |
| **Automatic Type Detection** | Detects and normalizes incoming values in real time, converting them into a consistent TRUE/FALSE logic for reliable bypass control. |
| **Mask-Aware Logic** | Automatically detects the presence of an image mask (alpha channel) and switches behavior: mask present → nodes active, no mask → nodes bypassed. Includes optional inversion via UI checkbox. |
| **Real-Time Evaluation** | Continuously evaluates the trigger signal and updates target node states instantly during workflow execution. |
| **Zero Data Interference** | Acts as a pure controller: it never modifies or blocks data flow, only changes the execution state (bypass) of connected nodes. |
| **Visual Feedback** | Target nodes immediately reflect their state in the UI (purple = bypass), providing clear and instant visual confirmation. |

---
## 📥 Inputs & Outputs

**Inputs**

- trigger_input → Control signal (any supported type)
- target_node_* → One or more nodes to control

**Outputs**

- trigger_output → Unmodified input signal (pass-through)

---
## 💡 Tip

Use ZN Smart Bypasser to build **fully conditional workflows**. Example: Automatically skip an inpainting pipeline when no mask is detected, keeping your generation fast and efficient without manual toggles.

[↑ Top](#the-essential-suite)

---
---
<a name="zn-wan-video-settings"></a>
## 🎬 ⧉ ZN Wan Video Settings

**ZN Wan Video Settings** is the central configuration hub for WanVideo workflows. It acts as a **"Single Point of Truth"** for video dimensions and timing, eliminating manual math and ensuring consistency across your entire generation pipeline.

### 🚀 Optimized for Performance

WanVideo requires specific dimensional "buckets" to generate high-quality motion without artifacts. This node provides these native presets out of the box, categorized by complexity (🟩 Standard, 🟨 HQ, 🟥 Extended).

### 🧠 Smart Frame & FPS Math

Stop calculating frame counts manually. This node handles the logic for you:

- **Auto-Length:** Enter the desired duration in seconds, and the node automatically calculates the exact length (total frames) using the formula: (Duration × Base FPS) + 1.
- **Interpolation Ready (RIFE):** Includes built-in logic for frame interpolation. Set your fps_base for generation and your rife_multiply for smoothness; the node outputs the final fps for the video encoder.

| Feature | Description |
| :--- | :--- |
| **Native Presets** | Instant access to 1:1, 16:9, 4:3, and 9:16 resolutions optimized for WanVideo training. |
| **RIFE Sync** | Calculates the final playback speed (e.g., 12 fps base × 2 RIFE = 24 fps final) automatically. |
| **VRAM Management** | Categorized presets (Light to Full) help you choose the best resolution for your hardware (RTX 3060/4090). |
| **Clean Output** | Provides both INT and FLOAT values ready to be plugged into Sampling, Latent, and Video Combine nodes. |

### 📥 Inputs & Outputs

- **Inputs:**
  - video_size: Choose from optimized WanVideo presets.
  - duration_sec: Desired video length in seconds.
  - fps_base: The actual frames per second the AI will generate.
  - rife_multiply: The multiplier for fluid motion interpolation (1 = Disabled).
- **Outputs:**
  - width / height: Precise pixel values for latent nodes.
  - length: The total frame count for the Sampler.
  - fps: The final calculated frame rate for the video output.

> [!TIP]
> To keep your generation fast on mid-range GPUs (like the RTX 3060 12GB), use a fps_base of 12 or 16 and a rife_multiply of 2. This gives you a smooth 24/32 fps result without the heavy VRAM cost of generating every frame natively.

[↑ Top](#the-essential-suite)

---
---

<a name="zn-smart-flusher"></a>
## 🧹 ⧉ ZN Smart Flusher

**ZN Smart Flusher** is an intelligent cache management node that optimizes how ComfyUI handles model memory. Instead of blindly clearing caches every execution, it detects **real conditioning changes** and performs a cleanup only when required, keeping models resident in memory whenever possible to maximize performance.

| Feature | Description |
| :--- | :--- |
| **Smart Conditioning Detection** | Generates a lightweight fingerprint of the conditioning to detect real prompt changes without relying on the raw prompt text. |
| **Selective Cache Flush** | Clears the model cache only when necessary, avoiding unnecessary model reloads between identical executions. |
| **Force Flush Mode** | Optionally performs a complete cache cleanup on every execution when deterministic behavior is preferred. |
| **VRAM Safety Guard** | Can automatically trigger a cleanup when available GPU memory falls below a configurable threshold. |
| **Node Cache Cleanup** | Optionally clears ComfyUI's execution cache together with the model cache, replicating the "Free model and node cache" behavior. |
| **Transparent Pass-Through** | Forwards data and conditioning unchanged, allowing seamless integration into virtually any workflow. |

### 🧠 Smart Cache Logic

Traditional cache managers either **always flush** or **never flush**. Both approaches have drawbacks: unnecessary model reloads reduce performance, while never clearing the cache may cause memory issues in long-running workflows.

**ZN Smart Flusher** continuously compares the current conditioning against the previous execution. Only when a genuine change is detected (or a manual/VRAM-triggered cleanup is requested) are the caches released, otherwise the loaded models remain available for immediate reuse.

### 🚀 Why it matters

This behavior makes the node useful in many different scenarios:

- **Complex ComfyUI workflows** where unnecessary model reloads waste execution time.
- **Long-running automation pipelines** that require controlled cache management.
- **Memory-sensitive workflows** where VRAM usage must be monitored dynamically.
- **Multi-model pipelines** where cache cleanup should happen only when actually required.
- **Recent ComfyUI versions**, where it restores the expected performance of **Z-Image Nunchaku** by preventing unnecessary cache flushes when prompt change detection is enabled.

### ⚙️ Flexible Cleanup Modes

The node supports multiple cleanup strategies depending on your workflow:

- **Smart Mode:** Flush only when conditioning changes.
- **Force Flush:** Always perform a complete cleanup.
- **VRAM Guard:** Trigger cleanup automatically when free VRAM becomes critically low.
- **Aggressive Mode:** Optionally invoke `torch.cuda.empty_cache()` after the standard cleanup for maximum memory recovery.

- ### 📥 Inputs & Outputs

- **Inputs:**
  - **force_flush:** Forces a complete cache cleanup on every execution, bypassing the smart detection logic.
  - **use_vram_guard:** Enables automatic cleanup when available VRAM falls below the configured threshold.
  - **vram_threshold_gb:** Minimum free VRAM (in GB) before the VRAM Guard triggers a cleanup.
  - **clear_node_cache:** Also clears ComfyUI's node execution cache together with the model cache.
  - **aggressive:** Executes `torch.cuda.empty_cache()` after the standard cleanup for maximum VRAM recovery.
  - **data:** *(Optional)* Accepts any data type and passes it through unchanged.
  - **positive_conditioning:** *(Optional)* Primary conditioning used for smart change detection and forwarded to the conditioning output.
  - **negative_conditioning:** *(Optional)* Secondary conditioning used for change detection.

- **Outputs:**
  - **data:** The original input data, passed through unchanged.
  - **conditioning:** Outputs the **positive conditioning** when connected; otherwise, it automatically falls back to the **negative conditioning**.
  - **status:** A human-readable debug string describing why the cache was (or wasn't) flushed, including Smart Mode decisions, VRAM checks, and cleanup operations.

> [!TIP]
> **ZN Smart Flusher** is not limited to solving the recent Z-Image Nunchaku slowdown. It is designed as a general-purpose intelligent cache manager for ComfyUI, making it especially valuable in advanced workflows where balancing execution speed and memory management is essential.

[↑ Top](#the-essential-suite)

---
---

<a name="zn-imagemask-bridge"></a>
## 🖌️ ⧉ ZN ImageMask Bridge

**ZN ImageMask Bridge** is a multi-purpose routing bridge that transmits images while providing an integrated Mask Editor to create and output masks.

This node acts as a central **Intermediary Hub** for image and mask data management. It is designed to simplify the workflow by receiving a single image input and acting as a distribution point for multiple downstream nodes, reducing "noodle" clutter in ComfyUI.

| Feature | Description |
| :--- | :--- |
| **Image Passthrough** | Receives a tensor image and re-transmits it without data loss. |
| **Integrated Mask Editor** | Allows users to manually define specific areas of interest directly on the input image via the native Mask Editor. |
| **Dual Output Stream** | Provides simultaneous outputs for both IMAGE and MASK, essential for Inpainting, Regional Prompts, or Targeted Upscaling. |
| **Workflow Efficiency** | Minimizes VRAM usage by referencing the same tensor across multiple outputs. |

### 🛠️ Technical Highlights

- **Single Input Hub:** One image in, many routes out—keeps graphs clean and readable.
- **Mask-Centric Workflows:** Perfect for inpainting, region-based effects, and targeted corrections.
- **Native Editor Integration:** Leverages ComfyUI’s built-in Mask Editor for a seamless UX.

> [!TIP]
> Use ZN ImageMask Bridge as the central “router” for any workflow that needs to reuse the same base image across multiple masked operations.

[↑ Top](#the-essential-suite)

---
---
<a name="zn-image-preview-save-adv"></a>
## 🖼️ ⧉ ZN Image Preview & Save ADV

**ZN Image Preview & Save ADV** is an advanced image viewer that supports both **dual-image comparison** and **single-image preview**, with integrated save options directly from the UI. It is ideal for upscaling, A/B testing, or any workflow where organized exporting and visual inspection are essential.

| Feature | Description |
| :--- | :--- |
| **Dual-Image Comparison** | Side-by-side visualization with a smooth vertical slider (A-Left, B-Right) for pixel-perfect analysis. |
| **Single-Image Preview** | Clean, unobstructed preview mode when only one image is connected, with dedicated save controls. |
| **Dynamic Smart Naming** | Uses input slot labels to generate file names, sanitizing them (spaces → underscores, UPPERCASE). |
| **Context-Aware UI** | Save buttons appear only when relevant slots are connected; visual feedback on successful save. |
| **Native Context Menu** | Right-click any loaded image to **Open**, **Save**, or **Copy** to clipboard — identical to ComfyUI's built-in image nodes. |
| **Integrated Export** | Saves high-quality PNGs into a dedicated subfolder (default: `zn_images`) with timestamp-based filenames. |

### Preview & Save ADV

An interactive visualization tool designed for precise A/B testing and quality control directly within the ComfyUI canvas.

**Key Features:**
* **Interactive Side-by-Side Comparison:** Implements a smooth vertical slider (A-Left, B-Right) to analyze pixel-perfect differences between two images.
* **Dynamic Smart Naming:**
  - The node uses the input slot labels (e.g., `Denoised`, `Raw_Latent`) to name the saved files.
  - Automatic sanitization: spaces are replaced with underscores and text is converted to UPPERCASE for consistent file management.
* **Context-Aware UI:**
  - Save buttons (`Save IMAGE_A`, `Save IMAGE_B`) are dynamically generated.
  - Buttons automatically hide when a slot is disconnected to keep the interface clean.
  - Visual feedback: button colors change from Blue (Ready) to Green (Saved) upon success.
* **Intelligent Watermarking:**
  - Overlays uppercase labels on images during comparison mode.
  - Automatically disables watermarks and sliders when viewing a single image for an unobstructed preview.
* **Integrated Export:** Saves high-quality PNGs to a custom subfolder (default: `zn_images`) within the ComfyUI output directory, appending a unique timestamp to prevent overwriting.

> [!TIP]
> Use ZN Image Preview & Save ADV at the end of your workflow to visually validate results and export only the variants that matter, with clean and traceable filenames.

[↑ Top](#the-essential-suite)

---
---
<a name="zn-seedvr2-smart-controller"></a>
## 🧩 ⧉ ZN SeedVR2 Smart Controller

**ZN SeedVR2 Smart Controller** is a SeedVR2 VAE tiling controller with VRAM-aware tiling. It computes the target resolution from the input image and does **not** perform upscaling.

| Feature | Description |
| :--- | :--- |
| **No Upscaling** | Does not change the scale of the image; only computes the optimal target resolution. |
| **Full-Frame Processing** | Forces SeedVR2 to operate on the full frame for maximum quality. |
| **VRAM-Aware Tiling** | Dynamically adjusts VAE tiles based on available VRAM to avoid OOM errors. |
| **SeedVR2-Specific Logic** | Tailored exclusively for SeedVR2 pipelines and assumptions. |

### SeedVR2 Smart Controller (Full-Frame Quality Mode + VRAM Aware)

This node DOES NOT perform upscaling.  
It computes the target resolution (short side) for SeedVR2, and dynamically adjusts VAE tiling based on available VRAM.  
Specific only for SeedVR2.

### 🛠️ Technical Highlights

- **Automatic Short-Side Target:** Reads the input image and derives the correct short-side resolution for SeedVR2.
- **Safe Tiling Strategy:** Balances tile size and VRAM usage to maintain stability on different GPUs.
- **Consistent Quality:** Ensures full-frame coverage so that SeedVR2 can operate at its intended quality level.

> [!TIP]
> Use ZN SeedVR2 Smart Controller whenever you build a SeedVR2 pipeline and want consistent full-frame quality without manually tuning VAE tiling per resolution or GPU.

[↑ Top](#the-essential-suite)
