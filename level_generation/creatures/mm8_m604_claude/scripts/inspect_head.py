"""Inspect the dedicated head before fitting it to the existing neck."""
from pathlib import Path
import runpy,sys,bpy
p=Path(__file__).resolve().parents[1]
s=p/'scripts/load_mesh.py';sys.argv=[str(s),'--',str(p/'meshy/head_geometry_v2/model_urls_glb.glb'),str(p/'work/head_raw.blend'),'0.36'];runpy.run_path(str(s),run_name='__main__')
sys.path.insert(0,str(p/'scripts'));import common
common.workbench_clay(bpy.context.scene)
common.render_views(str(p/'review/head_geometry_v2'),0.18,0.43,views=('front','left','back'),resolution=(500,500))

import bmesh
bm=bmesh.new();bm.from_mesh(bpy.data.objects["Body"].data);print("HEAD RAW BOUNDARY",sum(e.is_boundary for e in bm.edges));bm.free()
