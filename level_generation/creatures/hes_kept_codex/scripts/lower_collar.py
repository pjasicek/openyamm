"""Place the collar below the jaw hinge; retain its fitted neck motion."""
import bpy,sys,os,json
from pathlib import Path
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1];path=P/'work/male/runtime_ragged.blend';bpy.ops.wm.open_mainfile(filepath=str(path));rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
o=bpy.data.objects['hes_kept_collar'];offset=float(sys.argv[sys.argv.index('--')+1]);o.data.transform(Matrix.Translation((0,0,offset)))
factor=float(sys.argv[sys.argv.index('--')+2]) if len(sys.argv)>sys.argv.index('--')+2 else 1.0
centre=Vector((-.03255327,.02501907,1.46521306));o.data.transform(Matrix.Translation(centre)@Matrix.Diagonal((1,1,factor,1))@Matrix.Translation(-centre))
ob=o.copy();ob.data=o.data.copy();bpy.context.scene.collection.objects.link(ob)
for m in list(ob.modifiers):ob.modifiers.remove(m)
ob.vertex_groups.clear();ob.data.transform(rig.data.bones['Kept_Collar'].matrix_local.inverted());ob.parent=None;ob.matrix_world=Matrix.Identity(4)
for obj in bpy.data.objects:obj.select_set(obj==ob)
bpy.context.view_layer.objects.active=ob;bpy.ops.export_scene.gltf(filepath=str(P/'export/hes_kept_collar.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_skins=False,export_extras=True)
bpy.data.objects.remove(ob,do_unlink=True);bpy.ops.wm.save_as_mainfile(filepath=str(path));p=P/'review/attachments.json';d=json.loads(p.read_text());d['collar']['jaw_clearance_lowering_m']=d['collar'].get('jaw_clearance_lowering_m',0)+offset;d['collar']['band_height_scale']=d['collar'].get('band_height_scale',1)*factor;p.write_text(json.dumps(d,indent=2)+'\n');sys.stdout.flush();sys.stderr.flush();os._exit(0)
