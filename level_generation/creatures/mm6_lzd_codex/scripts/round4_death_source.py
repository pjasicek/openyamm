import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
sys.argv=['retarget_mixamo','--',str(P/'work/round4/sources.blend'),str(P/'work/round4/sources_death.blend'),str(P.parents[2]/'anim_library/mixamo/packs/Pro Longbow Pack/standing death backward 01.fbx')+':SourceDeath']
runpy.run_path(str(P/'scripts/retarget_mixamo.py'),run_name='__main__')
