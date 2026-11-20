"""Plot source route contacts, travel bounds and visual continuation at native unit scale."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch, Rectangle
import numpy as np
from PIL import Image

PROJECT = Path(__file__).resolve().parent
REVIEW = PROJECT/'review/travel_placeholder_v1'


def review():
    routes = json.loads((PROJECT/'implementation/route_placeholders.json').read_text())['routes']
    paths = json.loads((PROJECT/'implementation/roads.json').read_text())['paths']
    road_cells = {tuple(cell) for path in paths for cell in path['cells']}
    classes = np.array(Image.open(PROJECT/'landscape/surface_classes.png'))[:127,:127]
    palette = ListedColormap(['#242d35','#677d45','#71543c','#447897','#819449','#d6b975',
                             '#555555','#555555','#4d3e35','#555555','#8d877a'])
    fig, axes = plt.subplots(1,2,figsize=(13,7))
    for ax,route in zip(axes,routes):
        x0,y0,x1,y1 = route['bounds']
        ax.imshow(classes,origin='upper',extent=[-32768,32256,-32256,32768],
                  cmap=palette,vmin=0,vmax=10,interpolation='nearest')
        for row,col in road_cells:
            ax.add_patch(Rectangle(((col-64)*512,(63-row)*512),512,512,
                                   facecolor='#b9b7a9',edgecolor='none'))
        ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,facecolor='#ffd457',
                               edgecolor='#ffeea1',alpha=.8,lw=1.5))
        if route['id']=='sw_sc':
            ax.axvline(24576,color='#72e0e2',ls='--',lw=2)
            ax.set_xlim(21504,32256);ax.set_ylim(1792,8960)
            ax.text(26000,8000,'Visible road and river\ncontinue into buffer',color='white',fontsize=10)
        else:
            ax.axhline(24576,color='#72e0e2',ls='--',lw=2)
            ax.set_xlim(-15104,-7936);ax.set_ylim(22016,32768)
            ax.text(-14800,29200,'Off-road landscape\ncontinues into buffer',color='white',fontsize=10)
        ax.scatter(*route['arrival'],s=65,color='#77c9ff',edgecolors='white',zorder=5)
        ax.annotate('Future arrival',route['arrival'],xytext=(10,-20),textcoords='offset points',
                    color='white',fontsize=9)
        ax.scatter(*route['point'],s=50,marker='x',color='white',zorder=6)
        ax.set_title(route['label']+'\n'+route['id']+' — travel days unresolved')
        ax.set_xlabel('World X');ax.set_ylabel('World Y');ax.set_aspect('equal')
        ax.tick_params(labelsize=8);ax.grid(alpha=.12)
    fig.legend(handles=[Patch(facecolor='#ffd457',label='Invisible grounded contact'),
                        Patch(facecolor='#72e0e2',label='Travel boundary'),
                        Patch(facecolor='#b9b7a9',label='Native road cells')],loc='lower center',ncol=3)
    fig.suptitle('MM5 route placeholder source plan — unchanged terrain and travel envelope')
    fig.tight_layout(rect=[0,.07,1,.94])
    for extension in ['png','svg']:
        fig.savefig(REVIEW/('route_plan.'+extension),dpi=150)
    plt.close(fig)


if __name__=='__main__':
    review()
