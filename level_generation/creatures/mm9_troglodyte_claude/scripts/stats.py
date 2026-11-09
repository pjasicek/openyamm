import sys, numpy as np
sys.path.insert(0, '/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm9_yrsa_claude/v2/scripts')
import clips_mm9 as cm
g, rest, clips = cm.source_clips(sys.argv[1])
names=[n.name for n in g.nodes]
import collections
overall=collections.defaultdict(float)
for name,(ch,dur) in clips.items():
    mv={}
    for (j,p),(t,v) in ch.items():
        if p=='rotation':
            d=np.degrees(2*np.arccos(np.clip(np.abs(v@rest[j][1]),0,1))); mv[j]=float(d.max()); overall[j]=max(overall[j],mv[j])
    tr={j:np.round(np.ptp(v,axis=0),3).tolist() for (j,p),(t,v) in ch.items() if p=='translation' and np.ptp(v,axis=0).max()>0.002}
    print(name,round(dur,3),{k:round(v) for k,v in mv.items() if 'Box' in k or 'Finger1' in k or 'Toe' in k or 'Dummy' in k},tr)
print({k:round(v) for k,v in overall.items()})
print(names)
