from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
from pathlib import Path
import json,os
p=Path(__file__).resolve().parents[1]
s=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(p.parents[2])))
print(json.dumps({'pid':os.getpid(),'port':s.server_port}),flush=True)
s.serve_forever()
