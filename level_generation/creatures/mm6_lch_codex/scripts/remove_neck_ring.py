"""Remove the confirmed obsolete body-neck collar P13 after texture UV transfer; paid layouts stay fixed."""
import bpy,bmesh,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import common
for name in ['rig_reduced','rig_uv','rig_textured']:
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/{name}.blend'));ob=bpy.data.objects['Body'];bm=bmesh.new();bm.from_mesh(ob.data);piece=bm.verts.layers.int['piece']
 verts=[v for v in bm.verts if v[piece]==13];print('DELETE obsolete collar',name,len(verts));bmesh.ops.delete(bm,geom=verts,context='VERTS');bm.to_mesh(ob.data);bm.free()
 bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/{name}.blend'))
