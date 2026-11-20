"""Serial native game comparisons. Run without other builds/tests; visually review all four captures."""
from pathlib import Path
import subprocess
import json
PROJECT=Path(__file__).resolve().parent
cases=[('perf_brackenford','lg01.odm',[-10240,-1536,640,1.5707963267948966,0],0),
       ('perf_ravenshore','out02.odm',[13616,-9000,0,1.5707963267948966,0],0),
       ('perf_greywatch','lg02.blv',[3008,3072,384,0,0],0),
       ('perf_naga','d18.blv',[-500,-1576,-64,0,0],1.5707963267948966)]
for name,map_name,pose,look in cases:
    subprocess.run(['xvfb-run','-a','-s','-screen 0 1600x1200x24','python3',str(PROJECT/'capture_gameplay.py'),name,
      '--map',map_name,'--pose',*map(str,pose),'--look-left',str(look),'--warmup','2','--seconds','3'],check=True)
reports=[json.loads((PROJECT/'review/gameplay'/(c[0]+'.json')).read_text()) for c in cases]
assert len({r['binary_sha256'] for r in reports})==1
assert len({r['settings_sha256'] for r in reports})==1
assert all(len(r['fps_samples'])>=2 for r in reports)
(PROJECT/'review/performance.json').write_text(json.dumps(dict(status='captured; visual acceptance required',reports=reports,
 limitation='Same binary/settings/party, serial software-display samples. Outdoor service approaches and indoor active encounters differ in visible geometry/actors. These measure sampled workloads, not isolated terrain or GPU scalability.'),indent=2)+'\n')
