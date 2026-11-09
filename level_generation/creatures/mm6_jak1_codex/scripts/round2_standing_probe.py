import bpy,runpy,os,sys,json,math,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));os.environ['ROUND2_PROBE']='1'
runpy.run_path(str(P/'scripts/animate_staff.py'),run_name='__main__')
rig=bpy.data.objects['Rig'];rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];bpy.context.scene.frame_set(0)
import common
common.workbench_clay(bpy.context.scene)
common.render_views(str(P/'review/round2/standing_probe'),.95,2.5,views=('front','left','three_quarter'),resolution=(600,800))
print('PROBE',json.loads((P/'work/ik_report.json').read_text()),flush=True)
