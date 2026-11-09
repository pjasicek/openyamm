"""Head texture set (u > 0.5) split for the ladder. The face, skull, ears and neck are kept exactly: a 70 % head cut
slid the eye and lip texture (review/close/sheet_h70.png) and a 60 % skull cut removed the pointed ears
(review/close/sheet_hair.png). The dark topknot hair (base colour luminance < 0.18 from sample_lum.py) is group 1
with its own ratio, the cape (cape_faces.npy from finger_faces.py) group 2. Writes work/keep_head.npy (with small pieces and fingers) and work/groups_hair.npy."""
import numpy as np
head = np.load('work/protect_head.npy'); lum = np.load('work/face_lum.npy')
hair = head & (lum < .18)
keep = np.load('work/keep_small.npy') | np.load('work/keep_fingers.npy') | (head & ~hair)
groups = np.where(hair, 1, 0); groups[np.load('work/cape_faces.npy') & ~keep & ~hair] = 2  # cape: group 2
np.save('work/keep_head.npy', keep); np.save('work/groups_hair.npy', groups)
print('HAIR', int(hair.sum()), 'HEAD KEPT', int((head & ~hair).sum()), 'CAPE', int((groups == 2).sum()), 'KEEP total', int(keep.sum()))
