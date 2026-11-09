"""Reference for the collapse gate on the mouth: the bind has the jaw closed, so the mouth's bind faces are already folded and cannot be the reference. Each head face's reference is Meshy's open surface, turned rigidly by that face's own jaw angle into the bind. Writes work/head_ref.npz: nref, aref for the head primitive's faces, in file order."""
import numpy as np
D = np.load('work/final.npz'); J = np.load('work/joined.npz'); H = np.load('work/head1.npz')
vm = D['vmap']; tri = D['tri']; mat = D['mat']; nb = int(J['nb']); nh = int(J['nh'])
HM = np.array([0, -.07, -.13]); A = np.radians(25.8); S = .53; c_, s_ = np.cos(A), np.sin(A); RX = np.array([[1, 0, 0], [0, c_, -s_], [0, s_, c_]]); HT = np.array([0, .285, .023])
th = float(H['theta']); k = J['jawk'][vm]; up = J['co_up'][vm]; co = D['co']
F = tri[mat == 1]
kf = k[F].mean(1); a = kf * th
rel = up[F] - HM; y, z = rel[..., 1].copy(), rel[..., 2].copy(); ca, sa = np.cos(a)[:, None], np.sin(a)[:, None]
rel[..., 1] = y * ca + z * sa; rel[..., 2] = -y * sa + z * ca
Q = (rel @ RX.T) * S
n = np.cross(Q[:, 1] - Q[:, 0], Q[:, 2] - Q[:, 0]); ar = np.linalg.norm(n, axis=1) / 2
strip = np.isin(J['jawk'][vm][F].argmax(1), [-1])
# strip faces and rigid head parts keep the bind as reference
b = co[F]; nb_ = np.cross(b[:, 1] - b[:, 0], b[:, 2] - b[:, 0]); ab = np.linalg.norm(nb_, axis=1) / 2
use = kf > 1e-3
n[~use] = nb_[~use]; ar[~use] = ab[~use]
np.savez('work/head_ref.npz', nref=n, aref=ar, use=use); print('head_ref', len(F), int(use.sum()))
