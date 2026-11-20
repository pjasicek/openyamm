"""Body (asm + weights) and wings -> one mesh npz with weights over a shared bone list. Optional UV npz for the body
(vertices split at seams, 'orig' index into asm, 'mat'/'matnames') and wing UVs from the wing npz.
Args: <asm npz> <body weights npz> <wings npz> <out npz> [body uv npz]"""
import sys, numpy as np
A = np.load(sys.argv[1]); BW = np.load(sys.argv[2]); WG = np.load(sys.argv[3]); OUT = sys.argv[4]
UVF = sys.argv[5] if len(sys.argv) > 5 else None
bn = [str(x) for x in BW['names']]; wn = [str(x) for x in WG['names']]
names = list(dict.fromkeys(bn + wn)); ix = {n: i for i, n in enumerate(names)}
def expand(W, nm):
    out = np.zeros((len(W), len(names)), np.float32); out[:, [ix[n] for n in nm]] = W; return out
if UVF:
    U = np.load(UVF); orig = U['orig']; bco = U['co']; btri = U['tri']; buv = U['uv']; bmat = U['mat']; matnames = [str(x) for x in U['matnames']]
    bW = expand(BW['W'], bn)[orig]; bcomp = A['comp'][orig]
else:
    bco, btri = A['co'], A['tri']; buv = np.zeros((len(bco), 2)); bmat = np.zeros(len(btri), int); matnames = ['Ebora']
    bW = expand(BW['W'], bn); bcomp = A['comp']; orig = np.arange(len(bco))
wW = expand(WG['W'], wn); n0 = len(bco)
wmat = len(matnames); matnames = matnames + ['EboraWing']
co = np.vstack([bco, WG['co']]); tri = np.vstack([btri, WG['tri'] + n0]); uv = np.vstack([buv, WG['uv']])
mat = np.r_[bmat, np.full(len(WG['tri']), wmat)]
comp = np.r_[bcomp, 100 + WG['part']]
W = np.vstack([bW, wW]); W /= np.maximum(W.sum(1, keepdims=True), 1e-12)
np.savez(OUT, co=co, tri=tri, uv=uv, mat=mat, matnames=np.array(matnames), W=W, names=np.array(names), comp=comp, orig=np.r_[orig, -1 - np.arange(len(WG['co']))])
print('MERGED', len(co), len(tri), 'materials', matnames, 'bones', len(names))
