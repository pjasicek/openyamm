from pathlib import Path
P=Path(__file__).resolve().parents[1]
exec((P/'scripts/render_final.py').read_text().split("O=P/'review/final_frames'")[0])
for role,t in [('Standing',0),('Running',.2),('Death',1.2)]:
 a=next(a for a in bpy.data.actions if a.name.split('@')[-1].split('|')[-1]==role);rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];f=t*s.render.fps;s.frame_set(int(f),subframe=f%1)
 lo,hi=common.world_bounds(meshes);mid=(lo+hi)*.5;print('BOUNDS',role,list(lo),list(hi),[(o.name,list(o.location),o.hide_render)for o in meshes],flush=True)
 common.render_views(str(P/'review'/f'review1_preview_{role}'),mid.z,2.05,views=('front','left','right','three_quarter'),target=(mid.x,mid.y),resolution=(700,900))
