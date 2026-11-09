from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
sys.argv=[str(p/'scripts/step1_clean.py'),'--',str(p/'work/st_v1_parts.blend'),str(p/'work/step1.blend')]
runpy.run_path(sys.argv[0],run_name='__main__')
for name in ('build_rig.py','g4_animate.py','build_native_prop.py','g6_audit.py'):
 runpy.run_path(str(p/'scripts'/name),run_name='__main__')

runpy.run_path(str(p/'scripts/g7_export.py'),run_name='__main__')
