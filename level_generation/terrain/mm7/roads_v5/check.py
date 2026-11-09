"""Regression for the repeated projecting fragment seen in 1288.png, in finished RGB."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from common import *
from scipy.ndimage import gaussian_filter1d

def spike(path):
    rgb=read(path)
    stone=(rgb[:,:,0]-rgb[:,:,2])/np.maximum(rgb.mean(2),1)<.4
    stone[:130]=False;stone[205:]=False
    edge=255-np.argmax(stone[::-1],axis=0)
    repeated=np.tile(edge,3).astype(float)
    local=repeated-gaussian_filter1d(repeated,8)
    return float(local[248:264].max())

old=spike(P/'roads_v5/before/7drsrew.png')
new=spike(OUT/'7drsrew.png')
assert old>4,('reference no longer reproduces 1288',old)
assert new<3,('projecting fragment at finished road join',new)
report=dict(passed=True,reference='test_img/1288.png',old_outward_spike_runtime_px=old,
            new_outward_spike_runtime_px=new,threshold_runtime_px=3,
            files={p.name:sha(p) for p in OUT.glob('7drsr*.png')})
(P/'roads_v5/review.json').write_text(json.dumps(report,indent=2)+'\n')
print(report['old_outward_spike_runtime_px'], '->', report['new_outward_spike_runtime_px'], 'runtime px')
