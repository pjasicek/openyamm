import os,sys,json,subprocess,threading,http.server,functools,signal
from pathlib import Path
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];R=P/'review/round2';env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
b=subprocess.run([sys.executable,str(ROOT/'output/codex_batch/check_bindings.py'),str(P/'integration/actors.yml')],cwd=ROOT,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(R/'bindings.txt').write_text(b.stdout);assert b.returncode==0 and 'BAD'not in b.stdout,b.stdout
class Handler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT)));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();proc=None
try:
 url=f'http://127.0.0.1:{server.server_port}/level_generation/creatures/mm6_mfp_codex/review/viewer/'
 proc=subprocess.Popen(['node',str(ROOT/'level_generation/creatures/claude_shared/check_viewer.mjs'),url,'60'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,start_new_session=True);output,_=proc.communicate(timeout=180);(R/'viewer_check.json').write_text(output);assert proc.returncode==0,output;result=json.loads(output);assert result['switched']==24 and not result['failed'] and not result['consoleErrors'];print(output)
finally:
 server.shutdown();server.server_close()
 if proc:
  try:os.killpg(proc.pid,signal.SIGTERM)
  except ProcessLookupError:pass
print(b.stdout)
