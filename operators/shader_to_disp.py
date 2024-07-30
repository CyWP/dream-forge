import bpy

class ApplyMaterial(bpy.types.Operator):
    bl_idname = "shade.dream_texture_displace_material"
    bl_label = "Bake and Apply material."
    bl_description = "Bake and Apply material to displacement image."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        pass
    
    def execute(self, context):
        pass