"""Replace Amuck's unusable sheet head with a tapered solid crescent and open top fork."""
import sys
from pathlib import Path
import bpy,bmesh
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_weapons as weapons

def rebuild(obj):
    bm=bmesh.new();bm.from_mesh(obj.data);seen=set();groups=[]
    for v in bm.verts:
        if v in seen:continue
        group={v};seen.add(v);pending=[v]
        while pending:
            current=pending.pop()
            for e in current.link_edges:
                other=e.other_vert(current)
                if other not in seen:seen.add(other);group.add(other);pending.append(other)
        groups.append(group)
    keep=max(groups,key=len)
    shaft=[v for v in keep if -.2<v.co.y<0]
    cx=(min(v.co.x for v in shaft)+max(v.co.x for v in shaft))/2
    cz=(min(v.co.z for v in shaft)+max(v.co.z for v in shaft))/2
    for group in groups:
        if len(group)>30 and sum(v.co.x for v in group)/len(group)>cx+.025:keep|=group
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if v not in keep],context='VERTS')
    bm.to_mesh(obj.data);bm.free()
    # Authoring coordinates match the normalized, horizontal Meshy weapon before its final support fit.
    weapons.material()
    profile=[[.10,.03,.027],[.13,.10,.075],[.19,.20,.055],[.27,.245,.018],[.35,.245,.018],[.43,.17,.10],[.48,.06,.055],[.49,.025,.023]]
    weapons.axe_cheek(profile,-1,'filigree',.025)
    weapons.rod('closed deep head socket',.17,.39,.027,'brass',12)
    for sign in [-1,1]:
        weapons.tube('gold top fork',[(0,.37,0),(sign*.029,.41,0),(sign*.028,.455,0),(sign*.015,.47,0)],.009,'brass',10)
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    for ob in meshes:
        if ob!=obj:
            for v in ob.data.vertices:v.co.x+=cx;v.co.z+=cz
    bpy.ops.object.select_all(action='DESELECT')
    for ob in meshes:ob.select_set(True)
    bpy.context.view_layer.objects.active=obj;bpy.ops.object.join()
    return obj
