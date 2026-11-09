from pathlib import Path
import json
from PIL import Image,ImageDraw

P=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm8_m540_claude')
casts=json.loads((P/'review/source_casts/clips.json').read_text())
for clip in casts:
    canvas=Image.new('RGB',(7*400,3*388),'#30343c');draw=ImageDraw.Draw(canvas)
    for view in range(3):
        for i,frame in enumerate((0,5,10,15,20,25,30)):
            img=Image.open(clip['frames'][frame][view]).convert('RGB')
            assert img.size==(400,360)
            canvas.paste(img,(i*400,view*388+28));draw.text((i*400+4,view*388+4),f"{clip['clip']} {frame}/30",fill='white')
    canvas.save(P/f"review/source_casts/{clip['clip']}_sheet.png")
    for view,name in enumerate(('front','left','three_quarter')):
        frames=[Image.open(row[view]).convert('RGB') for row in clip['frames']]
        frames[0].save(P/f"review/source_casts/{clip['clip']}_{name}.gif",save_all=True,append_images=frames[1:],duration=33,loop=0)
        frames[0].save(P/f"review/source_casts/{clip['clip']}_{name}_slow.gif",save_all=True,append_images=frames[1:],duration=133,loop=0)
    points=[f['wand_tip'] for f in clip['motion']]
    print(clip['clip'],'wand bounds',[(round(min(p[i] for p in points),3),round(max(p[i] for p in points),3)) for i in range(3)])

index=json.loads((P.parents[2]/'anim_library/index.json').read_text())['clips']
picked=next(c for c in index if c.get('glb_clip')=='ArmedCastRAttack1')
selection={'status':'source base selected; final Mage choreography, retargeting and G1/G3-G7 remain pending',
 'selected_cast_source':picked,
 'reason':'Right-hand wand grip and forward release, no large travel or hop; native waist-level charge must be authored before release.',
 'rejected':{'ArmedCastRAttack2':'Large forward lunge and torso drop, unnecessary for native mostly planted cast.',
             'ArmedCastRAttack3':'Upward hop/heel lift and exaggerated anticipation.',
             'UnarmedCastDualAttack2':'Useful Djinn casting reference, but dual open-hand release conflicts with the Mage wand grip.'},
 'adaptations':['Keep right hand gripping the short wand; use left palm to guide the orb during waist-level charge.',
                'Add native waist-level charge/roll, then raise and release the wand; retain source release and recovery speed.',
                'Match gait/posture to completed MM6 Ogre locomotion and Mage-specific anatomy, measure soles/stride after retargeting.',
                'Attach charge/release socket to orb, not bare palm; preserve native gameplay timings.',
                'Keep cape separate from arm weights, add local cloak chains and clearance checks.'],
 'reviews':'Source front/side/three-quarter frame sequences inspected; GIFs available at normal and quarter speed. Final Mage playback unverified.',
 'sources':'review/source_casts/clips.json'}
(P/'motion_selection.json').write_text(json.dumps(selection,indent=2)+'\n')
