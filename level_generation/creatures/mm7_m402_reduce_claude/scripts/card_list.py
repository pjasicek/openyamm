#!/usr/bin/env python3
"""Fringe cards that mm7_m402_claude's rig left rigid on Fang_L/Fang_R or Abdomen (its fang detection took every piece
under 200 vertices in front of the body, and cards over 10 cm from a leg fell back to the body): rest positions of
their vertices per card -> work/cards.npz for export_cand.py (REA_FIX_CARDS=1 re-rigs each card on its leg).
Usage: card_list.py (work/mesh_in.npz, work/faces_info.npz, work/face_piece.npy)"""
import numpy as np
d = np.load('work/mesh_in.npz'); f = d['faces']; v = d['verts']
dom = np.load('work/faces_info.npz')['dom'].astype(str); pc = np.load('work/face_piece.npy'); sizes = np.bincount(pc)
pos, card = [], []
for p in np.unique(pc[sizes[pc] < 150]):
    sel = pc == p; vals, cnt = np.unique(dom[sel], return_counts=True); top = vals[cnt.argmax()]
    if top.startswith('Fang') or top == 'Abdomen':
        vs = np.unique(f[sel]); pos.append(v[vs]); card += [int(p)] * len(vs)
        print('CARD', int(p), top, len(vs), 'verts at', np.round(v[vs].mean(0), 2))
np.savez('work/cards.npz', pos=np.concatenate(pos), card=np.array(card))
