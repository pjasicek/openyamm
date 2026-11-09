"""Focused saved-project check; run with Blender on mm6_goblin.blend."""
import bpy,json
from pathlib import Path
s=bpy.context.scene
rig=next(o for o in s.objects if o.type=='ARMATURE')
mesh=next(o for o in s.objects if o.type=='MESH')
expected={'Standing','Walk','Attack','Hit','Death','Corpse','Fidget'}
assert set(a.name for a in bpy.data.actions)==expected
assert len([o for o in s.objects if o.type=='MESH'])==1
assert len(rig.data.bones)==88
images={n.image for m in mesh.data.materials for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image}
assert len(images)==3
assert all(im.packed_file for im in images)
assert rig.animation_data.action_slot
assert all(m.object==rig for m in mesh.modifiers if m.type=='ARMATURE')
report={'blender_version':bpy.app.version_string,'scene':s.name,'mesh':mesh.name,'rig':rig.name,
 'bones':len(rig.data.bones),'actions':sorted(expected),'packed_images':[im.name for im in images],
 'vertices':len(mesh.data.vertices),'triangles':sum(len(f.vertices)-2 for f in mesh.data.polygons),
 'uv_layers':[u.name for u in mesh.data.uv_layers],'action_slot_bound':True,'status':'Reopened saved delivery; all checks passed'}
(Path(__file__).resolve().parent / 'export_work/blend_reopen_report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
