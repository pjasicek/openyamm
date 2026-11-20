"""Inspect captured native liquid motion; bind all screenshots and preserve review limits."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import json
import argparse
from PIL import ImageDraw
from common import *

F=Path(__file__).resolve().parent
ROI=(320,420,1200,840)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--flying',action='store_true')
    parser.add_argument('--alvar-lava',action='store_true')
    parser.add_argument('--open-tar-pool',action='store_true')
    args=parser.parse_args()
    assert not (args.alvar_lava or args.open_tar_pool) or args.flying
    destination=F/'native_review' if args.alvar_lava else F/'native_flying' if args.flying else F
    destination.mkdir(exist_ok=True)
    results={};comparison=Image.new('RGB',(1600,3*624),'#202933');draw=ImageDraw.Draw(comparison)
    for row,family in enumerate(('water','lava','tar')):
        for col,quality in enumerate(('x1','x2')):
            name='mm8_liquid_'+family+('_flying' if args.flying else '')+'_'+quality
            if args.alvar_lava and family=='lava':name='mm8_liquid_lava_alvar_'+quality
            if args.open_tar_pool and family=='tar':name='mm8_liquid_tar_pool_'+quality
            metadata_path=P/'captures'/(name+'.json');metadata=json.loads(metadata_path.read_text())
            manifest_path=P/'captures'/(name+'_cycle_frames.json');manifest=json.loads(manifest_path.read_text())
            assert len(manifest['screenshots'])==40
            times=manifest['captureElapsedSeconds'];assert times[-1]-times[0]>3.5
            if quality=='x2':
                assert len(metadata['terrain_candidates']['files'])==239
                for r in json.loads((F/'build.json').read_text())['families'][family]['files']:
                    assert metadata['terrain_candidates']['files'][r['name']]==r['sha256']
            imgs=[Image.open(P/'captures'/n).convert('RGB').crop(ROI) for n in manifest['screenshots']]
            arrays=np.asarray([np.asarray(im.resize((220,105)),float) for im in imgs])
            steps=np.mean(abs(arrays[1:]-arrays[:-1]),axis=(1,2,3))
            lags=[]
            for lag in range(1,21):
                err=float(np.mean(abs(arrays[lag:]-arrays[:-lag])))
                lags.append(dict(lag=lag,seconds=float(np.mean(np.asarray(times[lag:])-times[:-lag])),mae=err))
            best=min(lags[12:19],key=lambda r:r['mae'])
            mean_nonlocal=float(np.mean([r['mae'] for r in lags[3:12]]))
            result=dict(captured_frames=40,elapsed_seconds=times[-1]-times[0],roi=list(ROI),
                temporal_steps=steps.tolist(),lag_errors=lags,best_cycle_candidate=best,
                cycle_to_nonlocal_error_ratio=best['mae']/max(mean_nonlocal,1e-6),
                time_varying=float(arrays.std(0).mean()),
                metadata_sha256=sha(metadata_path),burst_manifest_sha256=sha(manifest_path),
                screenshots={n:sha(P/'captures'/n) for n in manifest['screenshots']})
            result['temporal_screen_passed']=(result['time_varying']>.1 and
                abs(best['seconds']-14*15/128)<.12 and result['cycle_to_nonlocal_error_ratio']<.4)
            results[family+'_'+quality]=result
            durations=[max(1,round((times[i+1]-times[i])*1000)) for i in range(39)]+[100]
            imgs[0].save(destination/(family+'_'+quality+'_native_motion.webp'),save_all=True,append_images=imgs[1:],
                         duration=durations,loop=0,lossless=True)
            strip=Image.new('RGB',(4*440,3*234),'#202933');sd=ImageDraw.Draw(strip)
            for k,i in enumerate((0,3,7,10,13,16,20,23,27,30,33,37)):
                x,y=k%4*440,k//4*234;sd.text((x+4,y+4),'frame%d %.2fs'%(i,times[i]),fill='white')
                strip.paste(imgs[i].resize((440,210)),(x,y+24))
            strip.save(destination/(family+'_'+quality+'_motion_samples.png'))
            final=P/'captures'/(name+'.png');assert sha(final)==metadata['screenshot_sha256']
            draw.text((col*800+4,row*624+4),family+' '+quality,fill='white')
            comparison.paste(Image.open(final).resize((800,600)),(col*800,row*624+24))
            print(family,quality,'period',round(best['seconds'],3),'recurrence ratio',round(result['cycle_to_nonlocal_error_ratio'],3),
                  'screen',result['temporal_screen_passed'],flush=True)
    comparison.save(destination/'native_comparison.png')
    (destination/'motion_measurements.json').write_text(json.dumps(dict(scope='40-frame stationary native captures per liquid and quality; period screen, not complete visual acceptance',
        expected_cycle_seconds=14*15/128,measurements=results,build_sha256=sha(F/'build.json'),
        comparison_sha256=sha(destination/'native_comparison.png'),script_sha256=sha(Path(__file__))),indent=2)+'\n')


if __name__=='__main__':main()
