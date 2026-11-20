"""Per clip at 48 fps, MM9 source vs ours, landmark vertices fixed in the bind pose (independent of the weights):
- head_dir: skull -> beak tip direction in the Xbody frame; angle ours vs MM9 (deg)
- head_up: skull -> crown direction in the Xbody frame; angle ours vs MM9
- fold (ours): change of the angle between skull->tip and skull->crown against the bind pose (a rigid head keeps 0)
- stretch (ours): skull->tip length / bind length
- toe_bend: signed angle tarsus (Xfoot joint -> ankle) vs toes (ankle -> toe tips) in the leg plane, per side;
  ours vs MM9 difference (deg)
Usage: head_angles.py <mm9 source glb> <our glb> [--verbose] [--json out.json]"""
import sys, json
import numpy as np
sys.path.insert(0, '/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/floor')
from glb_pose import Glb, Model


def merged(model):
    """all LOD0 primitives of a Model as one: (prim dict with positions/joints/weights/triangles, posed(world))"""
    ps = model.primitives
    off = np.cumsum([0] + [len(p['positions']) for p in ps])
    prim = {'positions': np.concatenate([p['positions'] for p in ps]),
            'joints': np.concatenate([p['joints'] for p in ps]),
            'weights': np.concatenate([p['weights'] for p in ps]),
            'triangles': np.concatenate([p['triangles'] + o for p, o in zip(ps, off)])}

    def posed(W):
        return np.concatenate([q for q, _ in model.skinned_positions(W)])
    return prim, posed


ROLE = {'Standing': ['fly'], 'Running': ['fly'], 'Fidget': ['fidgetAir1'], 'AttackMelee': ['HattackAir1'],
        'Hit': ['winceair1'], 'Death': ['dieair1', 'fall1', 'falldown1']}
RATE = {'Running': 4 / 3}


class M:
    def __init__(self, path, mm9):
        self.m = Model(Glb(path))
        N = self.m.glb.json['nodes']
        self.idx = {N[j]['name']: j for j in self.m.joints}
        prim, self.posed = merged(self.m)
        jn = [N[j]['name'] for j in self.m.joints]
        dom = prim['joints'][np.arange(len(prim['joints'])), prim['weights'].argmax(1)]
        self.dom = np.array([jn[d] for d in dom])
        Wb, P = self.pose(None)
        self.Wb = Wb
        B = Wb[self.idx['Xbody']][:3, :3]
        self.Rb0 = B / np.linalg.norm(B[:, 0])
        L = P @ self.Rb0   # bind positions in the body frame
        jw = lambda n: Wb[self.idx[n]][:3, 3] @ self.Rb0
        hj = jw('Xhead')
        fwd = jw('Xbeak') - jw('XneckA'); fwd[1] = 0; fwd /= np.linalg.norm(fwd)   # horizontal forward (Y up)
        up = np.array([0, 1.0, 0])
        if mm9:
            head = np.nonzero(np.isin(self.dom, ['Xhead', 'Xheadpiv']))[0]
            beak = np.nonzero(np.isin(self.dom, ['Xbeak', 'Xjawpiv']))[0]
            skull = head
            sc = L[head].mean(0)
        else:
            # skull = the two eye pieces (small separate components nearest the head joint)
            tri = prim['triangles']
            parent = np.arange(len(P))

            def find(x):
                while parent[x] != x:
                    parent[x] = parent[parent[x]]; x = parent[x]
                return x
            # weld UV-seam duplicates (same position) so components are geometric pieces
            key = {}
            for i, p in enumerate(np.round(P, 6)):
                k = tuple(p)
                if k in key:
                    parent[find(i)] = find(key[k])
                else:
                    key[k] = i
            for t in tri:
                a, b, c = find(t[0]), find(t[1]), find(t[2])
                parent[b] = a; parent[find(c)] = a
            roots = np.array([find(i) for i in range(len(P))])
            ids, cnt = np.unique(roots, return_counts=True)
            small = ids[cnt < max(200, 0.15 * cnt.max())]
            cands = sorted(small, key=lambda r: np.linalg.norm(L[roots == r].mean(0) - hj))[:2]
            skull = np.nonzero(np.isin(roots, cands))[0]
            sc = L[skull].mean(0)
            ea, eb = (np.nonzero(roots == c)[0] for c in cands)
            if L[ea].mean(0)[0] < L[eb].mean(0)[0]:
                ea, eb = eb, ea
            self.eyes = (ea, eb)
            beak = np.nonzero(self.dom == 'Xbeak')[0]
            if len(beak) < 10:
                # grafted head: the beak is rigid on Xhead; its tip is the Socket_Mouth node
                sock = next(i for i, nd in enumerate(N) if nd.get('name') == 'Socket_Mouth')
                stip = Wb[sock][:3, 3] @ self.Rb0
                beak = np.nonzero(np.linalg.norm(L - stip, axis=1) < np.linalg.norm(stip - sc) * 0.55)[0]
        d = L[beak] - sc
        tipi = beak[np.argmax(d @ (fwd - up) / np.sqrt(2) + 0.0 * np.linalg.norm(d, axis=1))]
        # tip = the beak vertex farthest along forward-down from the skull (both models bind the beak down)
        dd = np.linalg.norm(L[beak] - sc, axis=1)
        tipi = beak[np.argsort(dd)[-max(3, len(beak) // 10):]]
        reg = np.nonzero(np.linalg.norm(L - sc, axis=1) < (0.05 if not mm9 else 0.06))[0]
        crown = reg[np.argsort(L[reg] @ up)[-max(3, len(reg) // 40):]]
        self.sel = {'skull': skull, 'tip': tipi, 'crown': crown}
        self.mm9 = mm9
        # feet: ankle = Xtoe joint; tarsus from the Xfoot joint; toe tips = Xtoe-dominated (or nearest) vertices
        # farthest from the ankle
        for side, (f, t) in {'L': ('Xfoot', 'Xtoe'), 'R': ('Xfoot01', 'Xtoe01')}.items():
            ank = jw(t)
            cand = np.nonzero(self.dom == t)[0]
            if len(cand) < 5:
                cand = np.nonzero(np.linalg.norm(L - ank, axis=1) < 0.06)[0]
            dist = np.linalg.norm(L[cand] - ank, axis=1)
            self.sel['toe' + side] = cand[np.argsort(dist)[-max(3, len(cand) // 5):]]
        self.bind = self.measure(Wb, P)

    def pose(self, clip, t=0.0):
        W = self.m.world(self.m.sample(clip, t) if clip else {})
        return W, self.posed(W)

    def measure(self, W, P):
        B = W[self.idx['Xbody']][:3, :3]
        Rb = B / np.linalg.norm(B[:, 0])
        L = P @ Rb
        s = L[self.sel['skull']].mean(0)
        out = {'dir': L[self.sel['tip']].mean(0) - s, 'up': L[self.sel['crown']].mean(0) - s}
        # lateral axis of the head: ours from the two eyes, MM9's from Xhead's rotation applied to the body lateral
        if self.mm9:
            Wb = self.Wb
            R = (W[self.idx['Xhead']][:3, :3] / np.linalg.norm(W[self.idx['Xhead']][:3, 0])) @ \
                (Wb[self.idx['Xhead']][:3, :3] / np.linalg.norm(Wb[self.idx['Xhead']][:3, 0])).T
            lat = Rb.T @ R @ self.Rb0 @ np.array([1.0, 0, 0])
        else:
            lat = L[self.eyes[0]].mean(0) - L[self.eyes[1]].mean(0)
        dn = out['dir'] / np.linalg.norm(out['dir'])
        lat = lat - (lat @ dn) * dn
        lat /= np.linalg.norm(lat)
        out['frame'] = np.stack([dn, lat, np.cross(dn, lat)])   # rows: beak, lateral, head up (+/- by convention)
        for side, (f, t) in {'L': ('Xfoot', 'Xtoe'), 'R': ('Xfoot01', 'Xtoe01')}.items():
            a = W[self.idx[f]][:3, 3] @ Rb
            k = W[self.idx[t]][:3, 3] @ Rb
            tips = L[self.sel['toe' + side]].mean(0)
            tar, toe = k - a, tips - k
            n = np.cross(tar, toe)
            out['tarsus' + side] = tar; out['toe' + side] = toe
            # signed bend in the plane of the leg; sign by the lateral body axis (X)
            out['bend' + side] = ang(tar, toe) * (1 if n[0] >= 0 else -1)
        return out


def ang(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b)
    return float(np.degrees(np.arccos(np.clip(a @ b, -1, 1))))


def main():
    src, ours = M(sys.argv[1], True), M(sys.argv[2], False)
    verbose = '--verbose' in sys.argv
    print('bind dir mm9', np.round(src.bind['dir'] / np.linalg.norm(src.bind['dir']), 3), 'ours',
          np.round(ours.bind['dir'] / np.linalg.norm(ours.bind['dir']), 3),
          'angle %.1f' % ang(src.bind['dir'], ours.bind['dir']))
    print('bind up  mm9', np.round(src.bind['up'] / np.linalg.norm(src.bind['up']), 3), 'ours',
          np.round(ours.bind['up'] / np.linalg.norm(ours.bind['up']), 3))
    print('bind toe bend L/R mm9 %.0f/%.0f ours %.0f/%.0f' % (src.bind['bendL'], src.bind['bendR'],
                                                             ours.bind['bendL'], ours.bind['bendR']))
    report = {}
    fold0 = ang(ours.bind['dir'], ours.bind['up'])
    len0 = np.linalg.norm(ours.bind['dir'])
    for role, names in ROLE.items():
        dur = [src.m.clip_times(n)[-1] - src.m.clip_times(n)[0] for n in names]
        T = ours.m.clip_times(role)[-1]
        rate = RATE.get(role, 1.0)
        rows = []
        for k in range(int(round(T * 48)) + 1):
            t = min(k / 48, T)
            ts = t * rate
            ci = 0
            while ci < len(names) - 1 and ts > dur[ci] + 1e-9:
                ts -= dur[ci]; ci += 1
            fs = src.measure(*src.pose(names[ci], src.m.clip_times(names[ci])[0] + ts))
            fo = ours.measure(*ours.pose(role, t))
            Rd = fo['frame'].T @ fs['frame']
            full = float(np.degrees(np.arccos(np.clip((np.trace(Rd) - 1) / 2, -1, 1))))
            roll = float(np.degrees(np.arccos(np.clip(fo['frame'][1] @ fs['frame'][1], -1, 1))))
            hup = float(np.degrees(np.arccos(np.clip(fo['frame'][2] @ fs['frame'][2], -1, 1))))
            row = {'t': round(t, 4), 'roll_vs_mm9': roll, 'head_up_vs_mm9': hup, 'orient_vs_mm9': full,
                   'dir_vs_mm9': ang(fo['dir'], fs['dir']),
                   'up_vs_mm9': ang(fo['up'], fs['up']),
                   'mm9_turn': ang(fs['dir'], src.bind['dir']),
                   'ours_turn': ang(fo['dir'], ours.bind['dir']),
                   'fold': abs(ang(fo['dir'], fo['up']) - fold0),
                   'stretch': float(np.linalg.norm(fo['dir']) / len0),
                   'toeL_vs_mm9': ang(fo['toeL'], fs['toeL']), 'toeR_vs_mm9': ang(fo['toeR'], fs['toeR']),
                   'bendL_mm9': fs['bendL'], 'bendL_ours': fo['bendL']}
            rows.append(row)
        report[role] = rows
        keys = ['dir_vs_mm9', 'roll_vs_mm9', 'head_up_vs_mm9', 'orient_vs_mm9', 'fold', 'toeL_vs_mm9', 'toeR_vs_mm9']
        print(f'{role:12s} n={len(rows):3d} ' + ' '.join(
            f'{k} max {max(r[k] for r in rows):5.1f}@{rows[int(np.argmax([r[k] for r in rows]))]["t"]:.2f}'
            f' mean {np.mean([r[k] for r in rows]):5.1f}' for k in keys)
            + ' stretch %.2f-%.2f' % (min(r['stretch'] for r in rows), max(r['stretch'] for r in rows)))
        if verbose:
            for r in rows:
                print('   ', ' '.join(f'{k}={v:.1f}' for k, v in r.items()))
    if '--json' in sys.argv:
        json.dump(report, open(sys.argv[sys.argv.index('--json') + 1], 'w'), indent=0)


main()
