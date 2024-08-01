import bpy
from ..heph_utils.uv_layout import uv_to_img, auto_uv_map

class CreateUvImg(bpy.types.Operator):
    bl_idname = "shade.dream_texture_displace_uv_img"
    bl_label = "Create UV image"
    bl_description = "Create Editable UV image for image geenration control."
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return context.object.data.uv_layers
    
    def execute(self, context):
        props = context.scene.hephaestus_props
        uv_to_img(context, auto_uv_map(context), suffix="edit")
        return {'FINISHED'}