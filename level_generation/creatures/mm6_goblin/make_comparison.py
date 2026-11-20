"""Align native sprites, selected AI interpretations and final model renders without changing proportions."""
from pathlib import Path
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parent
BG=(43,47,48,255)
VIEWS=[('Front',0,(15,116,407,825)),('Oblique',1,(426,118,862,824)),
       ('Profile',2,(866,116,1349,814)),('Rear',4,(1280,125,1633,810))]

def opaque(image):
    image=image.convert('RGBA');box=image.getchannel('A').getbbox();assert box
    return image.crop(box)

def build():
    reference=Image.open(ROOT/'reference_restoration/turnaround_v1.png').convert('RGBA')
    sheet=Image.new('RGB',(1440,3040),BG[:3]);draw=ImageDraw.Draw(sheet)
    draw.text((15,12),'Native -> reviewed AI interpretation -> actual rigged model render. Equal figure height within each row.',fill='white')
    for row,(label,direction,box) in enumerate(VIEWS):
        native=opaque(Image.open(ROOT/'source_audit/frames'/f'gobsta{direction}.png'))
        restored=reference.crop(box)
        model=opaque(Image.open(ROOT/'spritesheets/masters_710x578'/f'rgobsa{direction}.png'))
        images=[native,restored,model]
        height=min(670,440/max(im.width/im.height for im in images))
        top=40+row*750;baseline=top+715
        for column,(image,title) in enumerate(zip(images,['Native MM6','Selected AI reference','Final 3D model'])):
            size=(round(image.width*height/image.height),round(height))
            image=image.resize(size,Image.Resampling.NEAREST if column==0 else Image.Resampling.LANCZOS)
            canvas=Image.new('RGBA',image.size,BG);canvas.alpha_composite(image)
            x=column*480+(480-image.width)//2
            sheet.paste(canvas.convert('RGB'),(x,baseline-image.height))
            draw.text((column*480+16,top+8),label+' | '+title,fill='white')
            draw.line((column*480+12,baseline+2,column*480+468,baseline+2),fill=(98,106,108))
    sheet.save(ROOT/'review/native_restored_model.png')

if __name__=='__main__':build()
