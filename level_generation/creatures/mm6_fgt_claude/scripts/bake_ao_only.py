from pathlib import Path
import bpy,bmesh,sys,runpy
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_textured.blend'))
body=bpy.data.objects['Body'];head=body.copy();head.data=body.data.copy();bpy.context.scene.collection.objects.link(head)
for ob,keep in ((body,0),(head,1)):
 bm=bmesh.new();bm.from_mesh(ob.data);hl=bm.faces.layers.int['head']
 bmesh.ops.delete(bm,geom=[f for f in bm.faces if f[hl]!=keep],context='FACES');bm.to_mesh(ob.data);bm.free()
body.data.uv_layers.active=body.data.uv_layers['UVMap']
sys.argv=['bake','--','Body',str(p/'work/ao_body.png'),'0.03','1024']
runpy.run_path(str(p.parent/'claude_shared/bake_creature_ao.py'),run_name='__main__')
