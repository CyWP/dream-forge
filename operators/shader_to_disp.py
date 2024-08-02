import bpy

class ApplyMaterial(bpy.types.Operator):
    bl_idname = "shade.dream_texture_displace_material"
    bl_label = "Bake and Apply material."
    bl_description = "Bake and Apply material to displacement image."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.object.type=="MESH" and any([slot.material is not None for slot in context.object.material_slots])
    
    def execute(self, context):

        #HOTFIX get out of local view 
        if context.space_data.local_view:
            bpy.ops.view3d.localview()
        #2 make sure we are in object mode and nothing is selected
        if bpy.context.object.mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

        #5 remember render engine and switch to CYCLES for baking
        orig_renderer = bpy.data.scenes[bpy.context.scene.name].render.engine
        bpy.data.scenes[bpy.context.scene.name].render.engine = "CYCLES"

        #6 create temporary bake image and material
        bakeimage = bpy.data.images.new("BakeImage", width=512, height=512)
        bakemat = bpy.data.materials.new(name="bakemat")
        bakemat.use_nodes = True

        #9 select lowpoly material and create temporary render target
        orig_mat = context.object.data.materials[0]
        bpy.context.active_object.data.materials[0] = bakemat
        node_tree = bakemat.node_tree
        node = node_tree.nodes.new("ShaderNodeTexImage")
        node.select = True
        node_tree.nodes.active = node
        node.image = bakeimage

        #bake color
        bpy.context.scene.cycles.samples = 1
        bpy.context.scene.render.bake.use_pass_direct = False
        bpy.context.scene.render.bake.use_pass_indirect = False
        bpy.context.scene.render.bake.use_pass_color = True
        bpy.ops.object.bake(type='DIFFUSE', use_clear=True, use_selected_to_active=False)

        #clean up
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.materials.remove(bakemat)
        bakemat.node_tree.nodes.remove(node)
        bpy.context.active_object.data.materials[0] = orig_mat
        bpy.data.scenes[bpy.context.scene.name].render.engine = orig_renderer

        #reload all textures
        for image in bpy.data.images:
            image.reload()

        return {"FINISHED"}