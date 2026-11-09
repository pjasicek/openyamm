"""Rebake selected motions on the textured master, preserving its fitted mesh and UVs."""
from pathlib import Path
p=Path(__file__).resolve().parent
s=(p/'animate_medusa.py').read_text().replace('work/rig_v1.blend','revisions/v1/work/textured_master.blend').replace('work/anim_v1.blend','work/motion_v4.blend').replace('work/animation_audit.json','work/animation_audit_v4.json')
exec(compile(s,str(p/'animate_medusa.py'),'exec'))
