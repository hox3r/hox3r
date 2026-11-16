#!/usr/bin/env python3
"""Build monochrome animated ASCII portrait banners for the HOX3R profile."""
from __future__ import annotations
import argparse, json, random
from pathlib import Path
from xml.sax.saxutils import escape
from PIL import Image, ImageOps, ImageFilter
import cairosvg

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

def svg_doc(profile,cells,cols,rows,mobile=False):
    if mobile:
        W,H=560,850; px,py,pw,ph=54,44,452,452; cw=pw/cols; ch=ph/rows
        title_y=570; body_y=650; line_gap=31
    else:
        W,H=1120,500; px,py,pw,ph=42,34,438,438; cw=pw/cols; ch=ph/rows
        title_y=150; body_y=214; line_gap=36
    uname=escape(profile['username']); name=escape(profile['display_name'].upper())
    role=escape(profile['role'].upper()); focus=escape(profile['focus'].upper())
    about=escape(profile['about'])
    areas=profile.get('focus_areas',[])[:4]
    if mobile:
        panel=''.join(f'<text x="58" y="{body_y+i*line_gap}" class="detail">{escape(a.upper())}</text>' for i,a in enumerate(areas))
        panel+=f'<text x="58" y="790" class="micro">{uname}@profile:~$ _</text>'
    else:
        panel=(f'<text x="560" y="{title_y}" class="name">{name}</text>'
          f'<text x="562" y="{title_y+38}" class="role">{role}</text>'
          f'<path d="M560 220H1060" class="rule"/>'
          f'<text x="560" y="260" class="label">PRIMARY FOCUS</text>'
          f'<text x="560" y="294" class="focus">{focus}</text>'
          f'<text x="560" y="346" class="label">AREAS</text>')
        panel+=''.join(f'<text x="560" y="{385+i*27}" class="detail">/ {escape(a.upper())}</text>' for i,a in enumerate(areas))
        panel+=f'<text x="560" y="482" class="micro">{uname}@profile:~$ whoami</text>'
    glyphs=portrait_markup(cells,px,py,cw,ch,8.2,'p')
    scan=f'''<g class="scan" opacity="0"><rect x="{px-8}" y="{py}" width="{pw+16}" height="3" fill="#fff" opacity=".9"/><rect x="{px-8}" y="{py-7}" width="{pw+16}" height="17" fill="#fff" opacity=".12"/><animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.05;.92;1" dur="5.8s" begin="4.1s" repeatCount="indefinite"/><animateTransform attributeName="transform" type="translate" values="0 0;0 {ph}" keyTimes="0;1" dur="1.55s" begin="4.1s" repeatCount="indefinite"/></g>'''
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
@media(prefers-reduced-motion:reduce){{.glyph animate,.glyph animateTransform,.scan animate,.scan animateTransform{{display:none}}.glyph{{opacity:1}}}}
</style>
<rect x="{px-12}" y="{py-10}" width="{pw+24}" height="{ph+20}" fill="none" stroke="#555" stroke-width="1"/>
<g>{glyphs}</g>{scan}
{panel}
</svg>'''

def make_gif(profile, cells, mobile=False):
    from PIL import ImageDraw, ImageFont
    import math
    W,H=(560,850) if mobile else (1120,500)
    px,py,pw,ph=(54,44,452,452) if mobile else (42,34,438,438)
    cw,ch=pw/49,ph/49
    font_path='/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
    glyph_font=ImageFont.truetype(font_path,max(6,round(cw*.94)))
    frames=[]; rng=random.Random(20261117); vectors={}
    for x,y,char,ink in cells:
        if char==' ': continue
        side=[x,48-x,y,48-y].index(min([x,48-x,y,48-y]))
        if side==0: dx,dy=-rng.randint(90,300),rng.randint(-120,120)
        elif side==1: dx,dy=rng.randint(90,300),rng.randint(-120,120)
        elif side==2: dx,dy=rng.randint(-140,140),-rng.randint(90,260)
        else: dx,dy=rng.randint(-140,140),rng.randint(90,260)
        delay=(x*13+y*7)%97/97*2.7
        vectors[(x,y)]=(dx,dy,delay,ink)
    name=profile['display_name'].upper(); role=profile['role'].upper(); focus=profile['focus'].upper()
    areas=profile.get('focus_areas',[])[:4]
    for frame_no in range(38):
        im=Image.new('RGB',(W,H),'black'); d=ImageDraw.Draw(im)
        d.rectangle((px-12,py-10,px+pw+12,py+ph+10),outline=(75,75,75),width=1)
        progress_time=frame_no*.12
        for x,y,char,ink in cells:
            if char==' ': continue
            dx,dy,delay,_=vectors[(x,y)]
            t=max(0,min(1,(progress_time-delay)/.78))
            # Smooth ease-out for the character assembly.
            eased=1-(1-t)**3
            ox=dx*(1-eased); oy=dy*(1-eased)
            alpha=max(0,min(255,int(255*min(1,(progress_time-delay)/.35))))
            if alpha:
                color=(alpha,alpha,alpha)
                d.text((px+x*cw+ox,py+(y+.02)*ch+oy),char,font=glyph_font,fill=color)
        if mobile:
            small=ImageFont.truetype(font_path,14); micro=ImageFont.truetype(font_path,11)
            for i,a in enumerate(areas): d.text((58,650+i*31),a.upper(),font=small,fill=(220,220,220))
            d.text((58,790),f"{profile['username']}@profile:~$ _",font=micro,fill=(120,120,120))
        else:
            title=ImageFont.truetype(font_path,43); rolefont=ImageFont.truetype(font_path,14)
            label=ImageFont.truetype(font_path,11); focusfont=ImageFont.truetype(font_path,22); detail=ImageFont.truetype(font_path,13); micro=ImageFont.truetype(font_path,10)
            d.text((560,105),name,font=title,fill='white'); d.text((562,178),role,font=rolefont,fill='white')
            d.line((560,220,1060,220),fill=(85,85,85),width=1)
            d.text((560,249),'P R I M A R Y   F O C U S',font=label,fill=(140,140,140)); d.text((560,275),focus,font=focusfont,fill='white')
            d.text((560,335),'A R E A S',font=label,fill=(140,140,140))
            for i,a in enumerate(areas): d.text((560,374+i*27),'/ '+a.upper(),font=detail,fill=(220,220,220))
            d.text((560,470),f"{profile['username']}@profile:~$ whoami",font=micro,fill=(120,120,120))
        # Scan starts only after all characters have arrived.
        if frame_no>=31:
            scan_y=py-5+(frame_no-31)*((ph+10)/6)
            d.rectangle((px-8,scan_y-7,px+pw+8,scan_y+10),fill=(35,35,35))
            d.rectangle((px-8,scan_y,px+pw+8,scan_y+2),fill=(255,255,255))
        frames.append(im.quantize(colors=32,method=Image.Quantize.MEDIANCUT))
    return frames

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--source',type=Path,default=DEFAULT_SOURCE); ap.add_argument('--data',type=Path,default=DEFAULT_DATA); ap.add_argument('--check',action='store_true'); args=ap.parse_args()
    profile=load_profile(args.data)
    cells,cols,rows=portrait_grid(args.source)
    OUT.mkdir(parents=True,exist_ok=True)
    outputs={
      'hox3r-hero-desktop.svg':svg_doc(profile,cells,cols,rows,False),
      'hox3r-hero-mobile.svg':svg_doc(profile,cells,cols,rows,True),
    }
    for name,content in outputs.items():
        path=OUT/name
        if args.check:
            if not path.exists() or path.read_text(encoding='utf-8')!=content: raise SystemExit(f'out of date: {path.relative_to(ROOT)}')
        else: path.write_text(content,encoding='utf-8')
    if args.check and not all((OUT/n).exists() for n in ('hox3r-hero-desktop.gif','hox3r-hero-mobile.gif')): raise SystemExit('animated GIF assets are missing')
    if not args.check:
        for name in outputs:
            svg=(OUT/name).read_text(encoding='utf-8').replace('opacity="0"','opacity="1"'); svg=__import__('re').sub(r'<animate[^>]*/>', '', svg); svg=__import__('re').sub(r'<g class="scan".*?</g>', '', svg, flags=__import__('re').S); png=cairosvg.svg2png(bytestring=svg.encode(),output_width=1120 if 'desktop' in name else 560)
            (OUT/(name.replace('.svg','-preview.png'))).write_bytes(png)
        for mobile in (False, True):
            frames=make_gif(profile,cells,mobile)
            gif_name='hox3r-hero-mobile.gif' if mobile else 'hox3r-hero-desktop.gif'
            frames[0].save(OUT/gif_name,save_all=True,append_images=frames[1:],duration=120,loop=0,optimize=True,disposal=2)
        print('Generated monochrome desktop/mobile ASCII hero assets and animated GIFs.')
    else: print('Hero assets are up to date.')
if __name__=='__main__': main()
