import bpy
from ..heph_utils.smooth_vertex_group import auto_smooth

class SmoothVertexGroup(bpy.types.Operator):
    bl_idname = "shade.dream_texture_displace_smooth_vg"
    bl_label = "Smooth Vertex Group"
    bl_description = "Smooth a modifier's vertex group's edges."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        heph_props = context.scene.hephaestus_props
        return heph_props.active_modifier in context.object.modifiers
    
    def execute(self, context):
        obj = context.object
        heph_props = context.scene.hephaestus_props
        mod = obj.modifiers[heph_props.active_modifier]
        
        mod.vertex_group = auto_smooth(context, vg_name=mod.vertex_group, num_iters=heph_props.edit_smooth_amount, update=True)

        return {'FINISHED'}