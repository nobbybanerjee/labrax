import numpy as np, struct, math, json
from PIL import Image, ImageDraw, ImageFont
def rd(p):
    with open(p,'rb') as f:
        f.read(80); n=struct.unpack('<I',f.read(4))[0]
        d=np.frombuffer(f.read(n*50),dtype=np.uint8).reshape(n,50)
        return d[:,12:48].copy().view('<f4').reshape(-1,3,3)
def render(groups,az,el,W,H,bg=250):
    a,e=math.radians(az),math.radians(el)
    d=np.array([math.cos(e)*math.sin(a),-math.cos(e)*math.cos(a),-math.sin(e)])
    r=np.cross(d,[0,0,1.]); r=r/np.linalg.norm(r) if np.linalg.norm(r)>1e-6 else np.array([1.,0,0])
    u=np.cross(r,d); u/=np.linalg.norm(u)
    allv=np.concatenate([g[0].reshape(-1,3) for g in groups]); cen=(allv.min(0)+allv.max(0))/2
    xs=(allv-cen)@r; ys=(allv-cen)@u
    s=min((W-40)/(xs.max()-xs.min()),(H-40)/(ys.max()-ys.min()))
    img=np.full((H,W,3),bg,np.uint8); zb=np.full((H,W),1e18)
    L=np.array([.35,-.55,.76]); L/=np.linalg.norm(L)
    for T,col in groups:
        vv=T-cen; x,y,z=vv@r,vv@u,vv@d
        px=(x*s+W/2).astype(np.int32); py=(H/2-y*s).astype(np.int32)
        n=np.cross(vv[:,1]-vv[:,0],vv[:,2]-vv[:,0]); n/=np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-12)
        sh=np.abs(n@L)*.68+.32
        for k in range(len(vv)):
            X,Y,Z=px[k],py[k],z[k]
            x0,x1=max(X.min(),0),min(X.max(),W-1); y0,y1=max(Y.min(),0),min(Y.max(),H-1)
            if x1<x0 or y1<y0: continue
            gx,gy=np.meshgrid(np.arange(x0,x1+1),np.arange(y0,y1+1))
            d0=(X[1]-X[0])*(gy-Y[0])-(Y[1]-Y[0])*(gx-X[0]); d1=(X[2]-X[1])*(gy-Y[1])-(Y[2]-Y[1])*(gx-X[1]); d2=(X[0]-X[2])*(gy-Y[2])-(Y[0]-Y[2])*(gx-X[2])
            m=((d0>=0)&(d1>=0)&(d2>=0))|((d0<=0)&(d1<=0)&(d2<=0))
            if not m.any(): continue
            zz=Z.mean(); sel=m&(zz<zb[y0:y1+1,x0:x1+1])
            if not sel.any(): continue
            zb[y0:y1+1,x0:x1+1]=np.where(sel,zz,zb[y0:y1+1,x0:x1+1])
            c=(np.array(col)*sh[k]).clip(0,255).astype(np.uint8)
            blk=img[y0:y1+1,x0:x1+1]; blk[sel]=c; img[y0:y1+1,x0:x1+1]=blk
    return Image.fromarray(img)
hx=lambda h:tuple(int(h[i:i+2],16) for i in (0,2,4))
L=json.load(open('out/LAYOUT.json'))
G=[(rd('out/frame_posts.stl'),hx('8f7ddb')),(rd('out/frame_joiners.stl'),hx('5f6bd6')),(rd('out/frames.stl'),hx('3f4654')),(rd('out/feet.stl'),hx('202428')),(rd('out/bottom_panel.stl'),hx('9aa3b0')),(rd('out/side_panels.stl'),hx('c2c8d2')),(rd('out/handles.stl'),hx('e69650'))]
for m in L['modules']:
    for f in m.get('files',[]):
        G.append((rd(f'out/{f}.stl'),hx(m['colour'][1:])))
W,H=620,1180
front=render(G,180,0,W,H); side=render(G,90,0,560,H); iso=render(G,35,22,760,H)
sheet=Image.new('RGB',(W+560+760+40,H+40),(255,255,255)); d=ImageDraw.Draw(sheet)
sheet.paste(front,(10,30)); sheet.paste(side,(W+20,30)); sheet.paste(iso,(W+580,30))
try: f=ImageFont.truetype('arialbd.ttf',17)
except Exception: f=ImageFont.load_default()
for t,x in (('FRONT',10),('SIDE (left)',W+20),('ISO (rear)',W+580)): d.text((x+6,6),t,fill=(30,30,30),font=f)
sheet.save('C:/Users/nabaru/.kiro/crew/scratch/rack_views_rear.png')
print('saved',sheet.size)
