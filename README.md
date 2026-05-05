# ZN_ComfyUI_Nodes
A collection of essential, lightweight nodes designed for efficiency and streamlined workflows

## 📜 Disclaimer & Philosophy
**Please read before using:**
* **Not a Coder:** I am not a professional developer. I created these nodes primarily for my personal use to solve specific problems in my own workflows[cite: 1].
* **As-Is:** I'm sharing them because I think they might be useful to others, but I offer **no guarantees, no formal support, and no assistance.** Use them at your own risk[cite: 1].
* **Why these nodes?** I was tired of installing massive node suites just to use a single node. This repository follows a "less is more" philosophy: it contains only the essentials I actually use, keeping the workflow clean and avoiding unnecessary bloat[cite: 1].

## 🛠️ Installation
---

Choose one of the following methods:

### Method 1: Using Git (Recommended)
1. Open a terminal/command prompt[cite: 1].
2. Navigate to your ComfyUI custom nodes folder:
   ```bash
   cd ComfyUI/custom_nodes/
4. Clone the repository:
    ```bash
   git clone [https://github.com/znortr/ComfyUI-Zn-Nodes.git](https://github.com/znortr/ComfyUI-Zn-Nodes.git)
   
5. Restart ComfyUI[cite: 1].

### Method 2: Manual Download (Full Suite)
1. Download this repository as a **ZIP file** from the green **Code** button above[cite: 1].
2. Extract the contents into `ComfyUI/custom_nodes/`[cite: 1].
3. **Crucial:** Ensure the folder is named `ComfyUI-Zn-Nodes` and that the `__init__.py` file is located directly inside it (not in a double subfolder)[cite: 1].
4. Restart ComfyUI[cite: 1].

### Method 3: Selective Manual Installation (Individual Nodes)
If you only want to install specific nodes from this suite:
1. Create a folder named `ComfyUI-Zn-Nodes` in your `custom_nodes/` directory[cite: 1].
2. Download the `__init__.py` and only the specific `.py` files of the nodes you wish to use[cite: 1].
3. **Edit __init__.py:** Open the file and **comment out** (add a `#` at the start of the line) or delete the references to the nodes you did not download to prevent startup errors[cite: 1].
4. Restart ComfyUI[cite: 1].

---

## 💡 Tips:
* **JSON Configs:** The nodes will automatically create/read configuration files in the `presets/` folder. Do not delete this folder![cite: 1]
* **UI Updates:** If you don't see the new UI features (like the resolution buttons), clear your browser cache and refresh the page[cite: 1].
* **Requirements:** These nodes use standard ComfyUI libraries. No additional `pip install` is required[cite: 1].
