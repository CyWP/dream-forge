import bpy
from .constants import PREFIX

def gen_mod_name(context) -> str:
    obj = context.object
    highest = -1
    for mod in obj.modifiers:
        if mod.name[:len(PREFIX)] == PREFIX:
            try:
                val = int(mod.name[len(PREFIX)+1:])
                highest = max(val, highest)
            except:
                pass
    for img in bpy.data.images:
        if img.name[:len(PREFIX)] == PREFIX:
            try:
                val = int(img.name[len(PREFIX)+1:])
                highest = max(val, highest)
            except:
                pass
    return f"{PREFIX}_{highest+1}"