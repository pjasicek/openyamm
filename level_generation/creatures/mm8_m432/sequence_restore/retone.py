"""Reapply the frozen tone curve without re-extraction, resampling, or anchor changes."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image,ImageDraw
from tonal_curve import grade
F=Path(__file__).resolve().parent;R=F.parent
sys.path.insert(0,str(R));import process

def run():
    data=json.loads((F/'jobs.json').read_text())
    for key,j in data['jobs'].items():
        sheet=Image.new('RGB',(256*len(j['frames']),840),(35,35,35));draw=ImageDraw.Draw(sheet)
        for i,n in enumerate(j['frames']):
            art=Image.open(F/'registered_2x'/(n+'.png')).convert('RGBA');final=grade(art,n)
            final.save(F/'toned_2x'/(n+'.png'))
            native=Image.new('RGBA',(576,576));native.paste(process.queue.native(R,n).resize((512,512),Image.Resampling.NEAREST),(32,32))
            overlay=np.zeros((576,576,4),np.uint8);overlay[:,:,0]=np.array(native)[:,:,3];overlay[:,:,1]=np.array(final)[:,:,3];overlay[:,:,3]=255
            for row,pic in enumerate([native,final,Image.fromarray(overlay)]):
                bg=Image.new('RGBA',(576,576),(35,35,35,255));bg.alpha_composite(pic);sheet.paste(bg.resize((256,256)).convert('RGB'),(i*256,row*280+24));draw.text((i*256+3,row*280+4),n+' '+['native','enhanced 2x','native red / art green'][row],fill='white')
        sheet.save(F/'review'/(key+'_registration.png'))
        j['status']='processed_unreviewed';j['tone']='tone_settings.json'
    process.save(F/'jobs.json',data)
    print('Retoned all sequence masters; renewed contact review required.')

if __name__=='__main__':run()
