"""Contact sheet for comparing the restored reference and successive actual 3D renders."""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parent
BG=(43,47,48,255)
sheet=Image.new('RGBA',(1760,750),BG)
draw=ImageDraw.Draw(sheet)
native=Image.open(ROOT.parents[2]/'assets_dev/engine/sprites/m242sa0.bmp').convert('RGBA')
key=native.getpixel((0,0))[:3]
native.putdata([(*pixel[:3],0 if pixel[:3]==key else 255) for pixel in native.getdata()])
restored=Image.open(ROOT/'reference_restoration/standing_views_v1.png').convert('RGBA').crop((20,105,394,1035))
old=Image.open(ROOT/'revisions/v3_skull_draft/restoration_model_front.png').convert('RGBA')
new=Image.open(ROOT/'review/restoration_model_front.png').convert('RGBA')
for column,(label,im) in enumerate([
    ('Original m242',native),('AI-restored reference',restored),
    ('Accepted skull / older body',old),('Revised robe and skeleton',new)]):
    im=im.crop(im.getchannel('A').getbbox())
    scale=650/im.height
    size=(round(im.width*scale),round(im.height*scale))
    im=im.resize(size,Image.Resampling.NEAREST if column==0 else Image.Resampling.LANCZOS)
    assert im.width<440,(label,im.size)
    sheet.alpha_composite(im,(column*440+(440-im.width)//2,60))
    draw.text((column*440+15,20),label,fill='white')
sheet.convert('RGB').save(ROOT/'review/body_comparison.png')

# Identical camera and crop show the material/hood correction without scale changes.
detail=Image.new('RGBA',(1200,680),BG);labels=ImageDraw.Draw(detail)
for column,(label,path) in enumerate([
    ('Before: separate bone treatment and wide hood',ROOT/'revisions/v3_body_accepted/restoration_model_front.png'),
    ('After: matched bone surface and closer hood',ROOT/'review/restoration_model_front.png')]):
    im=Image.open(path).convert('RGBA').crop((150,50,750,680))
    detail.alpha_composite(im,(column*600,40))
    labels.text((column*600+15,15),label,fill='white')
detail.convert('RGB').save(ROOT/'review/material_fit_comparison.png')
