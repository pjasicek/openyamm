"""The broad strapped bib replaces the old small chest shell."""
import bpy,sys,os,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/forge_motion_fit.blend'))
bpy.data.objects.remove(bpy.data.objects['Arm_chest'],do_unlink=True)
spec=json.loads((P/'scripts/armour_forge.json').read_text())
chest=next(i+1 for i,p in enumerate(spec['plates']) if p['name']=='chest')
body=bpy.data.objects['Body'];pieces=body.data.attributes['piece'].data
# Keep the original cull of the loose ornament under the solid bib; restore the skin.
for index,value in enumerate(body.data.attributes['shell_hidden'].data):
 if value.value==chest and pieces[index].value!=1:value.value=0
path=P/'scripts/armour_forge_concept.json';spec=json.loads(path.read_text())
spec['plates']=[p for p in spec['plates'] if p['name']!='chest'];path.write_text(json.dumps(spec,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/forge_chest_fit.blend'))
sys.stdout.flush();os._exit(0)
