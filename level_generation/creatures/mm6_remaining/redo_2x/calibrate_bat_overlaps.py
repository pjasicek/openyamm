"""Measure identical native poses across split attack sheets; apply no artwork transformations."""
import hashlib
import json

import cv2
import numpy as np
from PIL import Image, ImageDraw

from prepare_run import REPO

OUT = REPO / 'level_generation/creatures/mm6_bat/redo_2x'


def main():
    run = json.loads((OUT / 'run.json').read_text())
    jobs = [job for job in run['jobs'] if job['id'].startswith('attack_')]
    sift = cv2.SIFT_create(nfeatures=4000)
    records = {}
    for old, new in zip(jobs, jobs[1:]):
        name = new['frames'][0]
        paths = [OUT / 'cleaned' / job['id'] / (name + '.png') for job in [old, new]]
        images = [cv2.imread(str(path), cv2.IMREAD_UNCHANGED) for path in paths]
        features = [sift.detectAndCompute(cv2.cvtColor(im[:, :, :3], cv2.COLOR_BGR2GRAY),
                    (im[:, :, 3] > 128).astype('uint8') * 255) for im in images]
        matches = [m for m, n in cv2.BFMatcher().knnMatch(features[0][1], features[1][1], k=2)
                   if m.distance < .7 * n.distance]
        p = np.float32([features[0][0][m.queryIdx].pt for m in matches])
        q = np.float32([features[1][0][m.trainIdx].pt for m in matches])
        matrix, keep = cv2.estimateAffinePartial2D(p, q, method=cv2.RANSAC,
            ransacReprojThreshold=4, maxIters=5000)
        assert matrix is not None and int(keep.sum()) >= 12, new['id']
        rotation = float(np.degrees(np.arctan2(matrix[1, 0], matrix[0, 0])))
        assert abs(rotation) < 3, (new['id'], rotation)
        chosen = keep.ravel().astype(bool)
        records[new['id']] = dict(previous_job=old['id'], frame=name,
            cleaned_sha256=[hashlib.sha256(path.read_bytes()).hexdigest() for path in paths],
            paths=[str(path.relative_to(REPO)) for path in paths],
            scale_ratio=float(np.hypot(matrix[0, 0], matrix[1, 0])), fitted_rotation_degrees=rotation,
            inliers=int(keep.sum()), correspondence_points=[p[chosen].tolist(), q[chosen].tolist()],
            applied_transform='Scale only, common to the whole new batch; native anatomical translation remains separate')
        canvas = Image.new('RGB', (sum(im.shape[1] for im in images), max(im.shape[0] for im in images)),
                           (45, 45, 45))
        offset = 0
        for im in images:
            rgba = Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGRA2RGBA))
            canvas.paste(rgba, (offset, 0), rgba)
            offset += im.shape[1]
        draw = ImageDraw.Draw(canvas)
        for a, b in zip(p[chosen], q[chosen]):
            draw.line([tuple(a), (b[0] + images[0].shape[1], b[1])], fill=(210, 200, 90), width=1)
        canvas.thumbnail((1600, 700))
        canvas.save(OUT / 'review' / (new['id'] + '_overlap_correspondences.png'))
    (OUT / 'review/attack_overlap_calibration.json').write_text(json.dumps(dict(
        status='measured_correspondences_pending_visual_review', records=records), indent=2) + '\n')
    print({key: value['scale_ratio'] for key, value in records.items()})


if __name__ == '__main__':
    main()
