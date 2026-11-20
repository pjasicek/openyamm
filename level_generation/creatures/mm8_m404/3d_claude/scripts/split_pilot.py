import sys,subprocess
from pathlib import Path
p=Path(__file__).resolve().parents[1];repo=Path.cwd();sys.path.insert(0,str(repo/'tools'))
from merge_head_material import read_glb,write_glb
prefix=sys.argv[1] if len(sys.argv)>1 else 'pilot'
doc,binary=read_glb(p/('export/'+prefix+'_combined.glb'));assert len(doc['meshes'])==1
doc['meshes'][0].setdefault('extras',{})['openyamm_lods']=[];write_glb(p/('export/'+prefix+'_combined.glb'),doc,binary)
subprocess.run(['python3','tools/split_attachment.py',str(p/('export/'+prefix+'_combined.glb')),'--joint','Socket_Sword','--body',str(p/('export/'+prefix+'_body.glb')),'--attachment',str(p/('export/'+prefix+'_sword.glb'))],check=True)
