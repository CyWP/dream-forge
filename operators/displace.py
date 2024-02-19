import bpy
import bmesh
import gpu
import gpu.texture
from gpu_extras.batch import batch_for_shader
import bmesh
from bpy_extras import view3d_utils
import mathutils
import numpy as np
from typing import List

from .view_history import ImportPromptFile
from .open_latest_version import OpenLatestVersion, is_force_show_download, new_version_available

from ..ui.panels.hephaestus import create_panel, prompt_panel, size_panel, advanced_panel, mesh_panel, control_panel
from .dream_texture import CancelGenerator, ReleaseGenerator
from .notify_result import NotifyResult

from ..generator_process import Generator
from ..generator_process.models import ModelType
from ..api.models import FixItError
import tempfile
import time
import copy

from ..engine.annotations.depth import render_depth_map

from .. import api

def _validate_displacement(context):
    return True

def auto_smooth(context, vg_name):
    obj = context.object
    dat = obj.data
    heph_props = context.scene.hephaestus_props
    smooth_factor = heph_props.smooth_amount
    vgi = obj.vertex_groups[heph_props.vertex_group].index

    return vg_name
'''def auto_smooth(context, vg_name):
    obj = context.object
    dat = obj.data
    heph_props = context.scene.hephaestus_props
    smooth_factor = heph_props.smooth_amount
    vgi = obj.vertex_groups[heph_props.vertex_group].index

    #get all vertices in vertex group
    vg = [ v.index for v in dat.vertices if vgi in [ vg.group for vg in v.groups ] ]
    print(1)
    #Map vertices to their neighbours
    map = [set() for _ in range(len(dat.vertices))]
    for edge in dat.edges:
        if edge.vertices[0] in vg:
            map[edge.vertices[0]].add(edge.vertices[1])
        if edge.vertices[1] in vg:
            map[edge.vertices[1]].add(edge.vertices[0])
    print(2)
    #define vertices on edge of vertex group
    #edge_verts = [v for v in vg if [neighbor not in vg for neighbor in map[v.index]].any()]
    edge_verts = [v for v in vg if any(neighbor not in vg for neighbor in map[v])]
    print(3)
    #initialize edge vertices' distances to 0
    distances = [0 if i in edge_verts else float('inf') for i in range(len(dat.vertices)) ]
    print(4)
    #record min distance from edge for each
    #start at edge, set neighbours distance f smaller, do the same with neighbours
    active_verts = edge_verts
    updates = True
    #loop until weights are no longer updated, breadth-first search
    i=0
    while updates:
        print(f'loop {i}')
        i+=1
        updates = False
        new_verts = set()
        for v in active_verts:
            for neighbor in [adj for adj in map[v] if adj in vg]:
                new_verts.add(neighbor)
                new_dist = distances[v]+np.linalg.norm(dat.vertices[neighbor].co-dat.vertices[v].co)
                if new_dist < distances[neighbor]:
                    updates = True
                    distances[neighbor] = new_dist
        active_verts = new_verts
    print(5)
    distances = [0 if dist==float('inf') else dist for dist in distances]
    #make new vg as copy of original oen with new weights
    smoothed_vg = obj.vertex_groups.new(name=vg_name)
    print(6)
    #create weights list from list of distances
    max_dist = max(distances)
    threshold = max_dist*smooth_factor
    weights = [-0.5*np.cos((np.pi*dist)/(threshold))+0.5 if dist<threshold else 1 for dist in [distances[v] for v in vg]]
    print(weights)
    print(distances)
    smoothed_vg.add([v.index for v in vg], weights, 'ADD')
    
    return vg_name'''

def dream_texture_displacement_panels():

    class DREAM_PT_dream_panel_displacement(bpy.types.Panel):
        """creates a Dream textures panel for displacement generation"""
        bl_label = "Dream Texture Displacement"
        bl_idname = f"DREAM_PT_dream_panel_displacement"
        bl_category = "Heph"
        bl_space_type = 'VIEW_3D'
        bl_region_type = 'UI'

        @classmethod
        def poll(cls, context):
            if cls.bl_space_type == 'NODE_EDITOR':
                return context.area.ui_type == "ShaderNodeTree" or context.area.ui_type == "CompositorNodeTree"
            else:
                return True
            
        def draw_header_preset(self, context):
            layout = self.layout
            layout.operator(ImportPromptFile.bl_idname, text="", icon="IMPORT")
            layout.separator()

        def draw(self, context):
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False

            layout.prop(context.scene.dream_textures_project_prompt, "backend")
            layout.prop(context.scene.dream_textures_project_prompt, 'model')

    yield DREAM_PT_dream_panel_displacement

    def get_prompt(context):
        return context.scene.dream_textures_project_prompt
    def get_heph_props(context):
        return context.scene.hephaestus_props
    yield from create_panel('VIEW_3D', 'UI', DREAM_PT_dream_panel_displacement.bl_idname, prompt_panel, get_prompt)
    yield create_panel('VIEW_3D', 'UI', DREAM_PT_dream_panel_displacement.bl_idname, size_panel, get_prompt)
    yield from create_panel('VIEW_3D', 'UI', DREAM_PT_dream_panel_displacement.bl_idname, advanced_panel, get_prompt)
    yield create_panel('VIEW_3D', 'UI', DREAM_PT_dream_panel_displacement.bl_idname, mesh_panel, get_heph_props)
    yield create_panel('VIEW_3D', 'UI', DREAM_PT_dream_panel_displacement.bl_idname, control_panel, get_heph_props)

    def actions_panel(sub_panel, space_type, get_prompt):

        class ActionsPanel(sub_panel):
            """Create a subpanel for actions"""
            bl_idname = f"DREAM_PT_dream_panel_displacement_actions"
            bl_label = "Actions"
            bl_options = {'HIDE_HEADER'}

            def draw(self, context):
                super().draw(context)
                layout = self.layout
                layout.use_property_split = True

                prompt = get_prompt(context)

                col = layout.column()
                
                col.prop(context.scene, "dream_textures_project_use_control_net")
                if context.scene.dream_textures_project_use_control_net and len(prompt.control_nets) > 0:
                    col.prop(prompt.control_nets[0], "control_net", text="Type")
                    col.prop(prompt.control_nets[0], "conditioning_scale", text="Strength")

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
    yield create_panel('VIEW_3D', 'UI', DREAM_PT_dream_panel_displacement.bl_idname, actions_panel, get_prompt)

class UpdateDisplacement(bpy.types.Operator):
    bl_idname = "shade.dream_texture_displace_update"
    bl_label = "Update Mesh"
    bl_description = "Update displacement parameters on mesh"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        heph_props = context.scene.hephaestus_props
        return heph_props.active_modifier not in (None, '')#No clue what it's actually returning, this works though
    
    def execute(self, context):
        obj = context.object
        heph_props = context.scene.hephaestus_props
        mod = obj.modifiers[heph_props.active_modifier]

        mod.strength = heph_props.disp_strength
        mod.mid_level = heph_props.disp_midlevel
        mod.uv_layer = heph_props.uv_map
        mod.vertex_group = heph_props.vertex_group 
        return {'FINISHED'}  

class DisplaceDreamtexture(bpy.types.Operator):
    bl_idname = "shade.dream_texture_displace"
    bl_label = "Displace using Dream Texture"
    bl_description = "Generate displacement using Stable Diffusion"
    bl_options = {'REGISTER'}

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

        # Setup the progress indicator
        def step_progress_update(self, context):
            if hasattr(context.area, "regions"):
                for region in context.area.regions:
                    if region.type == "UI":
                        region.tag_redraw()
            return None
        
        bpy.types.Scene.displace_progress = bpy.props.IntProperty(name="", default=0, min=0, max=context.scene.dream_textures_project_prompt.steps, update=step_progress_update)
        context.scene.displace_info = "Starting..."

        #TODO: implement auto uv unwrapping     

        if(heph_props.auto_smoothing):
            vg_name = f"smooth_{heph_props.vertex_group}_{int(heph_props.smooth_amount*100)}"
            if vg_name not in obj.vertex_groups:
                mod.vertex_group = auto_smooth(context, vg_name=vg_name)

        #Create empty texture of correct size
        tex = bpy.data.textures.new(name=f'heph_{int(time.time()*100)}', type='IMAGE')
        tex_img = bpy.data.images.new(name=tex.name, width=dream_props.width, height=dream_props.height)
        tex.image = tex_img

        #Create displacement modifier(disabled)
        mod = obj.modifiers.new(name=tex.name, type='DISPLACE')
        mod.show_viewport = False
        mod.show_render = False
        mod.strength = heph_props.disp_strength
        mod.mid_level = heph_props.disp_midlevel
        mod.texture_coords = 'UV'
        mod.uv_layer = heph_props.uv_map
        mod.vertex_group = heph_props.vertex_group
        mod.texture = tex
        
        #load direction image
        if heph_props.control_image == 'Internal':
            ctrl_img = bpy.data.images.load(heph_props.internal_image)
        elif heph_props.control_image == 'External':
            ctrl_img = bpy.data.images.load(heph_props.external_image)
        elif  heph_props.control_image == 'Texture':
            ctrl_img = bpy.data.textures[heph_props.texture_image].image
        else:
            ctrl_img = bpy.data.images.new(name=f'{tex.name}_ctrl', width=dream_props.width, height=dream_props.height)
        #TODO: Implement Auto image
            
        if(heph_props.tile_image):
            #TODO: Scale UV
            tex.extension = 'REPEAT'

        def step_callback(progress: List[api.GenerationResult]) -> bool:
            nonlocal tex_img
            context.scene.dream_textures_progress = progress[-1].progress
            image = api.GenerationResult.tile_images(progress)
            if tex_img is None:
                tex_img = bpy.data.images.new(name=tex.name, width=image.shape[1], height=image.shape[0])
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
        ctrl_img = np.asarray(ctrl_img.pixels).reshape((ctrl_img.size[0], ctrl_img.size[1], -1)) if ctrl_img is not None else None
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