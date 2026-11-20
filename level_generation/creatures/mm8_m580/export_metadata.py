"""Export standalone native animation and palette documents from the accepted manifest."""
import json
from process import ROOT,save,queue
def run():
 m=json.loads((ROOT/'manifest.json').read_text());assert m['status']=='validated'
 save(ROOT/'animations.json',{'schema_version':1,'creature':m['creature'],'animations':m['animations']})
 save(ROOT/'variants.json',{'schema_version':1,'creature':m['creature'],'variants':m['variants']})
 acceptance=json.loads((ROOT/'review/acceptance.json').read_text())
 for p in ['animations.json','variants.json','export_metadata.py']:acceptance['artifact_hashes'][p]=queue.sha(ROOT/p)
 save(ROOT/'review/acceptance.json',acceptance)
 print('Standalone metadata exactly mirrors the accepted manifest and is hash sealed.')
if __name__=='__main__':run()
