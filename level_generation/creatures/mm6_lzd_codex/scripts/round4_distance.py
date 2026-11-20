import bpy,sys,json,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
from rebake_reduce import build
from rebake_render import render
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round4/near_runtime.blend'));pieces=set(x.value for x in bpy.data.objects['Body'].data.attributes['piece'].data)
for l in [2,3]:
 budgets={i:2 for i in pieces}
 if l==2:budgets.update({1:400,2:210,3:195,4:185,6:48,7:57,8:57,9:30,10:22,11:38,12:18,13:28,14:28,15:23,16:34,17:34,19:15,20:15,21:15,22:15,23:10,200:570,201:392,202:22,203:12,204:12});budgets.update({i:6 for i in range(29,37)});budgets.update({i:4 for i in range(25,29)})
 else:budgets.update({1:120,2:56,3:67,4:65,6:15,7:16,8:16,9:6,10:6,11:22,12:6,13:11,14:11,15:8,16:10,17:10,19:6,20:6,21:6,22:6,23:6,200:155,201:116,202:12,203:12,204:12});budgets.update({i:4 for i in range(29,37)})
 print('BUDGET',l,sum(v for k,v in budgets.items()if k!=201),flush=True)
 tag=f'round4_distance{l}';path=build(tag,1,l,1,major_shells=True,source_path=P/'work/round4/near_runtime.blend',contact_poses=(('Standing',0),),piece_budgets=budgets)
 render(path,tag,l,parts=('actor',),palette=('round4_shared','lzd_a'),samples=32,camera_path=P/'review/round4/camera.json')
