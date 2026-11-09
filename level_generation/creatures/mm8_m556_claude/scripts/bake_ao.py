"""Bake the corrected neutral body only; props retain their own material atlas."""
from pathlib import Path
import bpy,bmesh,sys,runpy
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_uv.blend'));m=bpy.data.objects['Wasp']
bm=bmesh.new();bm.from_mesh(m.data);bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index==1],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(m.data);bm.free()
sys.argv=['bake_creature_ao.py','--','Wasp',str(P/'textures/m556_ao.png'),'.025','1024']
runpy.run_path(str(P.parent/'claude_shared/bake_creature_ao.py'),run_name='__main__')
