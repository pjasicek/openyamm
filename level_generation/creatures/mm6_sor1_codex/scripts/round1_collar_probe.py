"""Inspect the collar layers independently before changing their seam."""
import bpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'review/round1/baseline/work/production_master.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];scene.frame_set(0)
common.workbench_clay(scene,textured=True)
pieces=body.data.attributes['piece'].data
for part in [1,2]:
 copy=body.copy();copy.data=body.data.copy();scene.collection.objects.link(copy);copy.hide_render=False
 import bmesh
 bm=bmesh.new();bm.from_mesh(copy.data);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[v for v in bm.verts if pieces[v.index].value!=part],context='VERTS');bm.to_mesh(copy.data);bm.free()
 body.hide_render=True
 common.render_views(str(p/'review/round1'/('collar_layer_'+str(part))),1.40,.42,views=('front','three_quarter'),resolution=(600,600))
 bpy.data.objects.remove(copy,do_unlink=True)
