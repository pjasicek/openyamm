"""Independently classify baked corners and measure compatible raster-edge mixtures."""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]


def linear(rgb):
    return np.where(rgb <= .04045, rgb/12.92, ((rgb+.055)/1.055)**2.4)


def review(version):
    output = PROJECT/'review'/version
    manifest = json.loads((output/'manifest.json').read_text())
    images = {int(key):np.array(Image.open(output/value['path']).convert('RGB'))
              for key,value in manifest['variants'].items()}
    donors = {key:np.array(Image.open(ROOT/value['path']).convert('RGB'))
              for key,value in manifest['donors'].items()}
    canvas = Image.new('RGB',(800,880),'#242424')
    draw = ImageDraw.Draw(canvas)
    errors, classified = [], {}
    for slot,(bits,pixels) in enumerate(images.items()):
        x,y = slot%4*200,slot//4*220
        canvas.paste(Image.fromarray(pixels).resize((192,192)),(x,y))
        draw.text((x+3,y+198),f'dirt mask {bits}',fill='white')
        corners = []
        for i,(x,y) in enumerate([(0,0),(120,0),(0,120),(120,120)]):
            rgb = pixels[y:y+8,x:x+8].mean((0,1))
            dirt = bool(rgb[0]-rgb[1]>20 and rgb[1]<80)
            corners.append(int(dirt))
            if dirt != bool(bits&(1<<i)):
                errors.append({'mask':bits,'corner':i,'rgb':rgb.tolist()})
        classified[bits] = corners
    canvas.save(output/'contact_sheet.png')
    sand,dirt = [linear(donors[key].astype(float)/255) for key in ['sand','dirt']]
    delta = dirt-sand
    weights = {bits:np.clip(((linear(pixels.astype(float)/255)-sand)*delta).sum(2)
                           /(delta*delta).sum(2),0,1) for bits,pixels in images.items()}
    joins = []
    for a,weight_a in weights.items():
        for b,weight_b in weights.items():
            sides = [('east',(a>>1&1)==(b&1) and (a>>3&1)==(b>>2&1),weight_a[:,-1],weight_b[:,0]),
                     ('south',(a>>2&3)==(b&3),weight_a[-1,:],weight_b[0,:])]
            for side,compatible,x,y in sides:
                if compatible:
                    joins.append({'masks':[a,b],'edge':side,'maxWeightDelta':float(abs(x-y).max()),
                                  'meanWeightDelta':float(abs(x-y).mean())})
    report = {'status':'isolated artwork audit; regional source and native review still required',
              'cornerErrors':errors,'classifiedCorners':classified,'compatibleJoins':len(joins),
              'maximumJoinWeightDelta':max(j['maxWeightDelta'] for j in joins),
              'meanJoinWeightDelta':float(np.mean([j['meanWeightDelta'] for j in joins])),
              'worstJoins':sorted(joins,key=lambda j:j['maxWeightDelta'],reverse=True)[:10],
              'donorMaximumRgbDelta':{key:int(abs(images[bits].astype(int)-donors[key].astype(int)).max())
                                      for bits,key in [(0,'sand'),(15,'dirt')]},
              'method':'independent RGB corner classification; recover linear-light blend weights from actual pixels',
              'limits':'Recovered weights include 8-bit rounding; original donor texture edges themselves are not identical.'}
    (output/'artwork_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print({key:value for key,value in report.items() if key not in ['classifiedCorners','worstJoins','method','limits']})
    assert not errors
    assert report['maximumJoinWeightDelta']<.06, 'Baked boundary masks do not meet at raster edges'
    assert max(report['donorMaximumRgbDelta'].values())<=1, 'Bake changed the original native donor colours'


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version',default='desert_materials_v2')
    review(parser.parse_args().version)
