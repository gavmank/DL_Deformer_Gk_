# ML Deformer - Installation Guide

## Quick Install (Recommended)

### Step 1: Run the Installation Script

Navigate to this directory and run:

**Windows:**
```bash
python install_to_maya.py
```

**Mac/Linux:**
```bash
python3 install_to_maya.py
```

### Step 2: Follow the Prompts

The script will:
1. Auto-detect your Maya installations
2. Let you choose which Maya version to install to
3. Automatically reorganize and copy all files
4. Create the proper module structure

### Step 3: Restart Maya

After installation completes, restart Maya to use the tools.

---

## What the Installer Does

The installation script automatically:

- ✅ Detects all Maya versions on your system
- ✅ Creates the proper `mldeformer` package structure
- ✅ Reorganizes files (moves UI files to `mldeformer/ui/`)
- ✅ Copies all modules (`generator/`, `pose_extraction/`, `pose_remixer/`)
- ✅ Creates required files (`optional_numpy.py`, `__init__.py`)
- ✅ Backs up existing installations (asks before overwriting)

**Final structure:**
```
maya/scripts/mldeformer/
├── __init__.py
├── Qt.py
├── optional_numpy.py
├── ui/
│   ├── __init__.py
│   ├── config.py
│   ├── parameter.py
│   ├── mesh_mapping.py
│   ├── event_handler.py
│   ├── ... (other UI files)
│   └── qtgui/
│       └── (all GUI windows and widgets)
├── generator/
├── pose_extraction/
└── pose_remixer/
```

---

## Manual Installation

If you prefer to install manually:

### 1. Locate Maya Scripts Folder

**Windows:** `C:\Users\<YourUsername>\Documents\maya\<version>\scripts\`
**Mac:** `~/Library/Preferences/Autodesk/maya/<version>/scripts/`
**Linux:** `~/maya/<version>/scripts/`

### 2. Create Directory Structure

Create `mldeformer` folder in the scripts directory.

### 3. Copy Files

Follow the structure shown above, or refer to `install_to_maya.py` for the exact file mapping.

---

## Using ML Deformer in Maya

After installation, you can use the tools in Maya:

### Import the Package
```python
import mldeformer
```

### Launch Main Window
```python
from mldeformer.ui.qtgui.main_window import DeformerMainWindow
window = DeformerMainWindow()
window.show()
```

### Launch Pose Extraction
```python
from mldeformer.ui.qtgui.pose_extraction_window import PoseExtractionWindow
window = PoseExtractionWindow()
window.show()
```

### Launch Pose Remixer
```python
from mldeformer.ui.qtgui.pose_remixer_window import PoseRemixerWindow
window = PoseRemixerWindow()
window.show()
```

### Use Pose Extraction Directly (with interpolation)
```python
from mldeformer.pose_extraction.maya import greedy_pose_extraction

greedy_pose_extraction.extract_poses(
    fbx_input_folder='/path/to/fbx/files',
    joints_to_include_in_search=['joint1', 'joint2', ...],
    num_output_poses=100,
    max_frames_per_fbx=10000000,
    num_interpolated_frames=5  # Add 5 transition frames between poses
)
```

---

## Troubleshooting

### "No module named mldeformer"
- Ensure the installation completed successfully
- Restart Maya
- Check that `mldeformer` folder exists in Maya's scripts directory

### Import Errors for Qt
- Install PySide2: `pip install PySide2`
- Maya 2017+ should have PySide2 built-in

### "numpy not supported" Warning
- Install NumPy for faster pose extraction: `pip install numpy`
- The tool will still work without NumPy, just slower

---

## New Feature: Frame Interpolation

The modified version includes frame interpolation support in pose extraction:

**What it does:** Adds smooth transition frames between the selected diverse poses

**How to use:**
```python
num_interpolated_frames=5  # Adds 5 frames between each selected pose
```

**Example:**
- 10 selected poses + 5 interpolated frames = 55 total frames
- Creates smoother animations from the greedy pose selection

---

## Uninstallation

To remove ML Deformer:

1. Navigate to Maya's scripts folder
2. Delete the `mldeformer` directory

Or run:
```bash
rm -rf ~/maya/<version>/scripts/mldeformer  # Mac/Linux
```

---

## Support

For issues or questions:
- Check the original Epic Games ML Deformer documentation
- Review the code in `pose_extraction/maya/greedy_pose_extraction.py`
- Check import paths if you encounter module errors

---

**Copyright:** Epic Games, Inc. All Rights Reserved
**Modified by:** gavmank (frame interpolation feature)
