"""Selected raw-export parity, frozen-motion checks, exact switch-height review, and current sheets."""
import bpy,json,runpy,sys,subprocess,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P/'review/round3'
os.environ.pop('FIGC_EXPORT_DIR',None);os.environ.pop('FIGC_VALIDATION_DIR',None);runpy.run_path(str(P/'scripts/gates_exported.py'),run_name='__main__')
# Build a split validation copy with the rebaked UVs; packed export authoring remains canonical.
bpy.ops.wm.open_mainfile(filepath=str(P/'work/export_validation.blend'));body=bpy.data.objects['Body'];me=body.data
if 'head' not in me.attributes:
 attr=me.attributes.new('head','BOOLEAN','FACE')
 for f in me.polygons:attr.data[f.index].value='Head' in me.materials[f.material_index].name
if 'HeadUV' not in me.uv_layers:
 layer=me.uv_layers.new(name='HeadUV')
 for a,b in zip(layer.data,me.uv_layers['UVMap'].data):a.uv=b.uv
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/final_motion.blend'))
for script in ['export_parity.py','motion_trace.py','blade_gate.py','grip_preservation_r3.py']:
 runpy.run_path(str(P/'scripts'/script),run_name='__main__')
runpy.run_path(str(P/'scripts/render_final.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/render_props_r3.py'),run_name='__main__')
