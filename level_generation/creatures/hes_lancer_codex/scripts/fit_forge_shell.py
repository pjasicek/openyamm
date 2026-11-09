"""Forge-specific articulated shell clearance; retain the common atlas and the concept's exposed biceps."""
import bpy,sys,json,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];S=P/'scripts';src,out=sys.argv[sys.argv.index('--')+1:];bpy.ops.wm.open_mainfile(filepath=src)
spec=json.loads((S/'armour_lancer.json').read_text());spec['plates']=[x for x in spec['plates'] if not x['name'].startswith('shoulder_lame')]
for side in 'LR':
 ob=bpy.data.objects.get('Arm_shoulder_lame_'+side)
 if ob:bpy.data.objects.remove(ob,do_unlink=True)
for name in ('back','chest','breast_L','breast_R','abdomen_upper'):
 ob=bpy.data.objects['Arm_'+name];assert not ob.get('forge_shell_fitted'),'Rebuild the source shell before contour fitting'
 for v in ob.data.vertices:
  if name=='back':v.co.y+=.045*min(1,max(0,(1.29-v.co.z)/.12))
  elif name=='abdomen_upper':v.co.y-=.025;v.co.z-=.012
  elif v.co.z>1.42:v.co.z=1.42+(v.co.z-1.42)*.72
 if name.startswith('breast_'):
  for v in ob.data.vertices:v.co.x*=.9;v.co.y+=.018
 ob['forge_shell_fitted']=True
(S/'armour_forge.json').write_text(json.dumps(spec,indent=2)+'\n');bpy.ops.wm.save_as_mainfile(filepath=out)
sys.argv=['skin_shell.py','--',out,str(S/'armour_forge.json'),out];runpy.run_path(str(S/'skin_shell.py'),run_name='__main__')
