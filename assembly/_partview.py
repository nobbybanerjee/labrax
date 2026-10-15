"""Shaded z-buffer views of single real parts, optionally clipped to a box, to read mating faces.
   python _partview.py out.png  file|key  az el  [x0 x1 y0 y1 z0 z1]  [file az el [box]] ..."""
import sys, math, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, '.')
from _realbores import rd, D, WS


def render(T, az, el, W=520, H=520, col=(150, 160, 185)):
    a, e = math.radians(az), math.radians(el)
    d = np.array([math.cos(e) * math.sin(a), -math.cos(e) * math.cos(a), -math.sin(e)])
    r = np.cross(d, [0, 0, 1.]); r = r / np.linalg.norm(r) if np.linalg.norm(r) > 1e-6 else np.array([1., 0, 0])
    u = np.cross(r, d); u /= np.linalg.norm(u)
    v = T.reshape(-1, 3); cen = (v.min(0) + v.max(0)) / 2
    xs, ys = (v - cen) @ r, (v - cen) @ u
    s = min((W - 30) / np.ptp(xs), (H - 30) / np.ptp(ys))
    img = np.full((H, W, 3), 248, np.uint8); zb = np.full((H, W), 1e18)
    L = np.array([.35, -.55, .76]); L /= np.linalg.norm(L)
    vv = T - cen; X, Y, Z = vv @ r, vv @ u, vv @ d
    PX = (X * s + W / 2).astype(np.int32); PY = (H / 2 - Y * s).astype(np.int32)
    n = np.cross(vv[:, 1] - vv[:, 0], vv[:, 2] - vv[:, 0]); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    sh = np.abs(n @ L) * .7 + .3
    for k in range(len(vv)):
        px, py, pz = PX[k], PY[k], Z[k]
        x0, x1 = max(px.min(), 0), min(px.max(), W - 1); y0, y1 = max(py.min(), 0), min(py.max(), H - 1)
        if x1 < x0 or y1 < y0: continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        d0 = (px[1] - px[0]) * (gy - py[0]) - (py[1] - py[0]) * (gx - px[0])
        d1 = (px[2] - px[1]) * (gy - py[1]) - (py[2] - py[1]) * (gx - px[1])
        d2 = (px[0] - px[2]) * (gy - py[2]) - (py[0] - py[2]) * (gx - px[2])
        m = ((d0 >= 0) & (d1 >= 0) & (d2 >= 0)) | ((d0 <= 0) & (d1 <= 0) & (d2 <= 0))
        if not m.any(): continue
        sel = m & (pz.mean() < zb[y0:y1 + 1, x0:x1 + 1])
        if not sel.any(): continue
        zb[y0:y1 + 1, x0:x1 + 1] = np.where(sel, pz.mean(), zb[y0:y1 + 1, x0:x1 + 1])
        blk = img[y0:y1 + 1, x0:x1 + 1]; blk[sel] = (np.array(col) * sh[k]).clip(0, 255).astype(np.uint8)
        img[y0:y1 + 1, x0:x1 + 1] = blk
    return Image.fromarray(img)


KEYS = {'post': WS + 'cad/spec/labrax/5U+Vertical+Post.stl', 'he': D + 'Solid+Horizontal+Edge.stl',
        'te': D + 'Top+Edge.stl', 'handle': D + 'Handle.stl', 'foot': WS + 'cad/spec/labrax/Foot.stl'}
if __name__ == '__main__':
    out, rest = sys.argv[1], sys.argv[2:]
    tiles = []
    while rest:
        f, az, el = rest[0], float(rest[1]), float(rest[2]); rest = rest[3:]
        box = None
        if len(rest) >= 6 and all(t.replace('.', '').replace('-', '').isdigit() for t in rest[:6]):
            box = [float(t) for t in rest[:6]]; rest = rest[6:]
        T = rd(KEYS.get(f, f)); T = T - T.reshape(-1, 3).min(0)
        if box:
            c = T.mean(1)
            m = ((c[:, 0] >= box[0]) & (c[:, 0] <= box[1]) & (c[:, 1] >= box[2]) & (c[:, 1] <= box[3])
                 & (c[:, 2] >= box[4]) & (c[:, 2] <= box[5]))
            T = T[m]
        im = render(T, az, el); ImageDraw.Draw(im).text((8, 6), f'{f} az{az:.0f} el{el:.0f} {box or ""}', fill=(20, 20, 20))
        tiles.append(im)
    sheet = Image.new('RGB', (520 * min(3, len(tiles)), 520 * ((len(tiles) + 2) // 3)), (255, 255, 255))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % 3) * 520, (i // 3) * 520))
    sheet.save(out); print('saved', out, sheet.size)
    