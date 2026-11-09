"""Use shared pose sampler and viewer tools to document the timing-only revision."""
import functools
import hashlib
import http.server
import json
import os
import signal
import subprocess
import sys
import threading
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.dont_write_bytecode = True
P = Path(__file__).resolve().parents[1]
ROOT = P.parents[2]
R = P / 'review/round3'
sys.path.insert(0, str(P.parent / 'claude_shared/gates'))
import run_gates as G
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def write(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')
old = G.Glb(P / 'work/round3/before/export/mm6_mfp.glb')
new = G.Glb(P / 'export/mm6_mfp.glb')
oc = {n:c for n,c,*_ in old.clips()}
nc = {n:c for n,c,*_ in new.clips()}
times = np.unique(np.r_[np.linspace(0,143/48,1431),100/48])
new_times = (np.minimum(times,100/48)+np.maximum(times-100/48,0)/1.5)/1.25
before = old.pose(oc['Death'], times)
after = new.pose(nc['Death'], new_times)
delta = float(np.max(np.abs(before-after)))
positions = float(np.max(np.linalg.norm(before[:,:,:3,3]-after[:,:,:3,3],axis=-1)))
endpoint = float(np.max(np.abs(old.pose(oc['Death'],np.array([3.]))-new.pose(nc['Death'],np.array([3.])))))
others = {}
for name,clip,start,end in old.clips():
    if name != 'Death':
        t = np.linspace(start,end,49)
        others[name] = float(np.max(np.abs(old.pose(clip,t)-new.pose(nc[name],t))))
assert delta < 1e-5 and endpoint == 0 and all(v == 0 for v in others.values())
motion = {'sampler':'Unmodified claude_shared/gates/run_gates.Glb.pose',
          'before_sha256':sha(P/'work/round3/before/export/mm6_mfp.glb'),
          'after_sha256':sha(P/'export/mm6_mfp.glb'), 'sample_count':len(times),
          'all_node_matrix_max_delta':delta, 'all_node_position_max_delta_m':positions,
          'final_corpse_matrix_max_delta':endpoint, 'other_clips_matrix_max_delta':others,
          'old_duration_s':143/48, 'new_duration_s':193/90,
          'method':'Exact piecewise timestamp remap; all 716 dense pose samples retained. Sparse tracks gain an interpolated boundary key. Float32 quantization only.'}
write(R/'motion_preservation.json',motion)
print(json.dumps(motion,indent=2),flush=True)

# Use the established shared binding and viewer checker without duplicating gate code.
validate = (P/'scripts/round2_validate.py').read_text().replace("R=P/'review/round2'", "R=P/'review/round3'")
exec(compile(validate, str(P/'scripts/round2_validate.py'), 'exec'), {'__file__':str(P/'scripts/round2_validate.py')})

class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args):
        pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
proc=None
try:
    url=f'http://127.0.0.1:{server.server_port}/level_generation/creatures/mm6_mfp_codex/review/viewer/'
    proc=subprocess.Popen(['node',str(P/'scripts/round2_capture.mjs'),url,str(R),str(R/'capture_death.json')],start_new_session=True)
    assert proc.wait(timeout=180)==0
finally:
    server.shutdown()
    server.server_close()
    if proc:
        try:os.killpg(proc.pid,signal.SIGTERM)
        except ProcessLookupError:pass

plan=json.loads((R/'capture_death.json').read_text())
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
out=Image.new('RGB',(2160,1098),(31,34,39))
draw=ImageDraw.Draw(out)
draw.text((15,12),'Review round 3 — Death 2.979167 → 2.144444 s — unchanged poses',font=font,fill='white')
for row in plan:
    name,clip,time,*_=row
    label=name.rsplit('/',1)[-1]
    i=int(label[:2]);view=label[3:]
    j=['front','left','three_quarter'].index(view)
    im=Image.open(R/(name+'.png')).convert('RGB')
    im.thumbnail((352,316),Image.Resampling.LANCZOS)
    out.paste(im,(i*360+(360-im.width)//2,j*350+48))
    draw.text((i*360+8,j*350+371),f'{view} | {time:.4f} s',font=small,fill='white')
out.save(R/'Death.png')
out.save(P/'review/sheets/Death.png')
write(R/'capture_receipt.json',{'runtime_sha256':sha(P/'export/mm6_mfp.glb'),
                              'viewer_manifest':json.loads((P/'review/viewer/manifest.json').read_text()),
                              'captures':{row[0]+'.png':sha(R/(row[0]+'.png')) for row in plan},
                              'sheet_sha256':sha(R/'Death.png')})
print('Round 3 Death sheet and checks complete',flush=True)
