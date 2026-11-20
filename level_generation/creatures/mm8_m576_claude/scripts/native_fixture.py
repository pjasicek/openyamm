from pathlib import Path
import hashlib,json,yaml
source=Path('/home/pjasicek/github/OpenYAMM/assets_dev');target=Path('/tmp/openyamm-m576-native-assets');target.mkdir(exist_ok=True)
override=Path('engine/rendering/sprite_frame_data_common.yml')
def mount(src,dst,rel=Path()):
 for entry in src.iterdir():
  name=rel/entry.name;out=dst/entry.name
  if name==override:continue
  if name in override.parents:
   out.mkdir(exist_ok=True);mount(entry,out,name)
  elif not out.exists() and not out.is_symlink():out.symlink_to(entry,target_is_directory=entry.is_dir())
mount(source,target)
text=(source/override).read_text();records=[]
for n in (577,578,579):
 p=source/f'engine/rendering/sprite_frames/monsters/m{n}.yml';s=p.read_text();text+='\n'+s.split('sprites:\n',1)[1];records.append({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
d=yaml.safe_load(text);ids=[r['sprite_id'] for r in d['sprites']];assert len(ids)==len(set(ids))
(target/override).write_text(text)
(target/'fixture.json').write_text(json.dumps({'kind':'isolated native sprite preload fixture','source_files':records,'change':'Unchanged m577/m578/m579 family definitions appended to the common table for indoor comparison only. All other assets linked to ordinary development mount.'},indent=2))
print(target)
