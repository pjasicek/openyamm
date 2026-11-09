"""Draw the current ranger garden/working-ground reservations at native physical scale."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle
from PIL import Image
import numpy as np

from review_fortifications import rectangle

PROJECT = Path(__file__).resolve().parent


def render():
    read = lambda name: json.loads((PROJECT/name).read_text())
    spec = read('implementation/architecture.json')
    prop, = [p for p in spec['props'] if p['id']=='ranger_woodcraft']
    scene = read('implementation/scenery.json')
    fig, ax = plt.subplots(figsize=(10,9))
    surface = np.array(Image.open(PROJECT/'landscape/surface_classes.png'))
    palette = np.array(['#28343c','#71854c','#81634a','#405f73','#62666c','#c7aa68','#66534a'])
    from matplotlib.colors import ListedColormap
    ax.imshow(surface,cmap=ListedColormap(palette),vmin=0,vmax=6,
              extent=[-32768,32768,-32768,32768],interpolation='nearest')
    for b in spec['buildings']:
        for component in b['components']:
            poly = rectangle(b,component['bounds'])
            ax.add_patch(Polygon(poly,facecolor='#a88c78',edgecolor='#2c211c',linewidth=1.4))
        x,y = b['frontOrigin']
        if -8600<x<-5500 and -4100<y<100:
            ax.text(x-300,y+230,b['id'],ha='center',fontsize=10)
            for venue in b['venues']:
                ax.plot(*venue['door'],'s',color='#e8cc68',markersize=5)
    xy = lambda cell: [(cell[1]-64)*512+256,(64-cell[0])*512-256]
    for path in read('implementation/roads.json')['paths']:
        points = np.array([xy(c) for c in path['cells']])
        ax.plot(points[:,0],points[:,1],color='#c2b9a5',linewidth=4)
    ax.add_patch(Polygon(rectangle(prop,prop['bounds']),facecolor='#855333',edgecolor='#211910'))
    ax.text(-7190,-2900,'Woodcraft group',ha='center',fontsize=10,color='white')
    a,b,c,d = prop['clearLodgeApproach']
    ax.add_patch(Rectangle((a,b),c-a,d-b,fill=False,edgecolor='#ffffbb',linewidth=2,linestyle='--'))
    ax.text(-6990,-2070,'Clear unpaved approach',ha='center',fontsize=10,color='white')
    for record in scene['records']:
        x,y = record['position'][:2]
        if not (-8600<x<-5500 and -4100<y<100):
            continue
        garden = record.get('group')=='ranger_practice_garden'
        ax.add_patch(Circle((x,y),record['visualRadius'],facecolor='#cdd89b' if garden else '#3d5843',
                            edgecolor='#172916',alpha=.8))
        if garden:
            ax.text(x,y+record['visualRadius']+25,record['name'],ha='center',fontsize=8)
    ax.set(xlim=(-8600,-5500),ylim=(-4100,100),aspect='equal',xlabel='Native X',ylabel='Native Y',
           title='Goldur lodge: working ground and small practice garden\n'
                 'Semantic plan; circles show full sprite half-width, not collision radius')
    ax.grid(alpha=.15)
    fig.tight_layout()
    output = PROJECT/'review/ranger_yard_v3'
    for suffix in ['png','svg']:
        fig.savefig(output/('placement_plan.'+suffix),dpi=150)
    plt.close(fig)


if __name__=='__main__':
    render()
