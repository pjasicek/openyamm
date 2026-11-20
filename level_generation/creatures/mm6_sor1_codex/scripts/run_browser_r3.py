from pathlib import Path
import subprocess,json,sys
p=Path(__file__).resolve().parents[1];repo=p.parents[2]
server=subprocess.Popen([sys.executable,str(p/'scripts/serve_round1.py')],stdout=subprocess.PIPE,stderr=(p/'work/viewer_server_r3.log').open('w'),text=True)
try:
 info=json.loads(server.stdout.readline());info['url']=f"http://127.0.0.1:{info['port']}/{p.relative_to(repo)}/review/viewer/";(p/'work/viewer_server.json').write_text(json.dumps(info))
 subprocess.run([sys.executable,str(p/'scripts/update_viewer_manifest.py')],check=True)
 subprocess.run([sys.executable,str(p/'scripts/review_round3.py')],check=True)
finally:
 server.terminate();server.wait(timeout=10)
