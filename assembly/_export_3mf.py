"""Write the whole rack as ONE 3MF assembly: every part a separate named, coloured object, in final
rack coordinates (mm, z = 0 at the bottom of the feet). Opens in OrcaSlicer, Bambu Studio, Fusion,
PrusaSlicer, Windows 3D Viewer.
    python _export_3mf.py   ->  out/rack_assembly_17U.3mf"""
import json, os, sys, zipfile
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from rack_layout import read_stl

OUT = os.path.join(HERE, "out")
FRAME = [("Lab Rax 5U posts x12", "frame_posts", "#8F7DDB"),
         ("1U extensions x4", "frame_joiners", "#5F6BD6"),
         ("Top Edges x4 + Horizontal Edges x4 (base + top frames)", "frames", "#3F4654"),
         ("Feet x4", "feet", "#202428"),
         ("Handles x2", "handles", "#E69650"),
         ("Hex bottom panel + SmartiPi top panel", "bottom_panel", "#9AA3B0"),
         ("Side panels x2 (labrax-hws)", "side_panels", "#C2C8D2")]
NICE = {"pc_psu_hw": "ATX PSU (RM1000e size)", "itx_hw": "mini-ITX board + AXP90 cooler",
        "gpu_card": "RTX 3090 Ti FTW3", "sbc_holders": "Pi holders (4x Pi 4, 2x Pi 5/3)"}


def mesh_xml(T, oid, name, pid):
    v = T.reshape(-1, 3).astype(np.float64).round(4)
    uniq, inv = np.unique(v, axis=0, return_inverse=True)
    tri = inv.reshape(-1, 3)
    tri = tri[(tri[:, 0] != tri[:, 1]) & (tri[:, 1] != tri[:, 2]) & (tri[:, 0] != tri[:, 2])]
    vs = "".join(f'<vertex x="{a:.4f}" y="{b:.4f}" z="{c:.4f}"/>' for a, b, c in uniq)
    ts = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in tri)
    return (f'<object id="{oid}" name="{name}" type="model" pid="1" pindex="{pid}">'
            f'<mesh><vertices>{vs}</vertices><triangles>{ts}</triangles></mesh></object>'), len(tri)


def main():
    L = json.load(open(os.path.join(OUT, "LAYOUT.json")))
    parts = list(FRAME)
    for m in L["modules"]:
        for f in m.get("files", []):
            nm = NICE.get(f, m["label"] if f == m["key"] else f"{m['label']} - {f}")
            parts.append((nm.replace("·", "-"), f, m["colour"].upper()))
    objs, mats, total = [], [], 0
    for i, (name, f, col) in enumerate(parts):
        p = os.path.join(OUT, f + ".stl")
        if not os.path.exists(p):
            print("  skip (missing)", f); continue
        xml, n = mesh_xml(read_stl(p), len(objs) + 2, name.replace('"', "'").replace("&", "and"), len(mats))
        objs.append(xml); mats.append(f'<base name="{f}" displaycolor="{col}FF"/>'); total += n
        print(f"  {n:7d} tris  {name}")
    build = "".join(f'<item objectid="{k + 2}"/>' for k in range(len(objs)))
    model = ('<?xml version="1.0" encoding="UTF-8"?>'
             '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             '<metadata name="Title">Lab Rax 17U - nabaru</metadata>'
             f'<resources><basematerials id="1">{"".join(mats)}</basematerials>{"".join(objs)}</resources>'
             f'<build>{build}</build></model>')
    ct = ('<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
            '</Relationships>')
    dst = os.path.join(OUT, "rack_assembly_17U.3mf")
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct); z.writestr("_rels/.rels", rels); z.writestr("3D/3dmodel.model", model)
    print(f"{dst}: {len(objs)} parts, {total} triangles, {os.path.getsize(dst) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
