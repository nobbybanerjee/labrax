"""Multi-colour close-up of one rack corner from the assembled out/*.stl, to check the real joints.
   python _corner.py out.png x0 x1 y0 y1 z0 z1"""
import sys, math, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, '.')
from rack_layout import read_stl

PARTS = [('frame_posts', (150, 140, 215)), ('frames', (90, 100, 120)), ('side_panels', (200, 205, 215)),
         ('bottom_panel', (140, 190, 230)), ('feet', (60, 60, 60)), ('handles', (230, 150, 80)),
         ('frame_joiners', (95, 107, 214))]
PANEL = (200, 205, 215)


def gather(box):
    T, C = [], []
    for f, col in PARTS:
        try:
            v = read_stl(f'out/{f}.stl').reshape(-1, 3, 3)
        except FileNotFoundError:
            continue
        c = v.mean(1)
        m = ((c[:, 0] > box[0]) & (c[:, 0] < box[1]) & (c[:, 1] > box[2]) & (c[:, 1] < box[3])
             & (c[:, 2] > box[4]) & (c[:, 2] < box[5]))
        T.append(v[m]); C += [col] * int(m.sum())
    return np.concatenate(T), np.array(C, float)


def render_multi(T, C, az, el, W=620, H=620):
    a, e = math.radians(az), math.radians(el)
    d = np.array([math.cos(e) * math.sin(a), -math.cos(e) * math.cos(a), -math.sin(e)])
    r = np.cross(d, [0, 0, 1.]); r /= np.linalg.norm(r); u = np.cross(r, d); u /= np.linalg.norm(u)
    v = T.reshape(-1, 3); cen = (v.min(0) + v.max(0)) / 2
    s = min((W - 30) / np.ptp((v - cen) @ r), (H - 30) / np.ptp((v - cen) @ u))
    img = np.full((H, W, 3), 248, np.uint8); zb = np.full((H, W), 1e18)
    L = np.array([.35, -.55, .76]); L /= np.linalg.norm(L)
    vv = T - cen; X, Y, Z = vv @ r, vv @ u, vv @ d
    PX = (X * s + W / 2).astype(np.int32); PY = (H / 2 - Y * s).astype(np.int32)
    n = np.cross(vv[:, 1] - vv[:, 0], vv[:, 2] - vv[:, 0]); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    sh = np.abs(n @ L) * .7 + .3
    for k in range(len(vv)):
        px, py = PX[k], PY[k]
        x0, x1 = max(px.min(), 0), min(px.max(), W - 1); y0, y1 = max(py.min(), 0), min(py.max(), H - 1)
        if x1 < x0 or y1 < y0: continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        d0 = (px[1] - px[0]) * (gy - py[0]) - (py[1] - py[0]) * (gx - px[0])
        d1 = (px[2] - px[1]) * (gy - py[1]) - (py[2] - py[1]) * (gx - px[1])
        d2 = (px[0] - px[2]) * (gy - py[2]) - (py[0] - py[2]) * (gx - px[2])
        m = ((d0 >= 0) & (d1 >= 0) & (d2 >= 0)) | ((d0 <= 0) & (d1 <= 0) & (d2 <= 0))
        sel = m & (Z[k].mean() < zb[y0:y1 + 1, x0:x1 + 1])
        if not sel.any(): continue
        zb[y0:y1 + 1, x0:x1 + 1] = np.where(sel, Z[k].mean(), zb[y0:y1 + 1, x0:x1 + 1])
        blk = img[y0:y1 + 1, x0:x1 + 1]; blk[sel] = (C[k] * sh[k]).clip(0, 255).astype(np.uint8)
        img[y0:y1 + 1, x0:x1 + 1] = blk
    return Image.fromarray(img)


if __name__ == '__main__':
    out = sys.argv[1]; box = [float(t) for t in sys.argv[2:8]]
    T, C = gather(box)
    views = [(150, 25, 'outside, front-right'), (215, 30, 'inside, from rear-left'),
             (90, 0, 'from +X, side panel hidden')]
    tiles = []
    for az, el, lab in views:
        TT, CC = T, C
        if 'hidden' in lab:
            keep = ~np.all(C == np.array(PANEL, float), axis=1); TT, CC = T[keep], C[keep]
        im = render_multi(TT, CC, az, el); ImageDraw.Draw(im).text((8, 6), lab, fill=(0, 0, 0)); tiles.append(im)
    sheet = Image.new('RGB', (620 * len(tiles), 620), 'white')
    for i, t in enumerate(tiles): sheet.paste(t, (620 * i, 0))
    sheet.save(out); print('saved', out)
