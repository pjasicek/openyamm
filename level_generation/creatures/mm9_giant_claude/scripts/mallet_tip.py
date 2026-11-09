#!/usr/bin/env python3
"""Third pass: pull the fitted mallet's shaft tip from 1.33 to TIP (1.24 m) in work/mallet.npz, UVs unchanged (the retexture was painted on the
1.33 layout; the shaft's texture compresses 7 %). MM9 slides the right fist to 0.6-0.73 m up the shaft in the attacks; with 1.33 m the end ran
6 cm into the chest. Run once after fit_mallet_meshy.py."""
import numpy as np, sys
from pathlib import Path
p = Path(__file__).resolve().parents[1] / 'work' / 'mallet.npz'; TIP = float(sys.argv[1]) if len(sys.argv) > 1 else 1.24; HB = -0.029
Z = dict(np.load(p)); V = Z['V'].copy(); k = (TIP - HB) / (V[:, 1].max() - HB); b = V[:, 1] > HB; V[b, 1] = HB + (V[b, 1] - HB) * k
Z['V'] = V; np.savez(p, **Z); print('MALLETTIP', round(float(V[:, 1].max()), 3), 'scale', round(float(k), 3))
