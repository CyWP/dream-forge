import bpy

class ApplyViewerNode(bpy.types.Operator):
    bl_idname = "shade.dream_texture_displace_viewer_node"
    bl_label = "Apply viewer node output to displacement"
    bl_description = "Apply viewer node output to displacement."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        heph_props = context.scene.hephaestus_props
        tree = context.scene.node_tree
        has_mod = context.object.modifiers[heph_props.active_modifier] is not None
        has_viewer_node = tree and "Viewer" in tree.nodes and "Viewer Node" in bpy.data.images
        return has_mod and has_viewer_node
    
    def execute(self, context):
        obj = context.object
        heph_props = context.scene.hephaestus_props
        mod = obj.modifiers[heph_props.active_modifier]
        tree = context.scene.node_tree
            
        viewer_image = bpy.data.images["Viewer Node"]
        width, height = viewer_image.size
        pixels = list(viewer_image.pixels)
        new_image_name = mod.name+"_vn"
        new_image = bpy.data.images.new(name=new_image_name, width=width, height=height)
        new_image.pixels = pixels
        mod.texture.image = new_image
        return {'FINISHED'}