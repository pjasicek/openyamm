from pathlib import Path
import runpy,sys
P=Path(__file__).resolve().parents[1]
a=sys.argv[sys.argv.index('--')+1:];stem,step=a
sys.argv=['lod_render.py','--',str(P/'work/lod_repair'/stem/'audit'),'installed,'+step]
runpy.run_path(str(P.with_name('lod_repair_claude')/'scripts/lod_render.py'),run_name='__main__')
