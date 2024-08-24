from ...pil_to_image import *
from ...prompt_engineering import *
from ...operators.smooth_vertex_group import SmoothVertexGroup
from ...operators.viewer_to_disp import ApplyViewerNode
from ...operators.create_uv_img import CreateUvImg
from ...operators.shader_to_disp import ApplyMaterial
from ...heph_utils.constants import PREFIX

def displace_context(context) -> bool:
    return context.scene.dream_context == "Displace" and context.space_data.type == 'VIEW_3D'

def mesh_panel(sub_panel, space_type, get_prompt):
    class MeshPanel(sub_panel):
        """Create a subpanel for mesh input"""
        bl_label = "Mesh"
        bl_idname = f"DREAM_PT_dream_panel_mesh_{space_type}"
        bl_category = "Dream"
        bl_space_type = 'VIEW_3D'
        bl_region_type = 'UI'

        @classmethod
        def poll(cls, context):
            return displace_context(context)

        def draw_header_preset(self, context):
            layout = self.layout
            obj = context.object

            if obj != None and obj.type=='MESH':
                layout.label(text= f"Active object: {obj.name}", icon='MESH_MONKEY')
            else:
                layout.label(text = 'Select a valid mesh object', icon='ERROR')

        def draw(self, context):
            layout = self.layout
            obj = context.object
            props = get_prompt(context)

            row = layout.row()
            row.prop(props, 'vertex_group')
            row = layout.row()
            row.prop(props, 'uv_map')
            row.operator(CreateUvImg.bl_idname, text="Create UV Image", icon="MOD_TRIANGULATE")
            row = layout.row()
            row.prop(props, 'auto_smoothing')
            if props.auto_smoothing:
                row.prop(props, 'smooth_amount')
            row=layout.row()
            row.prop(props, 'disp_strength')
            row.prop(props, 'disp_midlevel')

    return MeshPanel

def edit_panel(sub_panel, space_type, get_prompt):
    class EditPanel(sub_panel):
        """Create a subpanel for editing displacement modifiers"""
        bl_label = "Edit"
        bl_idname = f"DREAM_PT_dream_panel_edit_{space_type}"
        bl_category = "Dream"
        bl_space_type = 'VIEW_3D'
        bl_region_type = 'UI'

        @classmethod
        def poll(cls, context):
            return displace_context(context) and any(mod.name[:len(PREFIX)]==PREFIX for mod in context.object.modifiers) and context.active_object.type=="MESH"

        def draw_header_preset(self, context):
            props = get_prompt(context)
            layout = self.layout
            layout.scale_x = 1.5
            layout.prop(props, 'active_modifier', icon='MODIFIER')

        def draw(self, context):
            props = get_prompt(context)
            if props.active_modifier in context.object.modifiers:
                layout = self.layout
                row = layout.row()
                row.prop(props, 'edit_disp_strength')
                row = layout.row()
                row.prop(props, 'edit_disp_midlevel')
                row = layout.row()
                row.prop(props, 'edit_smooth_amount')
                row.operator(SmoothVertexGroup.bl_idname, text="Update Smoothing", icon="SMOOTHCURVE")
                row = layout.row()
                row.operator(ApplyViewerNode.bl_idname, text="Apply Viewer Node", icon="FORCE_TEXTURE")
                box = layout.box()
                row = box.row()
                row.prop(props, 'bake_img_width')
                row.prop(props, 'bake_img_height')
                row=box.row()
                row.operator(ApplyMaterial.bl_idname, text=ApplyMaterial.button_text, icon="MATERIAL")
                
    return EditPanel

def control_panel(sub_panel, space_type, get_prompt):

    class ControlPanel(sub_panel):
        """Create a subpanel for control image input"""
        bl_label = "Control"
        bl_idname = f"DREAM_PT_dream_panel_control_{space_type}"
        bl_category = "Dream"
        bl_space_type = 'VIEW_3D'
        bl_region_type = 'UI'

        @classmethod
        def poll(cls, context):
            return displace_context(context)

        def draw_header_preset(self, context):
            layout = self.layout
            obj = context.object

            layout.scale_x = 1.1
            layout.prop(get_prompt(context), "control_image", icon="MOD_OPACITY")

        def draw(self, context):
            layout = self.layout
            obj = context.object
            props = get_prompt(context)

            if props.control_image == 'External':
                layout.prop(props, 'external_image')
            elif props.control_image == 'Internal':
                layout.prop(props, 'internal_image')
            elif props.control_image == 'Texture':
                layout.prop(props, 'texture_image')
        
    return ControlPanel