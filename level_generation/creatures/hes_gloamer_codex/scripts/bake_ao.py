"""Use the shared AO bake on body and isolated head UV layouts; retain unmodified rig and UV master."""
import bpy,bmesh,sys,os,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for kind,layer in [('body','BodyUV'),('head','HeadUV')]:
    bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_uv.blend'))
    body=bpy.data.objects['Body'];me=body.data
    if kind=='head':
        bm=bmesh.new();bm.from_mesh(me);h=bm.faces.layers.int['head']
        bmesh.ops.delete(bm,geom=[f for f in bm.faces if f[h]==0],context='FACES');bm.to_mesh(me);bm.free()
    me.uv_layers.active=me.uv_layers[layer];me.uv_layers[layer].active_render=True
    bpy.context.scene.render.threads_mode='FIXED';bpy.context.scene.render.threads=4
    out=P/'texturing'/f'gloamer_{kind}_ao.png'
    sys.argv=['bake_creature_ao.py','--','Body',str(out),'0.035','1024']
    runpy.run_path(str(P.parent/'claude_shared/bake_creature_ao.py'),run_name='__main__')
sys.stdout.flush();sys.stderr.flush();os._exit(0)
