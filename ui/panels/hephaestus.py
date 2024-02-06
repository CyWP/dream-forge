from bpy.types import Panel
from bpy_extras.io_utils import ImportHelper

import webbrowser
import os
import shutil

from ...absolute_path import CLIPSEG_WEIGHTS_PATH
from ..presets import DREAM_PT_AdvancedPresets
from ...pil_to_image import *
from ...prompt_engineering import *
from ...operators.dream_texture import DreamTexture, ReleaseGenerator, CancelGenerator, get_source_image
from ...operators.open_latest_version import OpenLatestVersion, is_force_show_download, new_version_available
from ...operators.view_history import ImportPromptFile
from ..space_types import SPACE_TYPES
from ...property_groups.dream_prompt import DreamPrompt, backend_options
from ...generator_process.actions.prompt_to_image import Optimizations
from ...generator_process.actions.detect_seamless import SeamlessAxes
from ...api.models import FixItError

def create_panel(space_type, region_type, parent_id, ctor, get_prompt, use_property_decorate=False, **kwargs):
    class BasePanel(bpy.types.Panel):
        bl_category = "Dream"
        bl_space_type = space_type
        bl_region_type = region_type

    class SubPanel(BasePanel):
        bl_category = "Dream"
        bl_space_type = space_type
        bl_region_type = region_type
        bl_parent_id = parent_id

        def draw(self, context):
            self.layout.use_property_decorate = use_property_decorate

    return ctor(kwargs.pop('base_panel', SubPanel), space_type, get_prompt, **kwargs)

def mesh_panel(sub_panel, space_type, get_prompt):
    class MeshPanel(sub_panel):
        """Create a subpanel for mesh input"""
        bl_label = "Mesh"
        bl_idname = f"DREAM_PT_dream_displacement_panel_mesh_{space_type}"

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

            


def prompt_panel(sub_panel, space_type, get_prompt):
    class PromptPanel(sub_panel):
        """Create a subpanel for prompt input"""
        bl_label = "Prompt"
        bl_idname = f"DREAM_PT_dream_displacement_panel_prompt_{space_type}"

        def draw_header_preset(self, context):
            layout = self.layout
            layout.prop(get_prompt(context), "prompt_structure", text="")

        def draw(self, context):
            super().draw(context)
            layout = self.layout
            layout.use_property_split = True
            prompt = get_prompt(context)

            structure = next(x for x in prompt_structures if x.id == prompt.prompt_structure)
            for segment in structure.structure:
                segment_row = layout.row()
                enum_prop = 'prompt_structure_token_' + segment.id + '_enum'
                is_custom = getattr(prompt, enum_prop) == 'custom'
                if is_custom:
                    segment_row.prop(prompt, 'prompt_structure_token_' + segment.id)
                enum_cases = DreamPrompt.__annotations__[enum_prop].keywords['items']
                if len(enum_cases) != 1 or enum_cases[0][0] != 'custom':
                    segment_row.prop(prompt, enum_prop, icon_only=is_custom)
            if prompt.prompt_structure == file_batch_structure.id:
                layout.template_ID(context.scene, "dream_textures_prompt_file", open="text.open")
            
    yield PromptPanel

    class NegativePromptPanel(sub_panel):
        """Create a subpanel for negative prompt input"""
        bl_idname = f"DREAM_PT_dream_panel_displacement_negative_prompt_{space_type}"
        bl_label = "Negative"
        bl_parent_id = PromptPanel.bl_idname

        @classmethod
        def poll(cls, context):
            return get_prompt(context).prompt_structure != file_batch_structure.id

        def draw_header(self, context):
            layout = self.layout
            layout.prop(get_prompt(context), "use_negative_prompt", text="")

        def draw(self, context):
            super().draw(context)
            layout = self.layout
            layout.use_property_split = True
            layout.enabled = layout.enabled and get_prompt(context).use_negative_prompt
            scene = context.scene

            layout.prop(get_prompt(context), "negative_prompt")
    yield NegativePromptPanel

def size_panel(sub_panel, space_type, get_prompt):
    class SizePanel(sub_panel):
        """Create a subpanel for size options"""
        bl_idname = f"DREAM_PT_dream_panel_displacement_size_{space_type}"
        bl_label = "Size"
        bl_options = {'DEFAULT_CLOSED'}

        def draw_header(self, context):
            self.layout.prop(get_prompt(context), "use_size", text="")

        def draw(self, context):
            super().draw(context)
            layout = self.layout
            layout.use_property_split = True
            layout.enabled = layout.enabled and get_prompt(context).use_size

            layout.prop(get_prompt(context), "width")
            layout.prop(get_prompt(context), "height")
    return SizePanel
   
