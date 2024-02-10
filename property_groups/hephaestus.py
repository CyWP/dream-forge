import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, StringProperty


control_images = (('Auto', 'Auto', ''),
                ('None', 'None', ''),
                ('External', 'External', ''),
                ('Internal', 'Internal', ''),
                ('Texture', 'Texture', ''))

tiling_axes = (('BOTH', 'BOTH', ''),
               ('X', 'X', ''),
               ('Y', 'Y', ''))

def get_active_modifiers(self, context):
    obj = context.object
    list = []
    for mod in obj.modifiers:
        if mod.name[:4]=="heph":
            list.append((mod.name, mod.name, ""))
    if len(list)==0:
        return None
    return list

def get_internal_images(self, context):
    if bpy.data.images is None:
        return [('', '', '')]
    return [(img.filepath, img.filepath, '') for img in bpy.data.images]

def get_uv_maps(self, context):
    obj = context.object

    if obj is None or obj.type != 'MESH':
        return [('', '', '')]
    
    obj = obj.data
    
    uvlist = [('Auto Unwrap', 'Auto Unwrap', ''),
              ('Smart Island Project', 'Smart Island Project', '')]
    for uv in obj.uv_layers:
        uvlist.append((uv.name, uv.name, ''))

    return uvlist

def get_textures(self, context):
    if bpy.data.textures is None:
        return [('', '', '')]
    return [(tex.name, tex.name, '') for tex in bpy.data.textures]

def get_vertex_groups(self, context):
    obj = context.object

    if obj is None or obj.type != 'MESH':
        return [('', '', '')]
    
    vglist = [('All', 'All', '')]
    for vg in obj.vertex_groups:
        vglist.append((vg.name, vg.name, ''))

    return vglist

attributes = {
    #Scene
    "active_modifier": EnumProperty(name="",
                                     items=get_active_modifiers,
                                     description="Modifier to update"), 
    #Mesh
    "vertex_group": EnumProperty(name="Vertex Group",
                                 items=get_vertex_groups,
                                 description="Specify which vertices will be affected by displacement."),
    "uv_map": EnumProperty(name="UV Map",
                           items=get_uv_maps,
                           description="Specify which UV Map to use for projection of texture."),
    "auto_smoothing": BoolProperty(name="Auto Edge Smoothing",
                                   default=False,
                                   description="Automatic smoothing of displacement values towards edges of UV islands."),
    "smooth_amount": FloatProperty(name="Smoothing",
                                   default=0.25, min=0., max=1.,
                                   subtype='PERCENTAGE',
                                   description="0 for no smoothing, 1 for max smoothing(full displacement only applied at farthest point from all edges)"),
    "disp_strength": FloatProperty(name="Strength",
                                   default=1.,
                                   description="Strength multiplier of displacement distance."),
    "disp_midlevel": FloatProperty(name="Midlevel",
                                   default=0.5, min=0., max=1.,
                                   description="Threshold dictating inwards or outwards displacement."),
    #Image
    "control_image": EnumProperty(name="Source",
                                 items=control_images,
                                 description="Provenance of image for texture generation control."),
    "internal_image":EnumProperty(name="Image",
                                  items=get_internal_images),
    "external_image": StringProperty(name="Image",
                                     default="path/to/image",
                                     subtype='FILE_PATH'),
    "texture_image": EnumProperty(name="Image",
                                  items=get_textures),
    "tile_image": BoolProperty(name="Tile",
                               default=False,
                               description="Tile generated image across UV map"),
    "tile_axes": EnumProperty(name="Axes",
                                items=tiling_axes,
                                description="Axis on which image will be repeated"),
    "tile_num": FloatProperty(name="Factor",
                              default=2., min=0,
                              description="Repetitions of image on UV map.")
}

HephProps = type('HephProps', (bpy.types.PropertyGroup,), {
    "bl_label": "HephProps",
    "bl_idname": "dream_textures.Hephprops",
    "__annotations__": attributes,
})