"""Counterbore-aware hole finder: clusters vertical-wall points per axis, then splits each cluster
along the axis into constant-radius steps (hole + counterbore)."""
import sys, numpy as np
from collections import defaultdict
sys.path.insert(0, '.')
def holes(T, ax):
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
    a, b = [k for k in (0, 1, 2) if k != ax]
    pts = np.unique(T[np.abs(n[:, ax]) < 0.15].reshape(-1, 3).round(2), axis=0)
    key = defaultdict(list)
    for i, p in enumerate(pts): key[(int(p[a] // 1.0), int(p[b] // 1.0))].append(i)
    seen, out = set(), []
    for k0 in list(key):
        if k0 in seen: continue
        st = [k0]; seen.add(k0); comp = []
        while st:
            k = st.pop(); comp += key[k]
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    kk = (k[0] + dx, k[1] + dy)
                    if kk in key and kk not in seen: seen.add(kk); st.append(kk)
        q = pts[comp]
        if len(q) < 8: continue
        c = q[:, [a, b]].mean(0); r = np.linalg.norm(q[:, [a, b]] - c, axis=1)
        if not (1.4 < r.min() and r.max() < 7.0 and np.ptp(q[:, ax]) > 0.8): continue
        # ring test: points spread around the centre in all four quadrants
        ang = np.arctan2(*(q[:, [b, a]] - c[::-1]).T)
        if len(np.unique((ang // (np.pi / 2)).astype(int))) < 4: continue
        steps = []
        for rr in np.unique(r.round(1)):
            m = np.abs(r - rr) < 0.3
            if m.sum() >= 4: steps.append((round(2 * rr, 1), q[m, ax].min(), q[m, ax].max()))
        out.append(('XYZ'[ax], 'XYZ'[a], c[0], 'XYZ'[b], c[1], steps))
    return out
if __name__ == '__main__':
    for f in sys.argv[1:]:
        Q = np.load(f); v = Q.reshape(-1, 3)
        print(f'=== {f}  bbox {v.max(0).round(2)}')
        for ax in (0, 1, 2):
            for h in holes(Q, ax):
                ax_, an, p, bn, q, steps = h
                st = ', '.join(f'd{d} {ax_}{lo:.1f}..{hi:.1f}' for d, lo, hi in steps[:4])
                print(f'   axis {ax_}  {an}={p:7.2f} {bn}={q:7.2f}   {st}')
