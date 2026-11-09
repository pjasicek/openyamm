"""Fit only the Hit recovery (after frame 9) into the native 0.75 seconds."""
import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def fit_hit():
    a=bpy.data.actions['Hit']
    end=float(a.frame_range[1])
    if abs(end-22.5)<1e-4:return
    assert abs(end-23)<1e-4,end
    for layer in a.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:
                        for point in (key.co,key.handle_left,key.handle_right):
                            if point.x>9:point.x=9+(point.x-9)*13.5/14
    a.use_frame_range=True;a.frame_start=0;a.frame_end=22.5
    assert abs(a.frame_range[1]/30-.75)<1e-6
if __name__=='__main__':
    for name in ('rig_final','rig_uv_head','rig_uv_body','textured_uv'):
        path=P/f'work/{name}.blend';bpy.ops.wm.open_mainfile(filepath=str(path))
        fit_hit();bpy.ops.wm.save_as_mainfile(filepath=str(path))
    p=P/'work/final_rig.json';d=json.loads(p.read_text());d['clips']['Hit']=.75;p.write_text(json.dumps(d,indent=2)+'\n')
