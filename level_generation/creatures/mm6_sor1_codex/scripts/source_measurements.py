import sys,runpy,json
from pathlib import Path
p=Path(__file__).resolve().parents[1];root=p.parents[2];lib=root/'anim_library/humanoid_set'
roles=json.loads((p/'source/clips.json').read_text())
sys.argv=['rom_extract.py','--',*[f'{role}={lib/(group+".glb")}:{clip}' for role,(group,clip) in roles.items()]]
runpy.run_path(str(p/'scripts/rom_extract.py'),run_name='__main__')
sys.argv=['source_rest.py','--',str(lib/'Relax.glb')]
runpy.run_path(str(p/'scripts/source_rest.py'),run_name='__main__')
