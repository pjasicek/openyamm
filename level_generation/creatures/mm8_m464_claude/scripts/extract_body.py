import bpy, json, sys, numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'mm6_mfp_codex/scripts'))
import common
bpy.ops.wm.open_mainfile(filepath=str(P.parent/'mm6_mfp_codex/export/mm6_mfp.blend'))
r=bpy.data.objects['Rig']; b=bpy.data.objects['Body']; r.animation_data.action=None
for pb in r.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
info={'objects':[(o.name,o.type)for o in bpy.data.objects],'actions':{a.name:list(a.frame_range)for a in bpy.data.actions},'fps':bpy.context.scene.render.fps,'bones':{x.name:{'head':list(x.head_local),'tail':list(x.tail_local)}for x in r.data.bones},'attributes':[(x.name,x.domain)for x in b.data.attributes]}
co=np.array([v.co[:]for v in b.data.vertices]);pv=np.array([v.value for v in b.data.attributes['piece'].data]);info['parts']={str(i):{'verts':int((pv==i).sum()),'lo':co[pv==i].min(0).tolist(),'hi':co[pv==i].max(0).tolist()}for i in np.unique(pv)}
(P/'review/source_inspection.json').write_text(json.dumps(info,indent=2))
for o in list(bpy.data.objects):
 if o not in (b,r):bpy.data.objects.remove(o,do_unlink=True)
import bmesh
bm=bmesh.new();bm.from_mesh(b.data);pieces=bm.verts.layers.int['piece'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[pieces]not in [0,4,5,8,9,15]],context='VERTS');bm.to_mesh(b.data);bm.free()
common.workbench_clay(bpy.context.scene);bpy.context.scene.display.shading.color_type='SINGLE';bpy.context.scene.display.shading.single_color=(.65,.68,.7)
common.render_views(str(P/'review/source_body'),.84,1.85,views=('front','left','back'),resolution=(650,900))
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/source_body.blend'))
