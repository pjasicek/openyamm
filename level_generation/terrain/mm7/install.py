"""Install reviewed terrain alongside MM7 originals; preserve all other world content and settings."""
import json,shutil
from common import *
def snapshot():
 root=ROOT/'assets_dev/worlds/mm7'
 return {str(p.relative_to(root)):sha(p) for p in root.rglob('*') if p.is_file() and 'terrain_x2' not in p.relative_to(root).parts}
def main():
 manifest=json.loads((P/'runtime_x2/manifest.json').read_text());review=json.loads((P/'reports/review.json').read_text());validation=json.loads((P/'reports/validation.json').read_text())
 assert not validation['failures'];assert review['water_animation_passed'] and review['mm6_checkpoint_unchanged']
 before=snapshot();settings=sha(ROOT/'settings.ini');target=ROOT/'assets_dev/worlds/mm7/terrain_x2';assert not target.is_symlink()
 previous={p.name:sha(p) for p in target.glob('*') if p.is_file()};target.mkdir(exist_ok=True)
 owned=json.loads((target/'manifest.json').read_text())['files'] if (target/'manifest.json').exists() else {}
 for name,h in manifest['files'].items():
  source=P/'runtime_x2'/name;dest=ROOT/'assets_dev'/name
  assert sha(source)==h==review['files'][source.name]
  if dest.exists() and sha(dest)!=h and sha(dest)!=owned.get(name):
   raise RuntimeError('Conflicting existing terrain file outside the installed manifest: '+str(dest))
 for name in manifest['files']:shutil.copy2(P/'runtime_x2'/name,ROOT/'assets_dev'/name)
 shutil.copy2(P/'runtime_x2/manifest.json',target/'manifest.json')
 assert before==snapshot() and settings==sha(ROOT/'settings.ini')
 assert all(sha(ROOT/'assets_dev'/n)==h for n,h in manifest['files'].items())
 report=dict(installed_directory=str(target.relative_to(ROOT)),installed_pngs=len(manifest['files']),preserved_other_world_files=len(before),settings_unchanged=True,other_world_content_unchanged=True,previous_files=previous,installed_files=manifest['files'],manifest_sha256=sha(P/'runtime_x2/manifest.json'),review_sha256=sha(P/'reports/review.json'))
 (P/'reports/integration.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k not in ('previous_files','installed_files')})
if __name__=='__main__':main()
