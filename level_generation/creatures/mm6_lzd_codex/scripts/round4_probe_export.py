import bpy,sys,runpy,json,shutil,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P.parents[2];sys.dont_write_bytecode=True
shutil.copyfile(P/'work/round4/repaired.blend',P/'work/master.blend')
runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__')
sys.path.insert(0,str(R/'tools'))
from build_actor_lods import read_glb,write_glb
d,b=read_glb(P/'export/mm6_lzd_raw.glb');d['meshes'][0].setdefault('extras',{})['openyamm_lods']=[];write_glb(P/'export/mm6_lzd_raw.glb',d,b)
subprocess.run(['/usr/bin/python3',str(R/'tools/split_attachment.py'),str(P/'export/mm6_lzd_raw.glb'),'--joint','Bow','--body',str(P/'work/round4/probe_body.glb'),'--attachment',str(P/'work/round4/probe_bow.glb')],check=True)
