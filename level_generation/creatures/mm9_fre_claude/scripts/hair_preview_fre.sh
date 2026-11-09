#!/bin/bash
# part-coloured head views of an asm npz: <asm npz> <out prefix>  (review/hair/<prefix>_sheet.png)
cd "$(dirname "$0")/.."
B="systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
$B --python scripts/view_npz_cull.py -- "$1" "review/hair/$2" 0,0,0.66 0.30 500 front:left:q34:back:q34b:below col 2>&1 | grep Error
python3 -c "
from PIL import Image
ims=[Image.open('review/hair/$2_'+v+'.png') for v in 'front left q34 back q34b below'.split()]
s=Image.new('RGB',(3000,500)); [s.paste(i,(500*k,0)) for k,i in enumerate(ims)]; s.save('review/hair/$2_sheet.png')"
