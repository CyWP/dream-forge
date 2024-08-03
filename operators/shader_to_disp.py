import bpy

class ApplyMaterial(bpy.types.Operator):
    bl_idname = "shade.dream_texture_displace_material"
    bl_label = "Bake and Apply material."
    bl_description = "Bake and Apply material to displacement image."
    bl_options = {'REGISTER', 'UNDO'}
    button_text = "Bake and Apply Material"

    @classmethod
    def poll(cls, context):
        return context.active_object.type=="MESH" and any([slot.material is not None for slot in context.object.material_slots])
    
    def execute(self, context):
        obj = context.active_object
        props = context.scene.hephaestus_props

        #HOTFIX get out of local view 
        if context.space_data.local_view:
            bpy.ops.view3d.localview()
        # make sure we are in object mode and nothing is selected
        if bpy.context.object.mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')
        #remember render engine and switch to CYCLES for baking
        orig_renderer = bpy.data.scenes[bpy.context.scene.name].render.engine
        bpy.data.scenes[bpy.context.scene.name].render.engine = "CYCLES"
        #create temporary bake image and material
        mat = context.object.data.materials[0]
        bakeimage = bpy.data.images.new(name=f"{obj.name}_{mat.name}_bake", width=props.bake_img_width, height=props.bake_img_height)
        node_tree = mat.node_tree
        node = node_tree.nodes.new("ShaderNodeTexImage")
        node.select = True
        node_tree.nodes.active = node
        node.image = bakeimage    
        #bake color
        bpy.context.scene.cycles.samples = 1
        bpy.context.scene.render.bake.use_pass_direct = False
        bpy.context.scene.render.bake.use_pass_indirect = False
        bpy.context.scene.render.bake.use_pass_color = True
        bpy.ops.object.bake(type='DIFFUSE', use_clear=True)
        bakeimage.pack()
        #clean up
        mat.node_tree.nodes.remove(node)
        bpy.data.scenes[bpy.context.scene.name].render.engine = orig_renderer

        #Apply to active modifier
        mod = obj.modifiers[props.active_modifier]
        tex = mod.texture
        tex.image = bakeimage

        return {"FINISHED"}