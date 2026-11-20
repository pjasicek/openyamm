"""Repeat the surface gates on the final UV-split GLB, including between its 60 Hz keys."""
from pathlib import Path
P=Path(__file__).resolve().parents[1]
s=(P/'scripts/check_pilots.py').read_text()
old="bpy.ops.wm.open_mainfile(filepath=str(P/'work/pilots_fitted.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];"
new="""bpy.ops.wm.open_mainfile(filepath=str(P/'work/step1.blend'))
from mathutils.kdtree import KDTree
src=bpy.data.objects['Body'];tree=KDTree(len(src.data.vertices));pieces=[v.value for v in src.data.attributes['piece'].data]
for v in src.data.vertices:tree.insert(v.co,v.index)
tree.balance();bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(P/'export/mm8_m592_runtime_lod0.glb'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=bpy.data.objects['PlaneGuardian'];
"""
assert old in s;s=s.replace(old,new).replace("piece=np.array([x.value for x in me.attributes['piece'].data])","piece=np.array([pieces[tree.find(v.co)[1]] for v in me.vertices])")
a=s.index("F=json.loads");b=s.index("report=",a)
s=s[:a]+"""hard=[]
for j,n in enumerate(gn):
 if 'Finger' in n:
  mask_hard=W[:,j]>.9999;hard.extend(np.flatnonzero(valid&mask_hard[E].all(1)).tolist())
assert len(hard)>100
"""+s[b:]
s=s.replace("('Standing','Walking','Running','Attack')","('Standing','Walking','Running','Attack','Cast','Hit','Fidget','Death','Dead')").replace("a=bpy.data.actions[name]","a=next(a for a in bpy.data.actions if a.name==name or a.name.startswith(name+'_'))").replace("a.frame_range[1]+.01,.5","a.frame_range[1]+.01,.25").replace("C[foot[sd],2].min()","(C[:,2].min() if name in ('Death','Dead') else C[foot[sd],2].min())").replace("P/'review/pilot_gates.json'","P/'review/export_motion_gates.json'")
exec(compile(s,str(P/'scripts/check_pilots.py'),'exec'))
assert max(r['minimum_sole'] for r in report['clips'].values())<.001
assert all(not r['contacts'] for r in report['clips'].values()),{n:r['contacts'] for n,r in report['clips'].items() if r['contacts']}
