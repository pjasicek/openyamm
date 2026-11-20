"""Orthographic joint X-rays drawn from measured mesh vertices and the three joint estimates."""
import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1]
raw=np.load(P/'review/geometry/joint_surface.npz');verts,faces=raw['vertices'],raw['faces']
sets={name:json.loads((P/'work'/file).read_text())['joints'] for name,file in [('fit','joints_final.json'),('Meshy','meshy_joints.json'),('rings','joints_rings.json')]}
im=Image.new('RGB',(1600,1000),'white');draw=ImageDraw.Draw(im);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)
links=[('Pelvis','Spine'),('Spine','Spine1'),('Spine1','Spine2'),('Spine2','Neck'),('Neck','Head')]
for side in ['L','R']:links += [(side+'_'+a,side+'_'+b) for a,b in [('Clavicle','UpperArm'),('UpperArm','Forearm'),('Forearm','Hand'),('Thigh','Calf'),('Calf','Foot'),('Foot','Toe0')]]
for panel,axis in enumerate([0,1]):
    def point(p):return (int(400+panel*800+p[axis]*430),int(920-p[2]*500))
    for face in faces:draw.line([point(verts[i]) for i in [*face,face[0]]],fill=(226,230,234),width=1)
    for name,color in [('Meshy','black'),('rings','green'),('fit','red')]:
        j=sets[name]
        if name=='fit':
            for a,b in links:draw.line([point(j[a]),point(j[b])],fill=color,width=2)
        for key,p in j.items():
            x,y=point(p)
            if name=='fit':draw.ellipse((x-3,y-3,x+3,y+3),fill=color)
            elif name=='Meshy':draw.line((x-4,y-4,x+4,y+4),fill=color,width=2);draw.line((x-4,y+4,x+4,y-4),fill=color,width=2)
            else:draw.line((x-5,y,x+5,y),fill=color,width=2);draw.line((x,y-5,x,y+5),fill=color,width=2)
            if name=='fit' and not (axis==1 and key.startswith('R_')):draw.text((x+5,y),key,fill=color,font=font)
    draw.text((panel*800+30,20),'Front X/Z' if axis==0 else 'Side Y/Z',fill='black',font=font)
draw.text((30,970),'Red: fitted joints / Black: raw Meshy / Green: independent skin rings',fill='black',font=font)
im.save(P/'review/geometry/joints_xray.png')
