"""Every cylindrical bore on every real Lab Rax frame part (clean CAD meshes, not g-code)."""
import numpy as np, struct
from collections import defaultdict
D = 'C:/Users/nabaru/Downloads/CAD/LabRax/'
WS = 'C:/Users/nabaru/.kiro/crew/workspace/'


def rd(p):
    with open(p, 'rb') as f:
        head = f.read(80); rest = f.read()
    if head[:5].lower() == b'solid' and b'facet' in rest[:400]:
        v = [float(w) for ln in (head + rest).decode('ascii', 'ignore').splitlines()
             if ln.strip().startswith('vertex') for w in ln.split()[1:4]]
        return np.array(v, 'f4').reshape(-1, 3, 3)
    n = struct.unpack('<I', rest[:4])[0]
    d = np.frombuffer(rest[4:4 + n * 50], dtype=np.uint8).reshape(n, 50)
    return d[:, 12:48].copy().view('<f4').reshape(-1, 3, 3)


def bores(T):
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
    out = []
    for ax in (0, 1, 2):
        a, b = [k for k in (0, 1, 2) if k != ax]
        sel = T[np.abs(n[:, ax]) < 0.15]
        if len(sel) < 10:
            continue
        pts = np.unique(sel.reshape(-1, 3).round(2), axis=0)
        g = 1.0; key = defaultdict(list)
        for i, p in enumerate(pts):
            key[(int(p[a] // g), int(p[b] // g))].append(i)
        seen = set()
        for k0 in list(key):
            if k0 in seen:
                continue
            st = [k0]; seen.add(k0); comp = []
            while st:
                k = st.pop(); comp += key[k]
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        kk = (k[0] + dx, k[1] + dy)
                        if kk in key and kk not in seen:
                            seen.add(kk); st.append(kk)
            q = pts[comp]
            if len(q) < 10:
                continue
            c = q[:, [a, b]].mean(0); r = np.linalg.norm(q[:, [a, b]] - c, axis=1)
            if 1.4 < r.mean() < 6.5 and r.std() < 0.35 and np.ptp(q[:, ax]) > 0.8:
                out.append(('XYZ'[ax], 'XYZ'[a], c[0], 'XYZ'[b], c[1], 2 * r.mean(), q[:, ax].min(), q[:, ax].max()))
    return out


if __name__ == "__main__":
  PARTS = [('5U post', WS + 'cad/spec/labrax/5U+Vertical+Post.stl'),
           ('Solid Horizontal Edge', D + 'Solid+Horizontal+Edge.stl'),
           ('Top Edge', D + 'Top+Edge.stl'),
           ('Handle', D + 'Handle.stl'),
           ('Foot', WS + 'cad/spec/labrax/Foot.stl'),
           ('Top Panel', D + 'Top+Panel.stl'),
           ('Post Joiner', D + 'Brass+Insert+Post+Joiner.stl')]
  for nm, p in PARTS:
      T = rd(p); T = T - T.reshape(-1, 3).min(0); v = T.reshape(-1, 3)
      print(f'\n=== {nm}   {v[:,0].max():.2f} x {v[:,1].max():.2f} x {v[:,2].max():.2f}')
      for ax, an, a, bn, b, d, lo, hi in sorted(bores(T)):
          print(f'   axis {ax}  {an}={a:7.2f} {bn}={b:7.2f}  d={d:5.2f}  {ax} {lo:6.2f}..{hi:6.2f}')
