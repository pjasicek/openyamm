"""Process Griffin raw RGBA sheets at measured native scale, preserving real alpha."""
import argparse
import importlib.util
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

P = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('griffin_shared_process', P.parent/'mm7_m514/process.py')
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)
keyed_extract = pipeline.extract


def extract(image, *args):
    if image.mode == 'RGBA' and image.getchannel('A').getextrema()[0] < 255:
        rgba = np.array(image)
        alpha = rgba[:, :, 3]
        labels, count = ndimage.label(alpha > 0)
        maxima = ndimage.maximum(alpha, labels, np.arange(count + 1))
        rgba[(alpha > 0) & (maxima[labels] <= 1)] = 0
        if Path(getattr(image, 'filename', '')).name == 'w_4_detail_1_v1.png':
            # Light composite confirms an intact feather tip at x=9. Only
            # opacity <=2/255 reaches the first seven gutter columns.
            gutter = rgba[:, :7]
            assert gutter[:, :, 3].max() <= 2
            gutter[:] = 0
        if Path(getattr(image, 'filename', '')).name == 'a_0_detail_1_v1.png':
            # Reviewed light composite has no art in this top gutter.
            assert rgba[:20, :, 3].max() <= 1
            rgba[:20] = 0
        if Path(getattr(image, 'filename', '')).name == 'a_2_detail_0_v1.png':
            assert rgba[:, 1251:, 3].max() <= 1
            rgba[:, 1251:] = 0
        return Image.fromarray(rgba)
    return keyed_extract(image, *args)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selected-only', action='store_true')
    args = parser.parse_args()
    pipeline.extract = extract
    pipeline.run(P, tone=.80, selected_only=args.selected_only)
    p = P/'processing_settings.json'
    settings = json.loads(p.read_text())
    settings['native_alpha_delivery'] = {
        'extraction': 'Preserve actual RGBA. Remove only detached components with maximum opacity1/255.',
        'tone': .80,
        'registration': 'Whole connected poses, one common native scale calibration per sheet and native baseline translation.',
        'variant_stage': 'Run local variants.py after this stage to author the enhanced masks.'
    }
    settings['reviewed_gutter_repairs'] = {
        'w_4_detail_1_v1.png': 'Clear x<7 only; maximum alpha2, visible feather tip starts x9; review/w4_alpha.png.',
        'a_0_detail_1_v1.png': 'Clear y<20 only; maximum alpha1; review/a0_alpha.png confirms empty gutter.',
        'a_2_detail_0_v1.png': 'Clear x>=1251 only; maximum alpha1, visible beak ends x1247; review/a2_alpha.png.'
    }
    p.write_text(json.dumps(settings,indent=2)+'\n')
