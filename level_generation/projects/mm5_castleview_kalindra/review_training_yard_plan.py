"""Source-scale practice-target plan with conservative native road-tile envelopes."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle

from author_training_yard import prepare
from review_fortifications import rectangle

PROJECT=Path(__file__).resolve().parent


def render():
    spec=json.loads((PROJECT/'implementation/architecture.json').read_text())
    roads=json.loads((PROJECT/'implementation/roads.json').read_text())
    targets=prepare((PROJECT/'landscape/heightmap.raw').read_bytes())
    hall=next(b for b in spec['buildings'] if b['id']=='training')
    pool=next(p for p in spec['props'] if p['id']=='training_pool')
    fig,ax=plt.subplots(figsize=(9,9))
    ax.set_facecolor('#eee8d9')
    road_rects=[]
    for r,c in roads['cells']:
        x,y=c*512-32768,32768-(r+1)*512
        if -2300<x<2400 and -2100<y<2600:
            ax.add_patch(Rectangle((x,y),512,512,facecolor='#bcb7ad',edgecolor='#e4e0d5'))
            road_rects.append((x,y,x+512,y+512))
    for component in hall['components']:
        ax.add_patch(Polygon(rectangle(hall,component['bounds']),facecolor='#a98870',edgecolor='#433426'))
    for detail in hall['details']:
        b=detail['bounds']
        ax.add_patch(Polygon(rectangle(hall,[b[0],b[1],b[3],b[4]]),facecolor='#806c5a',edgecolor='#433426'))
    ax.add_patch(Polygon(rectangle(pool,pool['bounds']),facecolor='#688f9c',edgecolor='#273b44'))
    ax.text(-54,1170,'Practice pool\nNorth step retained',ha='center',va='center',fontsize=9)
    ax.text(-80,280,'Training hall',ha='center',fontsize=11)
    for venue in hall['venues']:
        x,y=venue['door'];ax.plot(x,y,'s',color='#8b5127',markersize=6)
        ax.plot([x-320,x],[y,y],color='#dcbf3f',linewidth=3)
    for prop in targets:
        poly=rectangle(prop,prop['bounds'])
        xs,ys=zip(*poly)
        assert all(max(xs)<=x0 or min(xs)>=x1 or max(ys)<=y0 or min(ys)>=y1
                   for x0,y0,x1,y1 in road_rects),prop['id']
        ax.add_patch(Polygon(poly,facecolor='#70452f',edgecolor='#251d13'))
        ax.add_patch(Polygon(rectangle(prop,prop['clearApproach']),fill=False,edgecolor='#8b6139',linestyle='--'))
        x,y=prop['frontOrigin'];ax.annotate(prop['title'],(x,y),xytext=(x-80,y-440),
            ha='center',fontsize=8,arrowprops={'arrowstyle':'-','color':'#5a4634'})
    ax.set(xlim=(-1800,1900),ylim=(-1500,2000),aspect='equal',xlabel='Native X',ylabel='Native Y',
           title='Training targets: south wall bays; pool and west doors stay clear\n'
                 'Grey squares show complete road tiles; dashed areas remain open for approach')
    ax.grid(alpha=.2)
    fig.tight_layout()
    output=PROJECT/'review/training_yard_v3'
    for extension in ['png','svg']:fig.savefig(output/('placement_plan.'+extension),dpi=150)
    plt.close(fig)


if __name__=='__main__':
    render()
