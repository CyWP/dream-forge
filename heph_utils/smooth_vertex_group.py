import bpy
import numpy as np
import copy

SMOOTHED = "_smoothed_"

def auto_smooth(context, vg_name:str=None, update=False) -> str:
    obj = context.object
    dat = obj.data
    heph_props = context.scene.hephaestus_props
    num_iters = heph_props.smooth_amount
    weights = (-(np.cos(np.linspace(0, np.pi, num_iters+2)))[1:-1]+1)/2
    if vg_name is None:
        vg_name = heph_props.vertex_group

    if vg_name not in obj.vertex_groups:
        raise ValueError(f"{vg_name} is not a valid vertex group for object {obj.name}.")
    if update and vg_name in obj.vertex_groups:
        smoothed_vg = obj.vertex_groups[vg_name]
    elif not update and vg_name in obj.vertex_groups:
        return vg_name
    else:
        smoothed_vg = obj.vertex_groups.new(name=f"{vg_name}{SMOOTHED}{num_iters}")

    vgi = obj.vertex_groups[vg_name].index
    vi = set([v.index for v in dat.vertices if vgi in [vg.group for vg in v.groups]])

    edges = dat.edges  
    for i in range(num_iters):
        iv = copy.copy(vi)
        etemp = []
        ev = []
        for edge in edges:
            if edge.vertices[0] in vi:
                if edge.vertices[1] not in vi:
                    ev.append(edge.vertices[0])
                    iv.discard(edge.vertices[0])
                else:
                    etemp.append(edge)
            elif edge.vertices[1] in vi:
                ev.append(edge.vertices[1])
                iv.discard(edge.vertices[1])        
        ev = list(set(ev))
        edges = etemp
        vi = iv
        smoothed_vg.add(ev, weights[i], 'REPLACE')
    smoothed_vg.add(list(vi), 1, 'REPLACE')   
    return vg_name

def update_smoothed_vgs(context, vg_name:str):
    obj = context.object

    for vg in obj.vertex_groups:
        if vg_name in vg.name and SMOOTHED in vg.name:
            auto_smooth(context, vg_name=vg.name, update=True)