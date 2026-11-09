"""Render the proposed layouts; these are design drawings, not native map evidence."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parent
outdoor = json.loads((ROOT / 'outdoor_plan.json').read_text())
indoor = json.loads((ROOT / 'indoor_plan.json').read_text())
fig, (outside, inside) = plt.subplots(1, 2, figsize=(20, 11), constrained_layout=True)
fig.suptitle('Brackenford / Greywatch — original design plans, before greybox validation', fontsize=18)

outside.set_facecolor('#dfe8ca')
river = outdoor['terrain']['river_centerline']
outside.plot(*zip(*river), color='#76b0cc', linewidth=15, solid_capstyle='round', zorder=1)
outside.plot(*zip(*outdoor['roads']['main']), color='#b79764', linewidth=5, zorder=2)
for building in outdoor['buildings']:
    x, y = building['xy']
    width, depth = building['target_footprint']
    outside.add_patch(Rectangle((x-width/2, y-depth/2), width, depth, color='#71624b', zorder=3))
    outside.text(x, y+850, building['id'].replace('_', ' '), ha='center', fontsize=6)
for landmark in outdoor['landmarks']:
    x, y = landmark['xy']
    outside.scatter(x, y, s=110, marker='D', color='#704b75', zorder=4)
    outside.annotate(landmark['id'], (x,y), xytext=(7,7), textcoords='offset points', fontsize=10)
for encounter in outdoor['encounters']:
    x, y = encounter['xy']
    outside.scatter(x, y, s=240, marker='x', color='#9b342e', linewidths=3)
    outside.annotate(encounter['id'].replace('_',' '), (x,y), xytext=(-5,12),
                     textcoords='offset points', ha='right', fontsize=9, color='#9b342e')
for loot in outdoor['loot_sites']:
    outside.scatter(*loot['xy'], s=100, marker='s', color='#bc850b')
outside.scatter(*outdoor['terrain']['bridge_center'], marker='s', s=100, color='#564a38', zorder=5)
outside.set_title('Grassland town, modest river, remote rewards and two dungeon approaches')
outside.set_xlim(-24576,24576)
outside.set_ylim(-24576,24576)
outside.set_xlabel('Native X — detailed road branches and height contours still to author')
outside.set_ylabel('Native Y')

rooms = {room['id']:room for room in indoor['rooms']}
colors = {0:'#adbd90', 384:'#e0c99a', 768:'#adbfd6'}
for link in indoor['connections']:
    a, b = rooms[link['a']], rooms[link['b']]
    color = '#914f58' if link['kind'] in ('secret_door','unlockable_shortcut_stairs') else '#8f8b80'
    inside.plot([a['center'][0],b['center'][0]], [a['center'][1],b['center'][1]],
                '--' if color == '#914f58' else '-', color=color, linewidth=3, zorder=0)
for room in indoor['rooms']:
    x, y, z = room['center']
    w, h = room['size']
    inside.add_patch(Rectangle((x-w/2,y-h/2),w,h,facecolor=colors[z],edgecolor='#424c56'))
    inside.text(x,y,room['id'].replace('_',' ')+'\nZ '+str(z),ha='center',va='center',fontsize=8)
inside.set_title('11 chambers — 3 floor levels — 24 humanoid hostiles')
inside.set_xlim(-4608,11520)
inside.set_ylim(-4352,10240)
inside.set_xlabel('Native X — boxes show footprint budgets, not final room polygons')
inside.set_ylabel('Native Y — connections need explicit corridors, stairs, portals and lift shaft')
for axis in (outside, inside):
    axis.set_aspect('equal')
    axis.grid(alpha=.2)
fig.savefig(ROOT / 'layout_plan.png', dpi=130)
plt.close(fig)
print(ROOT / 'layout_plan.png')
