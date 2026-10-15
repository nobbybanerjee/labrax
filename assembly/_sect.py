"""ASCII cross-sections of a real part: python _sect.py <file> <axis 0|1|2> <pos> [<pos> ...] [--g 1.0]
Even-odd fill of the mesh cut at each position; '#' = material."""
import sys, numpy as np
sys.path.insert(0, '.')
from _realbores import rd, D, WS

args = sys.argv[1:]
g = 1.0
if '--g' in args:
    i = args.index('--g'); g = float(args[i + 1]); del args[i:i + 2]
path = args[0] if ('/' in args[0] or ':' in args[0]) else D + args[0]
ax = int(args[1]); poss = [float(p) for p in args[2:]]
T = rd(path); T = T - T.reshape(-1, 3).min(0); v = T.reshape(-1, 3)
a, b = [k for k in (0, 1, 2) if k != ax]
print(f'{path.split("/")[-1]}  bbox {v.max(0).round(2)}  cut along {"XYZ"[ax]}, rows = {"XYZ"[b]} (up), cols = {"XYZ"[a]}')
for pos in poss:
    segs = []
    for t in T:
        d = t[:, ax] - pos
        if (d > 0).all() or (d < 0).all():
            continue
        pts = []
        for i in range(3):
            p, q = t[i], t[(i + 1) % 3]
            if (p[ax] - pos) * (q[ax] - pos) < 0:
                f = (pos - p[ax]) / (q[ax] - p[ax]); pts.append(p + f * (q - p))
        if len(pts) == 2:
            segs.append((pts[0][[a, b]], pts[1][[a, b]]))
    W = int(v[:, a].max() / g) + 2; H = int(v[:, b].max() / g) + 2
    M = np.zeros((W, H), bool)
    for j in range(H):
        y = (j + 0.5) * g; xs = []
        for p, q in segs:
            if (p[1] - y) * (q[1] - y) < 0:
                xs.append(p[0] + (y - p[1]) / (q[1] - p[1]) * (q[0] - p[0]))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            M[max(0, int(xs[k] / g)):int(xs[k + 1] / g) + 1, j] = True
    print(f'--- {"XYZ"[ax]} = {pos}')
    for j in range(H - 1, -1, -1):
        print(f'{j*g:6.1f} ' + ''.join('#' if M[i, j] else '.' for i in range(W)))
