"""World-space fitted props; bind_attachment.py applies the runtime glTF inverse bind, once."""
import bpy,sys,os
from pathlib import Path
from mathutils import Matrix
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/male/runtime_ragged.blend'));rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
out=P/'work/props_fitted_world';out.mkdir(exist_ok=True)
for part in ('collar','pick','club','plate'):
 src=bpy.data.objects['hes_kept_'+part];o=src.copy();o.data=src.data.copy();bpy.context.scene.collection.objects.link(o)
 for m in list(o.modifiers):o.modifiers.remove(m)
 o.vertex_groups.clear();o.parent=None;o.matrix_world=Matrix.Identity(4)
 for x in bpy.data.objects:x.select_set(x==o)
 bpy.context.view_layer.objects.active=o;bpy.ops.export_scene.gltf(filepath=str(out/f'{part}.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_skins=False,export_extras=True);bpy.data.objects.remove(o,do_unlink=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
