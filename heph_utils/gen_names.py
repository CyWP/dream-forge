import bpy

PREFIX = "heph_"

def gen_mod_name(context) -> str:
    obj = context.object
    highest = -1
    for mod in obj.modifiers:
        if mod.name[:5] == PREFIX:
            try:
                val = int(mod.name[6:])
                highest = max(val, highest)
            except:
                pass
    for img in bpy.data.images:
        if img.name[:5] == PREFIX:
            try:
                val = int(img.name[6:])
                highest = max(val, highest)
            except:
                pass
    return f"{PREFIX}_{highest+1}"