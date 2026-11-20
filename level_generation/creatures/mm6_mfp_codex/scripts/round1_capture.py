import http.server,functools,threading,subprocess,os,signal
from pathlib import Path
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2]
class Handler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start();proc=None
try:
 proc=subprocess.Popen(['node',str(P/'scripts/round1_capture.mjs'),f'http://127.0.0.1:{server.server_port}/level_generation/creatures/mm6_mfp_codex/review/viewer/',str(P/'review/round1'),str(P/'review/round1/capture_plan.json')],start_new_session=True);assert proc.wait(timeout=180)==0
finally:
 server.shutdown();server.server_close()
 if proc:
  try:os.killpg(proc.pid,signal.SIGTERM)
  except ProcessLookupError:pass
