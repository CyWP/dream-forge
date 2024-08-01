import bpy
import tempfile
import os
import numpy as np

from ..property_groups.hephaestus import unwrap_options

def auto_uv_map(context) -> str:

    obj = context.active_object
    dat = obj.data
    heph_props = context.scene.hephaestus_props

    vgi = obj.vertex_groups[heph_props.vertex_group].index
    action = heph_props.uv_map
    unwrap = action == unwrap_options[0][0]
    project = action == unwrap_options[1][0]
    if not unwrap and not project:
        return action
        #raise ValueError(f"Invalid action: {action} seems to be an existing UV map for object {obj.name}.")
    
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
    if uv_name in dat.uv_layers:
        uv_map = dat.uv_layers.get(uv_name)
    else:
        uv_map = dat.uv_layers.new(name=uv_name)
    dat.uv_layers.active = uv_map

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

def uv_to_img(context, uv_map:str=None, suffix:str="auto") -> str:

    obj = context.active_object
    dat = obj.data
    heph_props = context.scene.hephaestus_props
    current_mode = context.object.mode

    if uv_map is None:
        uv_map = heph_props.uv_map
    if uv_map not in dat.uv_layers.keys():
        raise ValueError(f"{uv_map} is not a valid UV map name for object {obj.name}.")
    
    #save previous uv to set it back afterwards, set to right one
    prev_uv = dat.uv_layers.active
    dat.uv_layers.active = dat.uv_layers.get(uv_map)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp:
        filename = temp.name
        bpy.ops.uv.export_layout(filepath=filename, export_all=True, modified=True, opacity=1, check_existing=False)

    #Load and rename exported image
    img_name = f"{obj.name}_{uv_map}_uv_{suffix}"
    img = bpy.data.images.get(img_name)
    if img:
        img.filepath = filename
        img.reload()
    else:
        img = bpy.data.images.load(filename) 
        img.name = img_name

    #make black and white form for generator
    pixels = np.array(img.pixels[:])
    pixels = pixels.reshape((-1, 4))
    mask = np.where(pixels[:, 3] == 0)[0]
    pixels = np.ones(pixels.shape)
    pixels[mask, :3] = 0
    pixels = pixels.ravel().tolist()
    img.pixels = pixels #saves it to internal img

    #reset active uv and delete temp image file afterwards
    dat.uv_layers.active = prev_uv
    os.remove(filename)
    bpy.ops.object.mode_set(mode=current_mode)
    return img.name

TILE = "_tiled_"

def scale_uv(context, uv_name:str=None, x:float=None, y:float=None):

    obj = context.active_object
    dat = obj.data
    heph_props = context.scene.hephaestus_props
    current_mode = context.object.mode
    current_area = context.area.ui_type
    current_uv = dat.uv_layers.active
    uv_name = heph_props.uv_map if uv_name is None else uv_name
    scale_x = heph_props.scale_x if x is None else x
    scale_y = heph_props.scale_Y if y is None else y
    new_name = f"{uv_name}{TILE}{scale_x:.2}x{scale_y:.2}"

    if uv_name not in dat.uv_layers:
        raise ValueError(f"{uv_name} not found in UV maps for {obj.name}.")
    
    #copy data to new uv_map
    uv_map = dat.uv_layers[uv_name]
    new_map = dat.uv_layers[new_name] if new_name in dat.uv_layers else dat.uv_layers.new(name=new_name)   
    for loop in obj.data.loops:
        new_map.data[loop.index].uv = uv_map.data[loop.index].uv
    dat.uv_layers.active = new_map
  
    # Switch to Object mode if not already in it (required to change mode to Edit)
    if context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')   
    bpy.ops.object.mode_set(mode='EDIT')       
    bpy.ops.mesh.select_mode(type="VERT")
    # Select all vertices
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.select_all(action='SELECT')
    #Scale
    bpy.context.area.ui_type = 'UV'
    bpy.ops.transform.resize(value=(scale_x, scale_y, 0), constraint_axis=(True, True, False))

    # Revert back to the original state
    bpy.context.area.ui_type = current_area
    bpy.ops.object.mode_set(mode=current_mode)
    dat.uv_layers.active = current_uv
    return new_name