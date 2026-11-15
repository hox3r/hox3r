#!/usr/bin/env python3
"""Build monochrome animated ASCII portrait banners for the HOX3R profile."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from PIL import Image, ImageOps, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / 'assets/source/portrait.png'
DEFAULT_DATA = ROOT / 'data/profile.json'
OUT = ROOT / 'assets/hero'
RAMP = ' .,:;irsXA253hMHGS#9B&@'

def load_profile(path):
    data = json.loads(path.read_text(encoding='utf-8'))
    for key in ('username','display_name','role','focus','about','focus_areas','projects'):
        if key not in data: raise ValueError(f'missing profile field: {key}')
    return data

def portrait_grid(path, cols=49, rows=49):
    im = Image.open(path).convert('RGB')
    # Remove the flat blue background by measuring distance from the image corners.
    px = im.load(); w,h = im.size
    corners = [px[0,0], px[w-1,0]]
    from collections import deque
    mask = bytearray(w*h); q=deque([(0,0),(w-1,0),(0,h-1),(w-1,h-1)])
    while q:
        x,y=q.popleft(); i=y*w+x
        if mask[i]: continue
        mask[i]=1
        rgb=px[x,y]
        if min(sum((rgb[k]-c[k])**2 for k in range(3))**.5 for c in corners)>42: continue
        px[x,y]=(0,0,0)
        if x: q.append((x-1,y))
        if x+1<w: q.append((x+1,y))
        if y: q.append((x,y-1))
        if y+1<h: q.append((x,y+1))
    # Keep only the subject; border-connected blue background pixels stay empty.
    subject=Image.new('L',(w,h),255)
    sp=subject.load()
    for yy in range(h):
        for xx in range(w):
            if not mask[yy*w+xx]: sp[xx,yy]=sum(px[xx,yy])//3
    gray=subject.resize((cols,rows),Image.Resampling.LANCZOS)
    gray=gray.filter(ImageFilter.UnsharpMask(radius=1,percent=130,threshold=2))
    p=gray.load(); cells=[]
    for y in range(rows):
        for x in range(cols):
            v=p[x,y]
            # Edge emphasis keeps glasses, hairline and jaw readable at small sizes.
            gx=abs(p[min(cols-1,x+1),y]-p[max(0,x-1),y])
            gy=abs(p[x,min(rows-1,y+1)]-p[x,max(0,y-1)])
            ink=max(0,min(1,(255-v)/255*.83+(gx+gy)/510*.48))
            if ink < .12: continue
            idx=min(len(RAMP)-1,round(ink*(len(RAMP)-1)))
            cells.append((x,y,RAMP[idx],ink))
    return cells,cols,rows

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--source',type=Path,default=DEFAULT_SOURCE); ap.add_argument('--data',type=Path,default=DEFAULT_DATA); args=ap.parse_args()
    profile=load_profile(args.data)
    cells,cols,rows=portrait_grid(args.source)
    print(f"Loaded profile for {profile['username']}; extracted {len(cells)} portrait cells from a {cols}x{rows} grid.")
if __name__=='__main__': main()
