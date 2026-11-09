# Body Magic page: local Real-ESRGAN restoration

The complete 640×480 native rendered page in `../originals/engine--icons--sbb000.bmp.png` was processed with the
workspace's `tools/upscaling/realesrgan-ncnn-vulkan` and its `realesrgan-x4plus` model. The 2560×1920 result is
retained as `sbb000-x4-master.png`. `finalize.py` reduces it with Pillow Lanczos to the exact 1280×960 opaque
`sbb000-x2.png` candidate. `manifest.json` records source, binary, model, master and final hashes.

Inference command from the repository root:

```sh
tools/upscaling/realesrgan-ncnn-vulkan \
  -i level_generation/ui/mm8_art_review/originals/engine--icons--sbb000.bmp.png \
  -o level_generation/ui/mm8_art_review/sbb000_esrgan/sbb000-x4-master.png \
  -m tools/upscaling/models -n realesrgan-x4plus -s 4 -t 128
python3 level_generation/ui/mm8_art_review/sbb000_esrgan/finalize.py
```

The inference run used the available llvmpipe Vulkan software device. Inspection at exact 2× found the original
open-book frame, center fold, blank parchment, `BODY` lettering and medallion composition intact. The output is
opaque, has no saturated magenta on its outer three pixels, and keeps every edge of the original canvas. The
approved copy is in `../staged_spellbook_pages/engine/icons_x2/sbb000.png`.
