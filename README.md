# 🌱 PCB Carbon Footprint Tool

A **KiCad plugin** to estimate the carbon footprint (kg CO₂e) of a PCB based on its surface area and number of copper layers.  
The modern and interactive interface provides a comparative analysis across multiple scenarios.

---

## Features

- Automatically calculates the **current carbon footprint** of the open PCB.
- Displays an **interactive comparison grid**:
  - Surface area variation ±20%  
  - Supported copper layers: `1, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20`
- Color-coded highlights:
  - 🟡 Reference PCB (current design)  
  - 🟢 Lower impact scenarios  
  - 🔴 Higher impact scenarios  
- Detailed information panel when selecting a cell (surface, layers, impact difference).  
- Export results as **CSV**.  
- About dialog with academic reference (PCBnCO article).  

---

## Installation

1. Locate KiCad’s user plugin directory:  
   - **Linux**: `~/.local/share/kicad/scripting/plugins/`  
   - **Windows**: `%APPDATA%\kicad\scripting\plugins\`  
   - **macOS**: `~/Library/Preferences/kicad/scripting/plugins/`  

2. Copy the Python file (e.g. `carbon_impact_plugin.py`) into this folder.

3. Restart KiCad (PCB Editor).  
   The plugin will appear in the menu:  
   `Tools → External Plugins → version 14`  

---

## Usage

1. Open a **PCB in KiCad PCB Editor** (version 6 or newer).  
2. Run the plugin:  
   - From the **Tools menu** → `version 14`  
   - Or from the **toolbar button** (if enabled).  
3. A new window will display:
   - Key PCB information (surface area, layers, current impact).  
   - An interactive comparison grid across different scenarios.  
   - A detail panel showing the selected case.  
4. You can:  
   - Export the results to **CSV**  
   - Open the **About** dialog for credits and source  
   - Close the analysis window  

---

## Calculation Method

The carbon footprint is estimated based on PCB surface area and copper layers, using the formula derived from the [PCBnCO](https://hal.science/hal-05054490v1/document) publication:

\[
Impact = (7.81 \times \text{layers} + 57.97) \times \text{surface (m²)}
\]

- Surface is converted from cm² to m².  
- Supported number of layers ranges from 1 to 20.  

---

## Dependencies

The plugin only requires:
- **KiCad API** (`pcbnew`)  
- **wxPython** (bundled with KiCad)  
- Python standard library (`csv`)  

No additional installation is needed.

---

## Credits

- Developed by **Alyzée Corre**  
- Supervised by **Pierre Le Gargasson**  
- Institution: **INSA Rennes, France**  

Scientific reference:  
*"PCBnCO: Life Cycle Assessment of Printed Circuit Boards"*  
[Read full article](https://hal.science/hal-05054490v1/document)

---

## License

This project is provided for educational and academic purposes.  
(Consider adding an open-source license such as MIT or GPL if publishing publicly.)  
