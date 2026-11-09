import bpy
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'delivery/mm8_lizardman_villager_a.blend'))
old=set(bpy.data.objects);actions=set(bpy.data.actions)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'delivery/mm8_lizardman_villager_a.glb'))
for o in bpy.data.objects:
    if o.type not in ('ARMATURE','MESH'):continue
    print('OBJECT',o.name,'new',o not in old,'world',list(o.matrix_world.to_scale()),'parent',o.parent.name if o.parent else None,'modifiers',[(m.type,m.object.name if m.type=='ARMATURE' else '') for m in o.modifiers],flush=True)
    if o.type=='ARMATURE':
        print('ACTION',o.animation_data.action.name if o.animation_data.action else None,'tracks',[(t.name,[(s.action.name,s.action_slot.name) for s in t.strips]) for t in o.animation_data.nla_tracks],flush=True)
        print('Hips',list(o.data.bones['Hips'].head_local),list(o.pose.bones['Hips'].head),list(o.pose.bones['Hips'].scale),flush=True)
    else:
        ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();p=[ev.matrix_world@v.co for v in m.vertices];print('BOUNDS',[(min(v[i] for v in p),max(v[i] for v in p)) for i in range(3)],flush=True);ev.to_mesh_clear()
print('NEW ACTIONS',[(a.name,list(a.frame_range)) for a in bpy.data.actions if a not in actions],flush=True)
