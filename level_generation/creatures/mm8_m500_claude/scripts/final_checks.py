import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
runpy.run_path(str(p/'scripts/export_parity.py'),run_name='__main__')
f=p/'scripts/uv_gate.py';s=f.read_text().replace('work/anim_uv.blend','work/anim_uv_brow.blend').replace('work/uv_gate.json','work/uv_gate_final.json');exec(compile(s,str(f),'exec'),{'__file__':str(f),'__name__':'__main__'})
runpy.run_path(str(p/'scripts/preview_caster.py'),run_name='__main__')
