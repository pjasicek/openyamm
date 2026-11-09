from pathlib import Path
import runpy,sys,json,bpy
p=Path(__file__).resolve().parents[1]
def run(name,*args):
 s=p/'scripts'/name;sys.argv=[str(s),'--',*map(str,args)];runpy.run_path(str(s),run_name='__main__')
run('finish_geometry.py')
run('reduce_rigged.py',p/'work/rig_gated.blend',p/'work/rig_reduced.blend')
(p/'work/bone_map.json').write_text(json.dumps({b.name:b.name for b in bpy.data.objects['Rig'].data.bones}))
run('proportions.py','target',p/'work/rig_reduced.blend','Rig','Body',p/'work/bone_map.json')
run('export_uploads.py')
runpy.run_path(str(p/'scripts/check_deformation.py'),init_globals={'INPUT_BLEND':'rig_reduced.blend','CLIPS':['Running']},run_name='__main__')
