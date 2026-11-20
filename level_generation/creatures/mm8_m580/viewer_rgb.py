"""Offline-only straight-RGB companions avoid Canvas alpha quantization before recoloring."""
import json
from PIL import Image
from process import ROOT
def run():
 m=json.loads((ROOT/'draft_manifest.json').read_text());s=json.loads((ROOT/'sources.json').read_text())
 (ROOT/'viewer_rgb').mkdir(exist_ok=True)
 for p in m['pages']:Image.open(ROOT/p['base']).convert('RGB').save(ROOT/p['base'].replace('atlas/','viewer_rgb/'))
 (ROOT/'viewer.html').write_text((ROOT/'viewer_template.html').read_text().replace('__DATA__',json.dumps({'manifest':m,'sources':s['sources']})))
 print('Offline straight-RGB companions and viewer rebuilt; runtime atlases unchanged.')
if __name__=='__main__':run()
