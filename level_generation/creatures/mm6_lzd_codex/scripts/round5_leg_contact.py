"""Resolve the remaining one-millimetre leg/tabard contact on LOD1 using the shared surface diagnostic."""
import bpy,sys,json,runpy,shutil
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parent/'claude_shared/gates'))
from run_gates import Glb,load_meshes,configure_mesh,Report
g=Glb(P/'export/mm6_lzd.glb');cfg=json.loads((P/'gates.json').read_text());m=next(m for m in load_meshes(g)if m.label.endswith('colour1'));configure_mesh(m,cfg,Report(cfg))
a=next(a for a in g.doc['animations']if a['name']=='Death');pose=g.pose(a,np.array([1.125]))[0];points=m.posed(pose)
_,surface,samples,_=next(x for x in m.cloth if x[0]=='loin flap');surface.build(points,pose);i=np.flatnonzero(samples)[707];hit,n,face,dist=surface.tree.find_nearest(Vector(points[i]))
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round5/lod1.blend'));ob=bpy.data.objects['Body'];co=np.array([v.co[:]for v in ob.data.vertices]);idx=int(np.linalg.norm(co-m.rest[i],axis=1).argmin());assert np.linalg.norm(co[idx]-m.rest[i])<1e-5
pv=np.array([x.value for x in ob.data.attributes['piece'].data]);assert pv[idx]==19
matrices=pose[m.skin_nodes[m.joints[i]]]@m.bind[m.joints[i]];skin=(matrices*m.weights[i,:,None,None]).sum(0)
rest=(g.rest[m.skin_nodes[m.joints[i]]]@m.bind[m.joints[i]]*m.weights[i,:,None,None]).sum(0)
delta=rest[:3,:3]@np.linalg.solve(skin[:3,:3],np.array(n)*.001)
changed=[]
for v in ob.data.vertices:
 if pv[v.index]!=pv[idx]:continue
 w=max(0,1-float(np.linalg.norm(co[v.index]-co[idx]))/.025)
 if w:v.co+=Vector(delta*w);changed.append(v.index)
ob.data.update();bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round5/lod1.blend'))
data=json.loads((P/'work/round5/lod1_pieces.json').read_text());data['positions']=[list(v.co)for v in ob.data.vertices];(P/'work/round5/lod1_pieces.json').write_text(json.dumps(data))
r=bpy.data.objects['Rig'];bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);r.select_set(True);bpy.context.view_layer.objects.active=r;ob.name=ob.data.name='Lizard'
bpy.ops.export_scene.gltf(filepath=str(P/'export/mm6_lzd_level1.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_image_format='AUTO')
(P/'review/round5/leg_contact.json').write_text(json.dumps({'source_vertex':idx,'bind_position':co[idx].tolist(),'posed_position':points[i].tolist(),'normal':list(n),'offset_m':.001,'affected':changed},indent=2))
shutil.copyfile(P/'work/round5/lod0.blend',P/'work/master.blend');runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__');runpy.run_path(str(P/'scripts/patch_string_export.py'),run_name='__main__');shutil.copyfile(P/'export/mm6_lzd_raw.glb',P/'export/mm6_lzd_lod0.glb')
