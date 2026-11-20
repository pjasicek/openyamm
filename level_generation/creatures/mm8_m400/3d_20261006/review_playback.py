import json,struct,subprocess,threading,hashlib,os
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[3]
model=ROOT/os.environ.get('LIZARD_REVIEW_MODEL','delivery/mm8_lizardman_villager_a.glb')
output=ROOT/os.environ.get('LIZARD_REVIEW_OUTPUT','final_playback_v2')
raw=model.read_bytes();data=json.loads(raw[20:20+struct.unpack_from('<I',raw,12)[0]])
native=json.loads((ROOT/'native_motion.json').read_text())['descriptor']['actions']
names={'Standing':'standing','Walk':'walk','Hit':'hit','Fidget':'fidget','Death':'death','Corpse':'corpse'}
restored=REPO/'level_generation/creatures/mm7_mm8_packed_outline/session_mm8_01/mm8_m400/redo_2x/runtime_aligned_2x'
def url(path):return '/'+str(path.relative_to(REPO))
clips={}
for a in data.get('animations',[]):
    if a['name'] not in names:continue
    name=a['name'];action=native[names[name]];frames=action['views']['0'];time=0;anchors=[]
    for i,f in enumerate(frames):
        anchors.append({'label':f['frame'],'time':time,'phase':'Native gait context; preset phases do not claim bitmap correspondence' if name=='Walk' else f'Native source {i+1}; authored interpolation between observations','source_images':[url(restored/(action['views'][str(v)][i]['frame']+'.png')) for v in range(5)]});time+=f['duration_ms']/1000
    duration=max(data['accessors'][s['input']]['max'][0] for s in a['samplers'])
    clips[name]={'label':name,'duration':duration,'mode':'hold' if name in ('Standing','Corpse') else 'loop' if name=='Walk' else 'once','provenance':'Meshy walking preset, corrected attachments/feet, retimed to native 0.875 s.' if name=='Walk' else 'Authored on retained corrected rig from native action observations. Held states remain held.','anchors':anchors}
manifest={'revision':model.name,'model':url(model),'model_sha256':hashlib.sha256(raw).hexdigest(),'default_clip':'Standing','clips':clips,'feedback':'/lizard_feedback.json'}
manifest['models']=[{'id':'mm8_m400_a','label':'MM8 lizardman villager A','revision':model.name,'url':url(model),'sha256':manifest['model_sha256']}]
manifest['default_model']='mm8_m400_a'
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(REPO),**kwargs)
    def log_message(self,*args):pass
    def do_GET(self):
        if self.path.endswith('/manifest.json') or self.path=='/lizard_feedback.json':
            payload=json.dumps(manifest if self.path.endswith('/manifest.json') else {'findings':[]}).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)
        else:super().do_GET()
server=ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
try:
    base=f'http://127.0.0.1:{server.server_port}/level_generation/creatures/mm6_goblin/review_20261006/'
    subprocess.run(['node',str(ROOT/'review_playback.mjs'),base,str(output)],check=True)
finally:server.shutdown();server.server_close()
