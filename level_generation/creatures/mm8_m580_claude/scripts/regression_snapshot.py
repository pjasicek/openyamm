from pathlib import Path
import os,shutil,tempfile,fcntl,json,struct,hashlib
P=Path('level_generation/creatures/mm8_m580_claude').resolve();source=Path('assets_dev').resolve();target=Path(tempfile.mkdtemp(prefix='regression-fixture-',dir=P/'work'))/'assets'
with Path('assets_source/.cook-cache/install.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 shutil.copytree(source,target,copy_function=os.link,symlinks=True)
 # The manifest is edited in place by other asset work; freeze its bytes for this run.
 path=target/'worlds/mm8/models/actors.yml';data=path.read_bytes();path.unlink();path.write_bytes(data)
models=target/'worlds/mm8/models';missing=[]
for f in models.glob('*.glb'):
 raw=f.read_bytes();n=struct.unpack_from('<I',raw,12)[0];d=json.loads(raw[20:20+n])
 missing += [str(f)+':'+i['uri'] for i in d.get('images',[]) if i.get('uri') and not (f.parent/i['uri']).is_file()]
assert not missing,missing
(P/'review/regression_fixture.json').write_text(json.dumps({'asset_root':str(target),'purpose':'Freeze the installed models and their texture files while concurrent creature jobs replace production assets. Original production maps and tables are preserved.','manifest_sha256':hashlib.sha256(data).hexdigest(),'missing_mm8_model_images':missing},indent=2)+'\n')
print(target)
