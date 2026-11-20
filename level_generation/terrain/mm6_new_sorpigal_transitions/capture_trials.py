"""Capture versioned native test scenes under xvfb using the established gameplay capture helper."""
import argparse
import json
from pathlib import Path
import subprocess
P=Path(__file__).resolve().parent
ROOT=P.parents[2]
parser=argparse.ArgumentParser()
parser.add_argument('--version',default='v1')
parser.add_argument('--only',nargs='*')
parser.add_argument('--actions',type=Path)
parser.add_argument('--binary',type=Path,help='Frozen executable for consistent before/after trials')
args=parser.parse_args()
poses=json.loads((P/'captures/poses.json').read_text())
review=P/'captures'/args.version;review.mkdir(exist_ok=True)
for pose in poses:
 name=pose['stage']+'_'+pose['name']
 if args.only and name not in args.only:continue
 if (review/(name+'.json')).exists():print('Already captured',name,flush=True);continue
 print('Capturing',name,flush=True)
 with (review/(name+'_capture.log')).open('w') as log:
  subprocess.run(['python3',str(ROOT/'level_generation/projects/brackenford_greywatch/capture_gameplay.py'),
                  name,'--world','mm6','--map','oute3.odm','--stage',pose['stage_path'],
                  '--review-directory',str(review),'--start-save',pose['save'],
                  '--actions',str(args.actions or P.parent/'mm6_new_sorpigal_master_study/references/capture_actions.json'),
                  '--warmup','1','--seconds','0']+(['--binary',str(args.binary)] if args.binary else []),
                 cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
 print('Captured',name,flush=True)
