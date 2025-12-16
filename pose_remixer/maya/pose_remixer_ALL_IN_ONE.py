# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved
# Enhanced with Blending and Integrated UI by Gav Knowlton

"""
Pose Remixer with Blend Controls - All-in-One Version
======================================================

This script contains both the pose remixing logic and the Maya UI in a single file.

USAGE:
    1. Copy this entire script to Maya Script Editor (Python tab)
    2. Run it!
    
    OR save as a shelf button:
    1. Select all this code in Script Editor
    2. Middle-mouse drag to shelf
    3. Click the shelf button anytime to launch UI

QUICK LAUNCH:
    import pose_remixer
    pose_remixer.show_ui()
"""

import maya.cmds as cmds
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as omanim
import math
import json
import os

# Optional numpy import
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("Warning: NumPy not available. Pose remixing will not work without it.")


# ============================================================================
# POSE REMIXER CORE FUNCTIONS
# ============================================================================

def om_set_keyframes(ctrl_name: str, attr_name: str, key_times: list, key_values: list) -> None:
    """"Set key frames at once using the open maya api
    Parameters:
        ctrl_name   -- Control Name
        attr_name   -- Attribute Name
        key_times   -- The keyframe time values.
        key_values  -- The keyframe values.
    """
    omslist = om.MSelectionList()
    omslist.add("{0}.{1}".format(ctrl_name, attr_name))
    mplug = omslist.getPlug(0)
    mcurve = omanim.MFnAnimCurve(mplug)
    try:
        mcurve.name()  # Errors if the curve does not exist.
    except:
        mcurve.create(mplug)  # If the curve does not exist, create it and attach it to the plug.

    angular_types = [omanim.MFnAnimCurve.kAnimCurveTA, omanim.MFnAnimCurve.kAnimCurveUA]
    if mcurve.animCurveType in angular_types:
        key_values = [math.radians(i) for i in key_values]

    mcurve.addKeys(
        key_times,
        key_values,
        omanim.MFnAnimCurve.kTangentStep,
        omanim.MFnAnimCurve.kTangentStep,
        True)


def has_keyframe_on_every_frame(joint_name: str, start_frame: int, end_frame: int) -> bool:
    """Check if joint has keyframes on every frame in range"""
    for attribute in ['rotateX', 'rotateY', 'rotateZ']:
        keyframes = cmds.keyframe(joint_name, t=(start_frame, end_frame), q=True, at=attribute)
        
        # Check if keyframes is None (no animation on this attribute)
        if keyframes is None:
            print(f'Joint attribute {joint_name}.{attribute} has no keyframes')
            return False

        # Create a set of all frames within the range.
        all_frames = set(range(start_frame, end_frame + 1))
        keyframed_frames = set(keyframes)

        # Check if all frames have keyframes.
        if not all_frames.issubset(keyframed_frames):
            print(f'Joint attribute {joint_name}.{attribute} does not have keys for every frame')
            return False

    return True


def keyframe_every_frame(joint_name: str, start_frame: int, end_frame: int) -> None:
    """Add keyframes on every frame where they're missing"""
    for attribute in ['rotateX', 'rotateY', 'rotateZ']:
        fixed_frames = False

        # Get the existing keyframes.
        existing_keyframes = cmds.keyframe(joint_name, q=True, tc=True, at=attribute)
        if existing_keyframes is None:
            existing_keyframes = []

        # Now check every frame, and add a keyframe where needed.
        for frame in range(start_frame, end_frame + 1):
            if frame not in existing_keyframes:
                # Get the (interpolated) key value for this frame, and set it.
                rot = cmds.keyframe(joint_name, query=True, eval=True, attribute=attribute, time=(frame,))
                if rot:
                    cmds.setKeyframe(joint_name, t=frame, at=attribute, v=rot[0])
                    fixed_frames = True

        if fixed_frames:
            print(f'Keyframes added on some missing frames for {joint_name}.{attribute}')


def interpolate_frames(start_values, end_values, num_blend_frames: int):
    """
    Interpolate between two sets of rotation values over a specified number of frames.
    
    Parameters:
        start_values    -- Starting rotation values (array of shape [num_axes])
        end_values      -- Ending rotation values (array of shape [num_axes])
        num_blend_frames -- Number of frames to blend over (not including start/end)
    
    Returns:
        Array of interpolated values with shape [num_axes, num_blend_frames]
    """
    if not NUMPY_AVAILABLE:
        return None
        
    # Create array to hold interpolated values
    interpolated = np.zeros((len(start_values), num_blend_frames))
    
    # For each axis (RX, RY, RZ for each joint)
    for axis_idx in range(len(start_values)):
        # Create linear interpolation between start and end
        interpolated[axis_idx] = np.linspace(start_values[axis_idx], end_values[axis_idx], num_blend_frames + 2)[1:-1]
    
    return interpolated


def remix_poses(joint_groups: list, blend_frames: int = 0) -> None:
    """
    Remix poses by shuffling animation frames and optionally blending between them.
    
    Parameters:
        joint_groups    -- List of joint groups to process
        blend_frames    -- Number of frames to blend between shuffled poses (0 = no blending)
    """
    if not NUMPY_AVAILABLE:
        cmds.error("NumPy is required for pose remixing. Please install NumPy.")
        return
        
    print('Remixing poses...')
    
    if blend_frames > 0:
        print(f'Blending enabled: {blend_frames} frames between each pose transition')

    # Find the list of all joints.
    all_joints = set()
    for joint_list in joint_groups:
        all_joints = all_joints.union(set(joint_list))

    # Find the joint with the lowest last keyframe time, and use that as animation duration. 
    start_frame = 9999999999
    end_frame = -9999999999
    for joint_name in all_joints:
        try:
            joint_last_keyframe = cmds.findKeyframe([joint_name], which='last')
            joint_first_keyframe = cmds.findKeyframe([joint_name], which='first')
            end_frame = max(end_frame, joint_last_keyframe)
            start_frame = min(start_frame, joint_first_keyframe)
        except:
            print(f"Warning: Could not find keyframes for {joint_name}")
            
    if start_frame == 9999999999 or end_frame == -9999999999:
        cmds.error("Could not find valid keyframe range. Make sure your joints are animated.")
        return
        
    start_frame = int(start_frame)
    end_frame = int(end_frame)

    # Make sure each joint has a keyframe on every frame.
    for joint_name in all_joints:
        if not has_keyframe_on_every_frame(joint_name, start_frame, end_frame):
            keyframe_every_frame(joint_name, start_frame, end_frame)
        if not has_keyframe_on_every_frame(joint_name, start_frame, end_frame):
            print(f'Warning: Keyframes not fully fixed for {joint_name}!')

    num_time_values = end_frame - start_frame + 1
    print(f'Animation start frame: {start_frame}')
    print(f'Animation end frame: {end_frame}')

    all_joint_rotations_array = None
    for joint_list in joint_groups:
        for joint_index, joint_name in enumerate(joint_list):
            # Pack the joint rotation keyframes into an array
            joint_rotations = cmds.keyframe(joint_name, t=(start_frame, end_frame), q=1, at='rotate', vc=1)
            if not joint_rotations:
                print(f"Warning: No rotation data for {joint_name}")
                continue
                
            joint_rotations_array = np.array(joint_rotations, dtype=float)

            # Reshape the array so each row is a rotation axis, and each column is a time index.
            joint_rotations_per_axis = joint_rotations_array.reshape(3, num_time_values)

            # Concatenate this joint's rotation values
            if joint_index == 0:
                all_joint_rotations_array = np.copy(joint_rotations_per_axis)
            else:
                all_joint_rotations_array = np.concatenate((all_joint_rotations_array, joint_rotations_per_axis), axis=0)

        # Shuffle the transposed array
        np.random.shuffle(np.transpose(all_joint_rotations_array))

        # Add blending between shuffled frames if requested
        if blend_frames > 0:
            blended_array = []
            num_shuffled_frames = all_joint_rotations_array.shape[1]
            
            for frame_idx in range(num_shuffled_frames):
                # Add the current frame
                blended_array.append(all_joint_rotations_array[:, frame_idx])
                
                # Add blend frames between this frame and the next (except for the last frame)
                if frame_idx < num_shuffled_frames - 1:
                    start_values = all_joint_rotations_array[:, frame_idx]
                    end_values = all_joint_rotations_array[:, frame_idx + 1]
                    
                    # Generate interpolated frames
                    interpolated = interpolate_frames(start_values, end_values, blend_frames)
                    
                    # Add each interpolated frame
                    for blend_idx in range(blend_frames):
                        blended_array.append(interpolated[:, blend_idx])
            
            # Convert list of frames back to array
            all_joint_rotations_array = np.column_stack(blended_array)
            
            # Update the number of frames
            num_output_frames = all_joint_rotations_array.shape[1]
            print(f'Created {num_output_frames} frames with blending (from {num_time_values} original frames)')
        else:
            num_output_frames = num_time_values

        # Split the all_rotations array
        per_joint_rotations_array = np.split(all_joint_rotations_array, len(joint_list))

        # Build the time array based on the output frame count
        attr_times = om.MTimeArray()
        for frame_index in range(num_output_frames):
            attr_times.append(om.MTime(start_frame + frame_index, om.MTime.uiUnit()))

        for joint_index, joint_name in enumerate(joint_list):
            for row, attribute in enumerate(['rx', 'ry', 'rz']):
                try:
                    # Delete existing keyframes.
                    cmds.delete(cmds.connectionInfo('{0}.{1}'.format(joint_name, attribute), sfd=1).split('.')[0])
                except:
                    pass

                # Set the new keyframes.
                om_set_keyframes(joint_name, attribute, attr_times, per_joint_rotations_array[joint_index][row, :].tolist())
        
        print(f'Remixing complete for joint group!')


# ============================================================================
# MAYA UI
# ============================================================================

class PoseRemixerUI:
    """Maya UI for Pose Remixer with Blend Controls"""
    
    def __init__(self):
        self.window_name = "poseRemixerBlendUI"
        self.window_title = "Pose Remixer - Enhanced"
        self.config_file = ""
        self.joint_groups = []
        
    def create(self):
        """Create the UI window"""
        # Delete existing window if it exists
        if cmds.window(self.window_name, exists=True):
            cmds.deleteUI(self.window_name)
        
        # Create new window
        self.window = cmds.window(
            self.window_name,
            title=self.window_title,
            widthHeight=(450, 350),
            sizeable=True
        )
        
        # Main layout
        main_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=10, columnAttach=('both', 10))
        
        # Title
        cmds.separator(height=10, style='none')
        cmds.text(label="Pose Remixer with Blending", font="boldLabelFont", align='center')
        cmds.separator(height=10, style='in')
        
        # Config File Section
        cmds.frameLayout(label="Configuration", collapsable=True, collapse=False, borderStyle='etchedIn')
        cmds.columnLayout(adjustableColumn=True, rowSpacing=5, columnAttach=('both', 5))
        
        cmds.rowLayout(numberOfColumns=3, adjustableColumn=2, columnAttach=[(1, 'both', 5), (2, 'both', 5), (3, 'both', 5)])
        cmds.text(label="Config File:", width=80)
        self.config_path_field = cmds.textField(text="No file loaded", editable=False)
        cmds.button(label="Browse...", command=self.browse_config, width=80)
        cmds.setParent('..')
        
        self.config_status = cmds.text(label="Status: No config loaded", align='left', font='smallPlainLabelFont')
        
        cmds.setParent('..')
        cmds.setParent('..')
        
        # Blend Settings Section
        cmds.frameLayout(label="Blend Settings", collapsable=True, collapse=False, borderStyle='etchedIn')
        cmds.columnLayout(adjustableColumn=True, rowSpacing=8, columnAttach=('both', 5))
        
        # Blend Frames Slider
        cmds.rowLayout(numberOfColumns=2, adjustableColumn=2, columnAttach=[(1, 'both', 5), (2, 'both', 5)])
        cmds.text(label="Blend Frames:", width=120, align='left')
        cmds.setParent('..')
        
        cmds.rowLayout(numberOfColumns=2, adjustableColumn=1, columnAttach=[(1, 'both', 5), (2, 'both', 5)])
        self.blend_slider = cmds.intSlider(
            min=0, max=30, value=5, step=1,
            dragCommand=self.update_blend_value
        )
        self.blend_value_text = cmds.text(label="5", width=30, align='center')
        cmds.setParent('..')
        
        cmds.separator(height=5, style='none')
        
        # Preset buttons
        cmds.text(label="Quick Presets:", align='left', font='smallBoldLabelFont')
        cmds.rowLayout(numberOfColumns=5, columnAttach=[(1, 'both', 2), (2, 'both', 2), (3, 'both', 2), (4, 'both', 2), (5, 'both', 2)])
        cmds.button(label="No Blend (0)", command=lambda x: self.set_blend_preset(0), backgroundColor=(0.4, 0.4, 0.4))
        cmds.button(label="Quick (3)", command=lambda x: self.set_blend_preset(3), backgroundColor=(0.5, 0.6, 0.5))
        cmds.button(label="Smooth (5)", command=lambda x: self.set_blend_preset(5), backgroundColor=(0.5, 0.7, 0.5))
        cmds.button(label="Very Smooth (10)", command=lambda x: self.set_blend_preset(10), backgroundColor=(0.5, 0.8, 0.5))
        cmds.button(label="Dreamy (20)", command=lambda x: self.set_blend_preset(20), backgroundColor=(0.6, 0.7, 0.9))
        cmds.setParent('..')
        
        cmds.separator(height=5, style='none')
        
        # Info text
        self.info_text = cmds.text(
            label="Blend frames: 5 | Example: 100 frames → 595 output frames",
            align='center',
            font='smallPlainLabelFont',
            backgroundColor=(0.2, 0.2, 0.25)
        )
        
        cmds.setParent('..')
        cmds.setParent('..')
        
        # Info Section
        cmds.frameLayout(label="Information", collapsable=True, collapse=True, borderStyle='etchedIn')
        cmds.columnLayout(adjustableColumn=True, rowSpacing=3, columnAttach=('both', 5))
        
        cmds.text(label="• Blend Frames: Number of frames to interpolate between poses", align='left', font='smallPlainLabelFont')
        cmds.text(label="• 0 = Hard snaps (original behavior)", align='left', font='smallPlainLabelFont')
        cmds.text(label="• 5-10 = Smooth, natural transitions (recommended)", align='left', font='smallPlainLabelFont')
        cmds.text(label="• 15+ = Very smooth, slow transitions", align='left', font='smallPlainLabelFont')
        
        cmds.setParent('..')
        cmds.setParent('..')
        
        # Execute Button
        cmds.separator(height=10, style='none')
        cmds.button(
            label="Generate Remixed Animation",
            command=self.execute_remix,
            height=40,
            backgroundColor=(0.3, 0.5, 0.3)
        )
        
        # Progress/Status
        cmds.separator(height=5, style='none')
        self.status_text = cmds.text(label="Ready", align='center', font='boldLabelFont')
        
        cmds.separator(height=10, style='none')
        
        # Show window
        cmds.showWindow(self.window)
        
    def browse_config(self, *args):
        """Browse for config file"""
        file_path = cmds.fileDialog2(
            caption="Select Pose Remixer Config",
            fileFilter="Pose Remixer Config (*.poseRemixerConfig);;All Files (*.*)",
            fileMode=1
        )
        
        if file_path:
            self.config_file = file_path[0]
            self.load_config()
            
    def load_config(self):
        """Load and parse the config file"""
        try:
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)
            
            # Extract joint groups
            self.joint_groups = []
            group_list = config_data.get('group_list', [])
            
            for group in group_list:
                if group.get('is_enabled', True):
                    self.joint_groups.append(group.get('joint_list', []))
            
            # Update UI
            file_name = os.path.basename(self.config_file)
            cmds.textField(self.config_path_field, edit=True, text=file_name)
            
            total_joints = sum(len(group) for group in self.joint_groups)
            status_msg = f"Loaded: {len(self.joint_groups)} groups, {total_joints} joints"
            cmds.text(self.config_status, edit=True, label=status_msg)
            cmds.text(self.status_text, edit=True, label="Config loaded - Ready to remix!")
            
            print(f"Loaded config: {len(self.joint_groups)} groups")
            
        except Exception as e:
            cmds.text(self.config_status, edit=True, label=f"Error: {str(e)}")
            cmds.text(self.status_text, edit=True, label="Error loading config")
            cmds.warning(f"Failed to load config: {str(e)}")
            
    def update_blend_value(self, value):
        """Update the blend value display"""
        blend_frames = int(value)
        cmds.text(self.blend_value_text, edit=True, label=str(blend_frames))
        
        # Update info text with frame count estimate
        example_frames = 100
        output_frames = example_frames + (example_frames - 1) * blend_frames
        info_msg = f"Blend frames: {blend_frames} | Example: 100 frames → {output_frames} output frames"
        cmds.text(self.info_text, edit=True, label=info_msg)
        
    def set_blend_preset(self, value):
        """Set blend slider to preset value"""
        cmds.intSlider(self.blend_slider, edit=True, value=value)
        self.update_blend_value(value)
        
    def execute_remix(self, *args):
        """Execute the pose remixing with blend settings"""
        if not self.joint_groups:
            cmds.warning("Please load a config file first!")
            cmds.text(self.status_text, edit=True, label="Error: No config loaded")
            return
        
        if not NUMPY_AVAILABLE:
            cmds.warning("NumPy is required for pose remixing!")
            cmds.text(self.status_text, edit=True, label="Error: NumPy not available")
            return
        
        # Get blend frames value
        blend_frames = cmds.intSlider(self.blend_slider, query=True, value=True)
        
        # Update status
        cmds.text(self.status_text, edit=True, label=f"Processing with {blend_frames} blend frames...")
        cmds.refresh()
        
        try:
            # Execute the remixing
            print(f"\n{'='*60}")
            print(f"Executing Pose Remix with {blend_frames} blend frames")
            print(f"{'='*60}\n")
            
            remix_poses(
                joint_groups=self.joint_groups,
                blend_frames=blend_frames
            )
            
            cmds.text(self.status_text, edit=True, label="✓ Remix Complete!")
            cmds.inViewMessage(
                assistMessage=f'Pose remixing complete with {blend_frames} blend frames!',
                position='topCenter',
                fade=True,
                fadeStayTime=2000
            )
            
        except Exception as e:
            error_msg = str(e)
            cmds.text(self.status_text, edit=True, label="Error during remix")
            cmds.warning(f"Remix failed: {error_msg}")
            
            # Show detailed error in script editor
            import traceback
            print("\nError Details:")
            print(traceback.format_exc())


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def show_ui():
    """
    Show the Pose Remixer UI
    
    Usage:
        import pose_remixer
        pose_remixer.show_ui()
    """
    ui = PoseRemixerUI()
    ui.create()
    return ui


# ============================================================================
# AUTO-LAUNCH (if running as main script)
# ============================================================================

if __name__ == "__main__":
    show_ui()
