import bpy,sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;config=json.loads((P/'work/round5/config.json').read_text());step=config['step'];blend=f'work/round5/baked{step}/candidate.blend'
path=P/'scripts/round4_export.py';s=path.read_text();s=s[:s.index("write_glb(P/'export/mm6_dwa1_runtime_lod0.glb'")]+"write_glb(P/'work/round5/pilot.glb',single,binary)\n"
s=s.replace("W=P/'work/round4';R=P/'review/round4'","W=P/'work/round5';R=P/'review/round5'").replace("selection=json.loads((R/'selection.json').read_text())",f"selection={{'body':[{{'blend':{blend!r}}}],'axe':[{{'blend':{blend!r}}}]}}").replace('range(4)','range(1)')
a=s.index(" bpy.data.objects.remove(bpy.data.objects['Axe'],do_unlink=True)");b=s.index(' for mod in axe.modifiers:',a)
s=s[:a]+" axe=bpy.data.objects['Axe']\n"+s[b:]
exec(compile(s,str(path),'exec'),{'__file__':str(path),'__name__':'__main__'})
path=P/'scripts/import_final.py';s=path.read_text().replace("P/'work/textured_master.blend'",f'P/{blend!r}').replace("P/'export/mm6_dwa1_runtime_lod0.glb'","P/'work/round5/pilot.glb'").replace("P/'work/export_reimport.blend'","P/'work/round5/pilot_reimport.blend'");exec(compile(s,str(path),'exec'),{'__file__':str(path),'__name__':'__main__'})
path=P/'scripts/g4_weights.py';sys.argv=[str(path),'--',str(P/'work/round5/pilot_reimport.blend'),'round5_pilot','Death:7.5','Death:8.0','Death:8.5'];exec(compile(path.read_text(),str(path),'exec'),{'__file__':str(path),'__name__':'__main__'})
