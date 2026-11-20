"""Install the reviewed complete pack; audit all other playtest content."""
import hashlib,json,os,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=P.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inventory(stage,targets):
    result={}
    for directory,dirs,files in os.walk(stage,followlinks=False):
        base=Path(directory)
        if base==stage:dirs[:]=[d for d in dirs if d!='seed']
        for name in dirs+files:
            p=base/name;relative=str(p.relative_to(stage))
            if relative in targets or relative=='playtest_snapshot.json':continue
            if p.is_symlink():result[relative]={'symlink':os.readlink(p)}
            elif p.is_file():result[relative]=sha(p)
    return result

def main():
    stage=Path(os.environ.get('OPENYAMM_SORPIGAL_PEASANTS_DEMO','/tmp/openyamm-sorpigal-peasants-playtest')).resolve()
    manifest=json.loads((P/'runtime_x2/manifest.json').read_text())
    targets={'enhanced/assets_dev/'+n for n in manifest['files']}
    before=inventory(stage,targets)
    snapshot=json.loads((stage/'playtest_snapshot.json').read_text())
    previous={n:sha(stage/'enhanced/assets_dev'/n) for n in manifest['files'] if (stage/'enhanced/assets_dev'/n).exists()}
    subprocess.run(['python3',str(ROOT/'level_generation/creatures/mm6_peasants/prepare_playtest.py'),'--directory',str(stage),'--terrain-only'],cwd=ROOT,check=True)
    after=inventory(stage,targets)
    assert before==after,'Non-terrain file content changed during installation'
    current=json.loads((stage/'playtest_snapshot.json').read_text())
    for k in snapshot:
        if k not in ('terrain','water'):assert current[k]==snapshot[k],k
    for n,h in manifest['files'].items():assert sha(stage/'enhanced/assets_dev'/n)==h,n
    added=sorted(set(manifest['files'])-set(previous))
    changed=[n for n,h in previous.items() if manifest['files'][n]!=h]
    report=dict(passed=True,stage=str(stage),installed_files=manifest['files'],added_files=added,changed_existing_files=changed,protected_entry_count=len(before),protected_entries=before,other_snapshot_sections_unchanged=True,note='Only terrain PNGs, terrain/water snapshot metadata and seed backups are permitted to change. Saves, maps, settings, executable, sprites, decorations and other artwork are audited unchanged.')
    (P/'reports/integration.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Installed',len(manifest['files']),'textures;',len(added),'added;',len(changed),'existing changed;',len(before),'other entries preserved.')
if __name__=='__main__':main()
