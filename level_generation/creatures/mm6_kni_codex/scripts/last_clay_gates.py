import os,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P)
def run(n,args=[]):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('g6_skirt_poke.py',['work/production_body.blend','Standing','Walking','Running','Attack','Hit','Death','Fidget'])
run('texture_upload.py')
