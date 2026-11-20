"""Independent evidence for split-sheet scale continuity; no transformations or acceptance."""
import hashlib
import json
import argparse
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

from prepare_run import REPO


def main(project):
    out = Path(project).resolve()/'redo_2x'
    run = json.loads((out/'run.json').read_text())
    calibration_path = out/'calibration.json'
    calibration = json.loads(calibration_path.read_text()) if calibration_path.exists() else {}
    previous, records = {}, {}
    sift = cv2.SIFT_create(nfeatures=4000)
    for job in run['jobs']:
        if not job.get('selected_raw'):
            continue
        old = previous.get(job['scope'])
        previous[job['scope']] = job
        if not old:
            continue
        shared = sorted(set(old['frames']) & set(job['frames']))
        if not shared:
            continue
        name = shared[0]
        paths = [out/'cleaned'/j['id']/(name+'.png') for j in [old, job]]
        images = [cv2.imread(str(path), cv2.IMREAD_UNCHANGED) for path in paths]
        features = [sift.detectAndCompute(cv2.cvtColor(im[:, :, :3], cv2.COLOR_BGR2GRAY),
            (im[:, :, 3] > 128).astype('uint8')*255) for im in images]
        matches = [m for m, n in cv2.BFMatcher().knnMatch(features[0][1], features[1][1], k=2)
                   if m.distance < .7*n.distance]
        record = dict(previous_job=old['id'], frame=name,
            paths=[str(path.relative_to(REPO)) for path in paths],
            hashes=[hashlib.sha256(path.read_bytes()).hexdigest() for path in paths])
        records[job['id']] = record
        if len(matches) < 12:
            record['status'] = 'insufficient_feature_matches'
            continue
        p = np.float32([features[0][0][m.queryIdx].pt for m in matches])
        q = np.float32([features[1][0][m.trainIdx].pt for m in matches])
        matrix, keep = cv2.estimateAffinePartial2D(p, q, method=cv2.RANSAC,
            ransacReprojThreshold=4, maxIters=5000)
        if matrix is None or int(keep.sum()) < 12:
            record['status'] = 'insufficient_inlier_matches'
            continue
        ratio = float(np.hypot(matrix[0, 0], matrix[1, 0]))
        rotation = float(np.degrees(np.arctan2(matrix[1, 0], matrix[0, 0])))
        chosen = keep.ravel().astype(bool)
        record.update(status='measured_pending_visual_review', scale_ratio=ratio,
            fitted_rotation_degrees=rotation, inliers=int(keep.sum()),
            correspondence_points=[p[chosen].tolist(), q[chosen].tolist()])
        if old['id'] in calibration and job['id'] in calibration:
            old_scale = calibration[old['id']]['generated_sampling']
            new_scale = calibration[job['id']]['generated_sampling']
            record['registered_scale_disagreement'] = new_scale/(old_scale*ratio)-1
        canvas = Image.new('RGB', (sum(im.shape[1] for im in images), max(im.shape[0] for im in images)),
                           (45, 45, 45))
        offset = 0
        for im in images:
            rgba = Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGRA2RGBA))
            canvas.paste(rgba, (offset, 0), rgba)
            offset += im.shape[1]
        draw = ImageDraw.Draw(canvas)
        for a, b in zip(p[chosen], q[chosen]):
            draw.line([tuple(a), (b[0]+images[0].shape[1], b[1])], fill=(210, 200, 90), width=1)
        canvas.thumbnail((1400, 600))
        canvas.save(out/'review'/(job['id']+'_overlap_correspondences.png'))
    (out/'review/overlap_calibration.json').write_text(json.dumps(dict(
        status='diagnostic_only_pending_visual_review', records=records), indent=2)+'\n')
    print(json.dumps({name: {k: row[k] for k in ['status', 'registered_scale_disagreement'] if k in row}
                      for name, row in records.items()}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('project', nargs='?', default=str(REPO/'level_generation/creatures/mm6_bh'))
    main(parser.parse_args().project)
