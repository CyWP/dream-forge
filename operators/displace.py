import bpy
import numpy as np
from typing import List

from .dream_texture import CancelGenerator, ReleaseGenerator
from .notify_result import NotifyResult
from ..generator_process import Generator

from ..heph_utils.smooth_vertex_group import auto_smooth
from ..heph_utils.gen_names import gen_mod_name
from ..heph_utils.uv_layout import auto_uv_map, uv_to_img
from ..ui.panels.hephaestus import displace_context

from ..property_groups.hephaestus import unwrap_options, ctrl_img_options
from .. import api

def _validate_displacement(context):
    return context.object.type == 'MESH', context.object.mode=='OBJECT'

def displace_panel(sub_panel, space_type, get_prompt):

    class ActionsPanel(sub_panel):
        """Create a subpanel for actions"""
        bl_idname = f"DREAM_PT_dream_panel_displacement_actions"
        bl_label = "Actions"
        bl_options = {'HIDE_HEADER'}

        @classmethod
        def poll(cls, context):
            return displace_context(context)

        def draw(self, context):
            super().draw(context)
            layout = self.layout
            layout.use_property_split = True

            prompt = get_prompt(context)

            col = layout.column()
            
            col.prop(context.scene, "dream_textures_project_use_control_net")
            if context.scene.dream_textures_project_use_control_net and len(context.scene.dream_textures_project_prompt.control_nets) > 0:
                col.prop(context.scene.dream_textures_project_prompt.control_nets[0], "control_net", text="Type")
                col.prop(context.scene.dream_textures_project_prompt.control_nets[0], "conditioning_scale", text="Strength")

            row = layout.row(align=True)
            row.scale_y = 1.5
            if CancelGenerator.poll(context):
                row.operator(CancelGenerator.bl_idname, icon="SNAP_FACE", text="")
            if context.scene.dream_textures_progress <= 0:
                if context.scene.dream_textures_info != "":
                    disabled_row = row.row(align=True)
                    disabled_row.operator(DisplaceDreamtexture.bl_idname, text=context.scene.dream_textures_info, icon="INFO")
                    disabled_row.enabled = False
                else:
                    r = row.row(align=True)
                    r.operator(DisplaceDreamtexture.bl_idname, icon="MOD_UVPROJECT")
                    r.enabled = context.object is not None and context.object.mode == 'OBJECT'
            else:
                disabled_row = row.row(align=True)
                disabled_row.use_property_split = True
                disabled_row.prop(context.scene, 'dream_textures_progress', slider=True)
                disabled_row.enabled = False
            row.operator(ReleaseGenerator.bl_idname, icon="X", text="")
            
    return ActionsPanel

class DisplaceDreamtexture(bpy.types.Operator):
    bl_idname = "shade.dream_texture_displace"
    bl_label = "Displace using Dream Texture"
    bl_description = "Generate displacement using Stable Diffusion"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        try:
            _validate_displacement(context)
            prompt = context.scene.dream_textures_project_prompt
            backend: api.Backend = prompt.get_backend()
            args = prompt.generate_args(context)
            args.task = api.task.PromptToImage() if context.scene.dream_textures_project_use_control_net else api.task.DepthToImage(None, None, 0)
            backend.validate(args)
        except:
            return False
        return Generator.shared().can_use()
    
    def execute(self, context):

        obj = context.object
        heph_props = context.scene.hephaestus_props
        dream_props = context.scene.dream_textures_project_prompt
        wm = bpy.context.window_manager

        # Setup the progress indicator
        def step_progress_update(self, context):
            if hasattr(context.area, "regions"):
                for region in context.area.regions:
                    if region.type == "UI":
                        region.tag_redraw()
            return None
        
        bpy.types.Scene.displace_progress = bpy.props.IntProperty(name="", default=0, min=0, max=context.scene.dream_textures_project_prompt.steps, update=step_progress_update)
        context.scene.displace_info = "Starting..."  

        gen_name = gen_mod_name(context)
        #Create empty texture of correct size
        try:
            tex = bpy.data.textures[gen_name]
        except:
            tex = bpy.data.textures.new(name=gen_name, type='IMAGE')
        tex_img = bpy.data.images.new(name=tex.name, width=dream_props.width, height=dream_props.height)
        tex.image = tex_img

        #Create displacement modifier(disabled)
        mod = obj.modifiers.new(name=gen_name, type='DISPLACE')
        mod.show_viewport = False
        mod.show_render = False
        mod.strength = heph_props.disp_strength
        mod.mid_level = heph_props.disp_midlevel
        mod.texture_coords = 'UV'
        if heph_props.auto_smoothing:
            context.scene.dream_textures_info = f"Smoothing Vertex Weights"
            mod.vertex_group = auto_smooth(context, vg_name=heph_props.vertex_group, num_iters=heph_props.smooth_amount)
            #context.scene.dream_textures_info = f"Starting..."
        else:
            mod.vertex_group = heph_props.vertex_group
        mod.texture = tex
        #Generate uv map if need be
        uv_map = auto_uv_map(context) if any([heph_props.uv_map in option[0] for option in unwrap_options]) else heph_props.uv_map
        mod.uv_layer = uv_map
        
        #load direction image
        if heph_props.control_image == ctrl_img_options[0][0]:
            ctrl_img = bpy.data.images.get(uv_to_img(context, uv_map))
        elif heph_props.control_image == ctrl_img_options[1][0]:
            ctrl_img = bpy.data.images.get(heph_props.external_image)
            if not ctrl_img:
                ctrl_img = bpy.data.images.load(heph_props.external_image)
        elif heph_props.control_image == ctrl_img_options[2][0]:
            ctrl_img = heph_props.internal_image
        elif heph_props.control_image == ctrl_img_options[3][0]:
            ctrl_img = bpy.data.textures[heph_props.texture_image].image
        else:
            ctrl_img = bpy.data.images.get(f"{tex.name}_ctrl")
            if not ctrl_img:
                ctrl_img = bpy.data.images.new(name=f"{tex.name}_ctrl", width=32, height=32)

        def step_callback(progress: List[api.GenerationResult]) -> bool:
            nonlocal tex_img
            context.scene.dream_textures_progress = progress[-1].progress
            context.scene.dream_textures_info = f"Step {progress[-1].progress}/{progress[-1].total}"
            image = api.GenerationResult.tile_images(progress)
            if tex_img is None:
                tex_img = bpy.data.images.new(name=tex.name, width=image.shape[1], height=image.shape[0])
            tex_img.name = f"Step {progress[-1].progress}/{progress[-1].total}"
            tex_img.pixels[:] = image.ravel()
            tex_img.update()
            tex.image = tex_img
            mod.show_viewport = True
            mod.show_render = True
            return CancelGenerator.should_continue
        
        def callback(results: List[api.GenerationResult] | Exception):
            CancelGenerator.should_continue = None
            if isinstance(results, Exception):
                context.scene.dream_textures_info = ""
                context.scene.dream_textures_progress = 0
                if not isinstance(results, InterruptedError): # this is a user-initiated cancellation
                    eval('bpy.ops.' + NotifyResult.bl_idname)('INVOKE_DEFAULT', exception=repr(results))
                raise results
            else:
                nonlocal tex_img
                context.scene.dream_textures_info = ""
                context.scene.dream_textures_progress = 0
                result = results[-1]
                prompt_subject = context.scene.dream_textures_project_prompt.prompt_structure_token_subject
                seed_str_length = len(str(result.seed))

                if tex_img is None:
                    tex_img = bpy.data.images.new(name=tex.name, width=result.image.shape[1], height=result.image.shape[0])
                tex_img.name = tex.name

                tex_img.pixels[:] = result.image.ravel()
                tex_img.update()
                tex_img.pack()

        #generation part
        backend: api.Backend = context.scene.dream_textures_project_prompt.get_backend()

        context.scene.dream_textures_info = "Starting..."
        CancelGenerator.should_continue = True # reset global cancellation state
    
        image = None
        ctrl_img = np.asarray(ctrl_img.pixels).reshape((ctrl_img.size[0], ctrl_img.size[1], -1))
        if ctrl_img.shape[-1] == 3: #Ensure images are rgba
            ctrl_img = np.stack([ctrl_img, np.ones(shape=(ctrl_img.size[0], ctrl_img.size[1], -1))])
        if context.scene.dream_textures_project_use_control_net:
            generated_args: api.GenerationArguments = context.scene.dream_textures_project_prompt.generate_args(context, init_image=image, control_images=[np.flipud(ctrl_img)])
            backend.generate(generated_args, step_callback=step_callback, callback=callback)
        else:
            generated_args: api.GenerationArguments = context.scene.dream_textures_project_prompt.generate_args(context)
            generated_args.task = api.DepthToImage(ctrl_img, image, context.scene.dream_textures_project_prompt.strength)
            backend.generate(generated_args, step_callback=step_callback, callback=callback)

        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
                return {'FINISHED'}

        return {'FINISHED'}