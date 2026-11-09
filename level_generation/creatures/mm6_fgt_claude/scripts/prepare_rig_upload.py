from pathlib import Path
import sys,runpy,bpy
p=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(p/'scripts'))
import common
def run(name,*args):
 sys.argv=[str(p/'scripts'/name),'--',*map(str,args)]
 runpy.run_path(sys.argv[0],run_name='__main__')
run('step1_clean.py',p/'work/st_v1_parts.blend',p/'work/step1.blend')
common.workbench_clay(bpy.context.scene)
common.render_views(str(p/'review/clean_head'),1.55,.38,views=('front','left'),resolution=(650,650))
common.render_views(str(p/'review/clean_hand'),.94,.29,views=('front','back'),target=(-.56,0),resolution=(650,650))
run('export_clean.py',p/'work/step1.blend',p/'export/clean_rest.glb')
run('source_rest.py',p.parents[2]/'anim_library/humanoid_set/Armed.glb')
run('proportions.py','source',p.parents[2]/'anim_library/humanoid_set/Armed.glb')
