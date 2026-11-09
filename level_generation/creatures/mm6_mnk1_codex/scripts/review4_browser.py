"""Own a temporary read-only server and close it with every browser review run."""
import http.server,threading,subprocess,json,hashlib
from pathlib import Path
p=Path(__file__).resolve().parents[1];root=p.parents[2]
class Handler(http.server.SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(root),**kw)
 def log_message(self,*a):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}/level_generation/creatures/mm6_mnk1_codex/review/viewer/'
try:
 result=subprocess.run(['node',str(p.parent/'claude_shared/check_viewer.mjs'),url,'60'],capture_output=True,text=True,check=True);d=json.loads(result.stdout);assert d['switched']==27 and not d['failed'] and not d['consoleErrors'];d['runtime_sha256']=hashlib.sha256((p/'export/mm6_mnk1.glb').read_bytes()).hexdigest();(p/'review/round4/viewer_check.json').write_text(json.dumps(d,indent=2));print('VIEWER 27 PASS',flush=True)
 specs=['standing_front:Standing:0:front:body:0,1.15,1.4:0,1.15,.15','standing_left:Standing:.5:left:body:1.25,1.15,.15:0,1.15,.15','standing_quarter:Standing:1.5:quarter:body:-.9,1.15,1.05:0,1.15,.15','attack_palms:Attack:.716667:front:body:0,1.3,2:0,1.2,.2','attack_side:Attack:.716667:left:body:1.7,1.3,.5:0,1.2,.2','attack_withdraw:Attack:.35:quarter:body:-.9,1.3,1.7:0,1.2,.2','cast_front:Cast:.45:front:body:0,1.3,2:0,1.2,.2','cast_palms:Cast:.45:quarter:body:-.9,1.3,1.7:0,1.2,.2','cast_return:Cast:1:front:body:0,1.15,1.4:0,1.15,.15','attack_return:Attack:1.266667:front:body:0,1.15,1.4:0,1.15,.15','walking_front:Walking:.6:front:body:0,.6,1.6:0,.45,0','walking_side:Walking:.6:left:body:1.6,.6,0:0,.45,0','walking_quarter:Walking:.6:quarter:body:-1.1,.55,1.2:0,.45,0','death_mid:Death:.7:quarter:body','death_final:Death:2:quarter:body']
 subprocess.run(['node',str(p.parent/'mm6_dru1_claude/scripts/viewer_shots.mjs'),url,str(p/'review/round4'),*specs],check=True)
 subprocess.run(['node',str(p/'scripts/viewer_playback.mjs'),url,str(p/'review/playback')],check=True)
finally:server.shutdown();server.server_close()
