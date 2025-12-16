#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ML Deformer Maya Installation Script
Automatically installs the ML Deformer package to Maya's scripts folder.
"""

import os
import sys
import shutil
import platform
from pathlib import Path


def get_maya_scripts_paths():
    """Detect Maya installation paths based on OS."""
    system = platform.system()
    maya_paths = []

    if system == "Windows":
        base = Path.home() / "Documents" / "maya"
    elif system == "Darwin":  # macOS
        base = Path.home() / "Library" / "Preferences" / "Autodesk" / "maya"
    else:  # Linux
        base = Path.home() / "maya"

    # Find all Maya version folders
    if base.exists():
        for item in sorted(base.iterdir(), reverse=True):
            if item.is_dir():
                scripts_dir = item / "scripts"
                if scripts_dir.exists() or item.name.replace('.', '').isdigit():
                    maya_paths.append((item.name, scripts_dir))

    return maya_paths


def create_optional_numpy():
    """Generate the optional_numpy.py content."""
    return '''# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

def numpy_supported():
    """Check if numpy is available."""
    try:
        import numpy
        return True
    except ImportError:
        return False
'''


def create_ui_init():
    """Generate the ui/__init__.py content."""
    return '''# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved
'''


def install_mldeformer(source_dir, maya_scripts_dir):
    """Install mldeformer to the specified Maya scripts directory."""

    source_dir = Path(source_dir)
    maya_scripts_dir = Path(maya_scripts_dir)

    # Create Maya scripts directory if it doesn't exist
    maya_scripts_dir.mkdir(parents=True, exist_ok=True)

    # Target directory
    target_dir = maya_scripts_dir / "mldeformer"

    print(f"\nInstalling to: {target_dir}")

    # Remove existing installation if present
    if target_dir.exists():
        response = input(f"\n{target_dir} already exists. Overwrite? (y/n): ")
        if response.lower() != 'y':
            print("Installation cancelled.")
            return False
        print("Removing existing installation...")
        shutil.rmtree(target_dir)

    # Create base mldeformer directory
    target_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created: {target_dir}")

    # Create ui subdirectory
    ui_dir = target_dir / "ui"
    ui_dir.mkdir(exist_ok=True)
    print(f"Created: {ui_dir}")

    # Copy root __init__.py
    shutil.copy2(source_dir / "__init__.py", target_dir / "__init__.py")
    print(f"Copied: __init__.py")

    # Copy Qt.py
    shutil.copy2(source_dir / "Qt.py", target_dir / "Qt.py")
    print(f"Copied: Qt.py")

    # Create optional_numpy.py
    with open(target_dir / "optional_numpy.py", 'w') as f:
        f.write(create_optional_numpy())
    print(f"Created: optional_numpy.py")

    # Files to move to ui/ subdirectory
    ui_files = [
        "config.py",
        "parameter.py",
        "parameter_filter.py",
        "mesh_mapping.py",
        "attribute_minmax.py",
        "json_encoder.py",
        "recent_file_list.py",
        "global_settings.py",
        "event_handler.py"
    ]

    # Copy files to ui/
    for filename in ui_files:
        src = source_dir / filename
        if src.exists():
            shutil.copy2(src, ui_dir / filename)
            print(f"Copied: {filename} -> ui/{filename}")

    # Create ui/__init__.py
    with open(ui_dir / "__init__.py", 'w') as f:
        f.write(create_ui_init())
    print(f"Created: ui/__init__.py")

    # Copy qtgui folder to ui/qtgui
    src_qtgui = source_dir / "qtgui"
    if src_qtgui.exists():
        dest_qtgui = ui_dir / "qtgui"
        shutil.copytree(src_qtgui, dest_qtgui)
        print(f"Copied: qtgui/ -> ui/qtgui/")

    # Copy entire folders as-is
    folders_to_copy = ["generator", "pose_extraction", "pose_remixer"]

    for folder in folders_to_copy:
        src_folder = source_dir / folder
        if src_folder.exists():
            dest_folder = target_dir / folder
            shutil.copytree(src_folder, dest_folder)
            print(f"Copied: {folder}/")

    # Optionally copy TPS folder
    src_tps = source_dir / "TPS"
    if src_tps.exists():
        dest_tps = target_dir / "TPS"
        shutil.copytree(src_tps, dest_tps)
        print(f"Copied: TPS/ (licenses)")

    print(f"\n✓ Installation complete!")
    print(f"\nmldeformer installed to: {target_dir}")
    return True


def main():
    print("=" * 60)
    print("ML Deformer - Maya Installation Script")
    print("=" * 60)

    # Get current script directory (source)
    script_dir = Path(__file__).parent
    print(f"\nSource directory: {script_dir}")

    # Detect Maya installations
    maya_paths = get_maya_scripts_paths()

    if not maya_paths:
        print("\n⚠ No Maya installations detected!")
        print("\nPlease enter the Maya scripts folder path manually:")
        custom_path = input("Path: ").strip()
        if custom_path:
            maya_paths = [("Custom", Path(custom_path))]
        else:
            print("Installation cancelled.")
            return

    print(f"\nDetected Maya installation(s):")
    for i, (version, path) in enumerate(maya_paths, 1):
        exists = "✓" if path.exists() else "✗"
        print(f"  {i}. Maya {version}: {path} {exists}")

    # Let user choose
    if len(maya_paths) == 1:
        choice = 1
        print(f"\nUsing Maya {maya_paths[0][0]}")
    else:
        choice = input(f"\nSelect Maya version (1-{len(maya_paths)}) or 'all': ").strip().lower()

        if choice == 'all':
            for version, scripts_path in maya_paths:
                print(f"\n--- Installing for Maya {version} ---")
                install_mldeformer(script_dir, scripts_path)
            return
        else:
            try:
                choice = int(choice)
            except ValueError:
                print("Invalid choice.")
                return

    if 1 <= choice <= len(maya_paths):
        version, scripts_path = maya_paths[choice - 1]
        install_mldeformer(script_dir, scripts_path)
    else:
        print("Invalid choice.")


if __name__ == "__main__":
    main()
