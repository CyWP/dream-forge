import bpy
import tempfile
import os
import numpy as np

def auto_uv_map(context) -> str:

    obj = context.active_object
    dat = obj.data
    heph_props = context.scene.hephaestus_props

    vgi = obj.vertex_groups[heph_props.vertex_group].index
    action = heph_props.uv_map
    unwrap = action in "Auto Unwrap"
    project = action in "Smart Island Project"

    if not unwrap and not project:
        raise ValueError(f"Invalid action: {action} seems to be an existing UV map for object {obj.name}.")
    
    # Store the current mode to revert back later
    current_mode = context.object.mode
    current_area = context.area.ui_type   
    # Switch to Object mode if not already in it (required to change mode to Edit)
    if context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')   
    bpy.ops.object.mode_set(mode='EDIT')       
    bpy.ops.mesh.select_mode(type="VERT")
    # Deselect all vertices
    bpy.ops.mesh.select_all(action='DESELECT')
    # Switch to Object mode to access vertex groups data
    bpy.ops.object.mode_set(mode='OBJECT')
    # Select vertices in the vertex group
    for v in obj.data.vertices:
        for g in v.groups:
            if g.group == vgi:
                v.select = True
                
    #Create or load UV map and make active
    uv_name = "auto_unwrap" if unwrap else "auto_project"
    if uv_name in obj.uv_layers:
        uv_map = obj.uv_layers.get(uv_name)
    else:
        uv_map = obj.data.uv_layers.new(name=uv_name)
    obj.data.uv_layers.active = uv_map

    # Switch back to Edit mode, select vertex group's vertices in uv editor, unwrap
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.select_all(action='DESELECT')
    bpy.ops.uv.select_all(action='SELECT')
    if unwrap:
        bpy.ops.uv.unwrap()
    else:
        bpy.ops.uv.smart_project()
    #unwrap all other vertices and scale to 0
    bpy.ops.mesh.select_all(action='INVERT')
    bpy.ops.uv.select_all(action='DESELECT')
    bpy.ops.uv.select_all(action='SELECT')    
    bpy.ops.uv.unwrap()
    bpy.context.area.ui_type = 'UV'
    bpy.ops.transform.resize(value=(0, 0, 0), constraint_axis=(True, True, False))
    bpy.context.area.ui_type = current_area
    # Revert back to the original mode
    bpy.ops.object.mode_set(mode=current_mode)

    return uv_name

def uv_to_img(context, uv_map:str=None) -> str:

    obj = context.active_object
    dat = obj.data
    heph_props = context.scene.hephaestus_props

    if uv_map is None:
        uv_map = heph_props.uv_map
    if uv_map not in obj.data.uv_layers:
        raise ValueError(f"{uv_map} is not a valid UV map name for object {obj.name}.")
    
    #save previous uv to set it back afterwards, set to right one
    prev_uv = obj.data.uv_layers.active
    obj.data.uv_layers.active = obj.data.uv_layers.get(uv_map)

    temp = tempfile.NamedTemporaryFile(suffix=".png")
    filename = temp.name
    bpy.ops.uv.export_layout(filepath=filename, export_all=True, modified=True, opacity=1, check_existing=False)

    #Load and rename exported image
    img = bpy.data.images.load(filename) 
    img.name = f"{obj.name}_{uv_map}_uv"

    #make black and white form for generator
    pixels = np.array(img.pixels[:])
    pixels = pixels.reshape((-1, 4))
    mask = np.where(pixels[:, 3] == 0)[0]
    pixels = np.ones(pixels.shape)
    pixels[mask, :3] = 0
    pixels = pixels.ravel().tolist()
    img.pixels = pixels #saves it to internal img

    #reset active uv and delete temp image file afterwards
    obj.data.uv_layers.active = prev_uv
    os.remove(filename)
    return img.name