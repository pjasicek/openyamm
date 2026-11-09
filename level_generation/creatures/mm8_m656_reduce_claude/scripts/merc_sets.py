"""Keep set and region groups for the Mercenary ladder (work/face_info.npz).
Kept exactly: finger faces (finger weight > 0.5: fitted sword grip and the empty hand), small separate pieces
(<= REA_SMALL faces: studs, rivets, eyes, buckles), and the painted face features (non-skin faces of the face piece in
front of the face: moustache, lips, brows). Groups: 1 face/neck skin, 2 rest of the head set (helmet, horns, cheek
guards, hair), 3 gloves (hand weight > 0.5 outside the fingers); 0 takes the rest of the ladder budget.
-> work/keep_merc.npy, work/groups_merc.npy"""
import os
import numpy as np
fi = np.load('work/face_info.npz'); h, s, v = fi['hsv'].T; ha = fi['head_atlas']; c = fi['centroid']
SMALL = int(os.environ.get('REA_SMALL', '80'))
skin = ha & (h > 0.02) & (h < 0.11) & (s > 0.2) & (s < 0.62) & (v > 0.5)
face_piece = fi['piece'] == np.bincount(fi['piece'][ha]).argmax()
front = (c[:, 1] < -0.02) & (np.abs(c[:, 0]) < 0.07) & (c[:, 2] > 1.46) & (c[:, 2] < 1.58)
features = face_piece & ~skin & front
keep = (fi['finger'] > .5) | (fi['psize'] <= SMALL) | features
groups = np.zeros(len(h), int)
groups[ha & skin] = 1
groups[ha & ~skin] = 2
groups[(fi['hand'] > .5) & ~(fi['finger'] > .5)] = 3
groups[keep] = 0
np.save('work/keep_merc.npy', keep); np.save('work/groups_merc.npy', groups)
print('KEEP', int(keep.sum()), '(fingers', int((fi['finger'] > .5).sum()), 'small', int((fi['psize'] <= SMALL).sum()),
      'features', int(features.sum()), ')', 'groups', {g: int((groups == g).sum()) for g in range(4)})
