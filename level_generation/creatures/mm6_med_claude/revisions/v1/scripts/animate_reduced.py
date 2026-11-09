"""Rebake the authored motions on the fixed reduced mesh without changing UVs."""
from pathlib import Path
p=Path(__file__).resolve().parent
s=(p/'animate_medusa.py').read_text().replace('work/rig_v1.blend','work/anim_uv.blend').replace('work/anim_v1.blend','work/anim_uv.blend').replace('work/animation_audit.json','work/animation_audit_reduced.json')
exec(compile(s,str(p/'animate_medusa.py'),'exec'))
