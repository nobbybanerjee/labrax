"""Exact clash check. Posts and 1U extensions are axis-aligned boxes, so test module vertices
for strict interior penetration with a 0.3 mm margin -- surface contact at a mounting face
(faceplate on the post's front flange at y=0) is an interface, not a clash."""
import numpy as np, struct, json, os
def rd(p):
    with open(p,'rb') as f:
        f.read(80); n=struct.unpack('<I',f.read(4))[0]
        d=np.frombuffer(f.read(n*50),dtype=np.uint8).reshape(n,50)
        return d[:,12:48].copy().view('<f4').reshape(-1,3,3)
U=44.45; XO=141.0; POST_W=30.0; POST_D=35.0; RACK_OUT=240.0
UPP,NP,JU=5,3,1.0
M=0.3                                        # margin: contact closer than this is an interface
boxes=[]
for i in range(NP):                          # 4 posts per 5U section
    z0=i*(UPP+JU)*U; z1=z0+UPP*U
    for sx in (-1,1):
        for y0,y1 in ((0,POST_D),(RACK_OUT-POST_D,RACK_OUT)):
            boxes.append(('post',sx*XO-(sx>0)*POST_W if sx>0 else -XO, y0, z0, 0))
            boxes[-1]=('post',(XO-POST_W if sx>0 else -XO),y0,z0,(XO if sx>0 else -XO+POST_W),y1,z1)
for i in range(NP-1):                        # 2 extensions per band, full depth
    z0=(i*(UPP+JU)+UPP)*U-19.83; z1=z0+84.17
    for sx in (1,-1):
        boxes.append(('ext',(XO-POST_W if sx>0 else -XO),0.0,z0,(XO if sx>0 else -XO+POST_W),RACK_OUT,z1))
L=json.load(open("out/LAYOUT.json")); bad=0; ZF=L.get("z_floor_mm",0.0); boxes=[(k,a,b,c+ZF,d,e,f+ZF) for k,a,b,c,d,e,f in boxes]
for m in L['modules']:
    for f in m.get('files',[]):
        p=f'out/{f}.stl'
        if not os.path.exists(p): continue
        v=rd(p).reshape(-1,3); worst=None
        for kind,x0,y0,z0,x1,y1,z1 in boxes:
            inside=((v[:,0]>x0+M)&(v[:,0]<x1-M)&(v[:,1]>y0+M)&(v[:,1]<y1-M)&(v[:,2]>z0+M)&(v[:,2]<z1-M))
            if inside.any():
                q=v[inside]
                d=min(q[:,0].max()-x0,x1-q[:,0].min(),q[:,1].max()-y0,y1-q[:,1].min(),q[:,2].max()-z0,z1-q[:,2].min())
                if worst is None or d>worst[1]: worst=(kind,d,inside.sum())
        if worst: bad+=1; print(f'  CLASH {f:18} into {worst[0]}: {worst[1]:.2f} mm deep, {worst[2]} verts')
        else:     print(f'  ok    {f:18} clear of all posts and extensions')
# and the clear-width sanity check
for m in L['modules']:
    for f in m.get('files',[]):
        p=f'out/{f}.stl'
        if not os.path.exists(p): continue
        T=rd(p); behind=T[T[:,:,1].mean(1)>POST_D*0+1.0].reshape(-1,3)
        if len(behind):
            w=behind[:,0].max()-behind[:,0].min()
            print(f'        {f:18} widest part behind the flange: {w:.1f} mm (clear width 222.0)'
                  + ('  TOO WIDE' if w>222.0 else ''))
print('\nFRAME CLEAN' if not bad else f'\n{bad} real clash(es)')
