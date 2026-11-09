import bpy,json
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];sc=bpy.context.scene
bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm6_cdr1.blend'));sc=bpy.context.scene;rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body']
def vertices(obj):
 e=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();used={i for f in m.polygons for i in f.vertices};v=[e.matrix_world@m.vertices[i].co for i in used];e.to_mesh_clear();return v
def distance(a,b):
 tree=KDTree(len(b))
 for i,v in enumerate(b):tree.insert(v,i)
 tree.balance();return max(tree.find(v)[2] for v in a)
refs={};clips=json.loads((P/'work/clips.json').read_text())
for name,c in clips.items():
 rig.animation_data.action=bpy.data.actions[name]
 for f in [0,c['frames']*.25,c['frames']*.5,c['frames']*.75,c['frames']]:
  sc.frame_set(int(f),subframe=f%1);refs[name,f]=vertices(body)
for ob in list(bpy.data.objects):bpy.data.objects.remove(ob,do_unlink=True)
for action in list(bpy.data.actions):bpy.data.actions.remove(action)
bpy.ops.import_scene.gltf(filepath=str(P/'export/mm6_cdr1_selected.glb'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=next(o for o in bpy.data.objects if o.type=='MESH');sc.render.fps=48;out={}
for name,c in clips.items():
 a=next(a for a in bpy.data.actions if a.name==name or a.name.endswith('|'+name));rig.animation_data.action=a;errors=[]
 for f in [0,c['frames']*.25,c['frames']*.5,c['frames']*.75,c['frames']]:
  sc.frame_set(int(f),subframe=f%1);v=vertices(body);errors.append(max(distance(v,refs[name,f]),distance(refs[name,f],v)))
 out[name]=max(errors);assert max(errors)<.0001,(name,max(errors))
 if name=='Dead':assert distance(refs[name,0],refs[name,c['frames']])<1e-7
for name in ['Standing','Walking','Running']:
 assert distance(refs[name,0],refs[name,clips[name]['frames']])<1e-5,name
(P/'review/export_parity.json').write_text(json.dumps({'maximum_vertex_errors_m':out,'samples_per_clip':5,'loop_endpoints_match':True,'dead_static':True},indent=2)+'\n');print('PARITY',out)
