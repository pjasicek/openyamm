"""Process selected mm7_m198 sheets; preserve genuine RGBA transparency."""
import argparse
import importlib.util
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

P = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('shared_process', P.parent/'mm7_m514/process.py')
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
        return Image.fromarray(rgba)
    return keyed_extract(image, *args)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selected-only', action='store_true')
    args = parser.parse_args()
    pipeline.extract = extract
    pipeline.run(P, tone=0.78, selected_only=args.selected_only)
    p = P/'processing_settings.json'
    settings = json.loads(p.read_text())
    settings['native_alpha_delivery'] = {
        'extraction': 'Preserve actual RGBA; remove only detached components with maximum opacity 1/255.',
        'tone': 0.78,
        'registration': 'Whole connected poses; shared batch scale and native baseline translation.'
    }
    p.write_text(json.dumps(settings, indent=2)+'\n')
