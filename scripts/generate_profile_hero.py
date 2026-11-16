#!/usr/bin/env python3
"""Build monochrome animated ASCII portrait banners for the HOX3R profile."""
from __future__ import annotations
import argparse, json, random
from pathlib import Path
from xml.sax.saxutils import escape
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

def portrait_markup(cells, x0, y0, cellw, cellh, font, prefix, total_delay=2.7):
    out=[]
    rng=random.Random(20261117)
    for x,y,ch,ink in cells:
        if ch==' ': continue
        tx=x0+x*cellw; ty=y0+(y+0.82)*cellh
        # Arrival vectors originate from the nearest outer edge, with slight deterministic scatter.
        distances=[x,48-x,y,48-y]; side=distances.index(min(distances))
        if side==0: dx=-rng.randint(90,300); dy=rng.randint(-120,120)
        elif side==1: dx=rng.randint(90,300); dy=rng.randint(-120,120)
        elif side==2: dx=rng.randint(-140,140); dy=-rng.randint(90,260)
        else: dx=rng.randint(-140,140); dy=rng.randint(90,260)
        delay=(x*13+y*7)%97/97*total_delay
        opacity=max(.52,min(1,ink+.22))
        out.append(f'<text x="{tx:.2f}" y="{ty:.2f}" class="glyph" opacity="0" fill-opacity="{opacity:.2f}">{escape(ch)}<animate attributeName="opacity" from="0" to="1" begin="{delay:.2f}s" dur=".45s" fill="freeze"/><animateTransform attributeName="transform" type="translate" from="{dx} {dy}" to="0 0" begin="{delay:.2f}s" dur=".78s" calcMode="spline" keySplines=".2 .7 .2 1" fill="freeze"/></text>')
    return ''.join(out)

def svg_doc(profile,cells,cols,rows):
    W,H=1120,500; px,py,pw,ph=42,34,438,438; cw=pw/cols; ch=ph/rows
    title_y=150
    uname=escape(profile['username']); name=escape(profile['display_name'].upper())
    role=escape(profile['role'].upper()); focus=escape(profile['focus'].upper())
    about=escape(profile['about'])
    areas=profile.get('focus_areas',[])[:4]
    panel=(f'<text x="560" y="{title_y}" class="name">{name}</text>'
      f'<text x="562" y="{title_y+38}" class="role">{role}</text>'
      f'<path d="M560 220H1060" class="rule"/>'
      f'<text x="560" y="260" class="label">PRIMARY FOCUS</text>'
      f'<text x="560" y="294" class="focus">{focus}</text>'
      f'<text x="560" y="346" class="label">AREAS</text>')
    panel+=''.join(f'<text x="560" y="{385+i*27}" class="detail">/ {escape(a.upper())}</text>' for i,a in enumerate(areas))
    panel+=f'<text x="560" y="482" class="micro">{uname}@profile:~$ whoami</text>'
    glyphs=portrait_markup(cells,px,py,cw,ch,8.2,'p')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="HOX3R monochrome animated ASCII portrait">
<rect width="{W}" height="{H}" fill="#000"/>
<style>
.glyph{{font-family:'DejaVu Sans Mono',monospace;font-size:{(cw*.96):.2f}px;font-weight:700;white-space:pre;fill:#fff}}
.name{{font:700 43px 'DejaVu Sans Mono',monospace;letter-spacing:2px;fill:#fff}}
.role{{font:14px 'DejaVu Sans Mono',monospace;letter-spacing:2px;fill:#fff}}
.label{{font:11px 'DejaVu Sans Mono',monospace;letter-spacing:3px;fill:#888}}
.focus{{font:700 22px 'DejaVu Sans Mono',monospace;fill:#fff}}
.detail{{font:13px 'DejaVu Sans Mono',monospace;letter-spacing:1px;fill:#ddd}}
.micro{{font:10px 'DejaVu Sans Mono',monospace;letter-spacing:1px;fill:#777}}
.rule{{stroke:#555;stroke-width:1}}
@media(prefers-reduced-motion:reduce){{.glyph animate,.glyph animateTransform{{display:none}}.glyph{{opacity:1}}}}
</style>
<rect x="{px-12}" y="{py-10}" width="{pw+24}" height="{ph+20}" fill="none" stroke="#555" stroke-width="1"/>
<g>{glyphs}</g>
{panel}
</svg>'''

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--source',type=Path,default=DEFAULT_SOURCE); ap.add_argument('--data',type=Path,default=DEFAULT_DATA); args=ap.parse_args()
    profile=load_profile(args.data)
    cells,cols,rows=portrait_grid(args.source)
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'hox3r-hero-desktop.svg').write_text(svg_doc(profile,cells,cols,rows),encoding='utf-8')
    print('Generated animated ASCII portrait banner.')
if __name__=='__main__': main()
