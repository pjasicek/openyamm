"""Process Treant's retained keyed sheets and newer native-alpha deliveries."""
import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('treant_shared_process', HERE.parent / 'mm7_m514/process.py')
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)
keyed_extract = pipeline.extract


def extract(image, *args):
    if image.mode == 'RGBA' and image.getchannel('A').getextrema()[0] < 255:
        rgba = np.array(image)
        alpha = rgba[:, :, 3]
        labels, count = ndimage.label(alpha > 0)
        maxima = ndimage.maximum(alpha, labels, np.arange(count + 1))
        # These deliveries contain detached 1/255-opacity specks in empty gutters.
        # Keep every component with stronger coverage and its complete soft edge.
        rgba[(alpha > 0) & (maxima[labels] <= 1)] = 0
        if Path(getattr(image, 'filename', '')).name == 'death_corpse_detail_margin_2_v1.png':
            # Reviewed rightmost gutter column: only 1/255 opacity, while all
            # stronger branch coverage ends before x=1021. Keep the inner soft edge.
            gutter = rgba[:, 1023:, :]
            assert gutter[:, :, 3].max() <= 1
            gutter[gutter[:, :, 3] == 1] = 0
        return Image.fromarray(rgba)
    return keyed_extract(image, *args)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selected-only', action='store_true')
    args = parser.parse_args()
    pipeline.extract = extract
    pipeline.run(HERE, tone=.75, selected_only=args.selected_only)
    path = HERE / 'processing_settings.json'
    settings = json.loads(path.read_text())
    settings['native_alpha_delivery'] = {
        'extraction': 'Preserve supplied RGBA alpha; opaque RGB sheets retain chroma extraction.',
        'detached_gutter_specks': 'Remove only disconnected alpha components whose maximum is 1/255. Preserve complete alpha of every stronger component, including fine twigs and connected 1/255 edges.',
        'local_gutter_correction': 'death_corpse_detail_margin_2_v1: clear alpha=1 only in rightmost x=1023 column; all alpha>1 ends at x=1020. Reviewed light composite.',
        'breakup_ownership': 'Whole-row owner rectangles split two portrait sheets at verified empty y=864 and y=950; retain all detached native debris. See config.json.',
        'shared_processing': 'Native registration, tone 0.75, contour audit and premultiplied resizing.'
    }
    path.write_text(json.dumps(settings, indent=2) + '\n')
