"""Dense surface/contact gates and reimport parity for the animated twelve-fish school."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector,kdtree
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];FPS=48
info=json.loads((P/'export/export_info.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(P/'export/m636_master.blend'));sc=bpy.context.scene;sc.render.fps=FPS
rig=bpy.data.objects['SchoolRig'];obj=bpy.data.objects['School']
def activate(rig,a,t):
    rig.animation_data.action=a
    if len(a.slots):rig.animation_data.action_slot=a.slots[0]
    f=t*FPS;sc.frame_set(int(f),subframe=f-int(f));bpy.context.view_layer.update()
def vertices(ob):
    ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    co=[tuple(ob.matrix_world@v.co) for v in me.vertices];ev.to_mesh_clear();return co
owners=[int(obj.vertex_groups[max(v.groups,key=lambda g:g.weight).group].name[4:6]) for v in obj.data.vertices]
polys=[[tuple(p.vertices) for p in obj.data.polygons if owners[p.vertices[0]]==i] for i in range(12)]
source={};report={};times={}
for name,duration in info['clips'].items():
    a=bpy.data.actions[name];ts=[duration*i/8 for i in range(9)];times[name]=ts
    for t in ts:
        activate(rig,a,t);source[name,t]=vertices(obj)
    worststep=0;previous=None;minz=10;overlaps=0
    for i in range(round(duration*FPS*2)+1):
        activate(rig,a,i/(FPS*2));current={b.name:b.matrix.to_quaternion() for b in rig.pose.bones}
        assert all(math.isfinite(c) for b in rig.pose.bones for row in b.matrix for c in row)
        if previous:worststep=max(worststep,max(2*math.acos(min(1,abs(q.dot(previous[k])))) for k,q in current.items()))
        previous=current;points=vertices(obj);minz=min(minz,min(p[2] for p in points))
        if i%4==0:
            trees=[BVHTree.FromPolygons(points,faces,all_triangles=True) for faces in polys]
            overlaps+=sum(len(trees[j].overlap(trees[k])) for j in range(12) for k in range(j))
    assert worststep<math.radians(15),(name,'rotation jump',math.degrees(worststep))
    assert minz>=0,(name,'ground intersection',minz)
    assert overlaps==0,(name,'fish intersections',overlaps)
    report[name]={'max_rotation_step_degrees_96hz':math.degrees(worststep),'dense_samples':round(duration*96)+1,
                  'minimum_height_m':minz,'interfish_triangle_contacts_24hz':overlaps}
    if name in ('Swim','Dead'):
        error=max((Vector(a)-Vector(b)).length for a,b in zip(source[name,0],source[name,duration]))
        assert error<.00015,(name,'loop seam',error);report[name]['loop_surface_error_m']=error
error=max((Vector(a)-Vector(b)).length for a,b in zip(source['Death',1.25],source['Dead',0]))
assert error<.00015;report['death_dead_endpoint_error_m']=error
bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene;sc.render.fps=FPS
bpy.ops.import_scene.gltf(filepath=str(P/'export/mm8_m636.glb'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');obj=bpy.data.objects['School']
for name,ts in times.items():
    a=next(a for a in bpy.data.actions if a.name==name or a.name.startswith(name+'_'));errors=[]
    for t in ts:
        activate(rig,a,t);before=source[name,t];after=vertices(obj);tree=kdtree.KDTree(len(before))
        for i,c in enumerate(before):tree.insert(Vector(c),i)
        tree.balance();errors.append(max(tree.find(Vector(c))[2] for c in after))
    report[name]['max_export_error_mm']=max(errors)*1000;assert max(errors)<.0002,(name,'export drift',max(errors))
(P/'work/motion_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('MOTION AUDIT',report,flush=True)
