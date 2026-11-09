"""Print actions, bones and body sizes of the monk blends (gait2 rework)."""
import bpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
for f in ['work/animation_finish.blend','export/mm6_mnk1.blend','work/review4_lod1.blend']:
 bpy.ops.wm.open_mainfile(filepath=str(p/f))
 r=bpy.data.objects.get('Rig');objs=[(o.name,o.type,len(o.data.polygons) if o.type=='MESH' else 0) for o in bpy.data.objects]
 print('BLEND',f,objs,'bones',len(r.data.bones),'fps',bpy.context.scene.render.fps)
 print(' ACTIONS',[(a.name,tuple(a.frame_range)) for a in bpy.data.actions])
 print(' BONES',[b.name for b in r.data.bones])
 b=next(o for o in bpy.data.objects if o.type=='MESH');print(' ATTRS',[a.name for a in b.data.attributes])
