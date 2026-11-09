"""Capture paired native flat fixtures and real Emerald Island with the frozen executable."""
import argparse,json,subprocess
from common import *
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--quality',choices=['x1','x2'],required=True);ap.add_argument('--family');args=ap.parse_args()
 stage=json.loads((P/'reports/review_stage.json').read_text());assert sha(Path(stage['stage'])/'openyamm')==stage['binary_sha256']
 assert all(sha(OUT/n)==h for n,h in stage['files'].items())
 names=[args.family] if args.family else list(stage['poses'])+['emerald']
 for name in names:
  mode=('original' if args.quality=='x1' else 'enhanced') if name=='emerald' else stage['poses'][name]['mode']+'_'+args.quality
  cmd=['python3',str(ROOT/'level_generation/projects/brackenford_greywatch/capture_gameplay.py'),'mm7_'+name+'_'+args.quality,'--world','mm7','--map','7out01.odm','--stage',stage['stage']+'/'+mode,'--binary',stage['stage']+'/openyamm','--review-directory',str(P/'captures'),'--warmup','1','--seconds','0']
  if name!='emerald':cmd+=['--start-save',str(P/'captures'/f'{name}.oysav'),'--diagnostic-flying']
  with (P/'captures'/f'capture_{name}_{args.quality}.log').open('w') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
  print('Captured',name,args.quality,flush=True)
if __name__=='__main__':main()
