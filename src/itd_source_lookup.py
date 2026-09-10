"""Extract Figure 2 from the supplied arXiv2606.11163v1 PDF, no device model.

Pre-registered extraction checks before coordinate conversion: PDF page2;
Figure2 panel in PDF points x90..285, top300..450 (visually identified).
Three non-filled polylines, each 10 vertices and width>100pt; blue total,
green dynamic, orange static. Axis ticks detected from numeric text adjacent
to grid lines (within5pt). Calibration residual <=0.05 axis units. Sum of
dynamic and static powers must match plotted total within1W. Temperature
vertices must increase; min total must be interior. Lookup is piecewise linear
within the plotted range ONLY, with no extrapolation. Display precision 0.1C/W
reflects plot extraction, not raw measurement precision. These are extraction
integrity checks, not validation of the paper's physical or facility claims.

Source: Crop, Moore & Pasricha (9 Jun2026), Figure2, 350W Xeon8480 povray at
fixed frequency; measured/derived plotted curve. No original numerical dataset
was provided. Figure5 fleet curves and Figure6 facility energy are model-based;
they are not substituted for the requested Figure2 lookup. CC BY-NC-ND4.0:
internal research extraction, no commercial training or deployment assertion.
"""
from pathlib import Path
import argparse,hashlib,json,math
import pdfplumber

def extract(path):
    page=pdfplumber.open(path).pages[1]
    curves=[c for c in page.curves if not c['fill'] and len(c['pts'])==10
            and c['width']>100 and c['x1']<285 and 300<c['top']<450 and c['bottom']<450]
    assert len(curves)==3,'wrong figure selection'
    words=page.extract_words()
    xt=[w for w in words if w['text'].isdigit() and 90<w['x0']<285 and 450<w['top']<460]
    yt=[w for w in words if w['text'].isdigit() and 75<w['x0']<92 and 300<w['top']<450]
    xl=[x['x0'] for x in page.lines if x['width']==0 and x['height']>100 and 300<x['top']<450 and x['x1']<285]
    yl=[x['top'] for x in page.lines if x['width']>150 and x['height']==0 and 300<x['top']<450 and x['x1']<285]
    def pairs(ticks,lines,axis):
        ret=[]
        for w in ticks:
            pos=(w['x0']+w['x1'])/2 if axis=='x' else (w['top']+w['bottom'])/2
            p=min(lines,key=lambda x:abs(x-pos))
            assert abs(p-pos)<5,'tick mismatch'
            ret.append((p,float(w['text'])))
        return ret
    def calibration(points):
        n=len(points);xp=sum(x for x,y in points)/n;yp=sum(y for x,y in points)/n
        slope=sum((x-xp)*(y-yp) for x,y in points)/sum((x-xp)**2 for x,y in points)
        intercept=yp-slope*xp
        residual=max(abs(slope*x+intercept-y) for x,y in points)
        assert residual<=0.05,'axis calibration'
        return slope,intercept,residual
    xp=pairs(xt,xl,'x');yp=pairs(yt,yl,'y')
    sx,ix,rx=calibration(xp);sy,iy,ry=calibration(yp)
    found={}
    for curve in curves:
        r,g,b=curve['stroking_color']
        key='P_total_W' if b>r and b>g else 'P_dynamic_W' if g>r and g>b else 'P_static_W'
        found[key]=[(sx*x+ix,sy*y+iy) for x,y in curve['pts']]
    points=[]
    for i,(t,p) in enumerate(found['P_total_W']):
        dynamic=found['P_dynamic_W'][i][1];static=found['P_static_W'][i][1]
        assert abs(p-dynamic-static)<=1,'component closure'
        points.append(dict(T_chip_C=round(t,1),P_total_W=round(p,1),P_dynamic_W=round(dynamic,1),P_static_W=round(static,1)))
    assert all(a['T_chip_C']<b['T_chip_C'] for a,b in zip(points,points[1:]))
    imin=min(range(len(points)),key=lambda i:points[i]['P_total_W'])
    assert 0<imin<len(points)-1,'no interior minimum'
    return dict(source=str(path),source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                source_url='https://arxiv.org/abs/2606.11163',source_page=2,figure=2,
                status='PDF vector extraction of published measured/derived curve; not raw observations',
                application='Xeon8480 povray fixed-frequency, not GPU and not coolant temperature',
                license='CC BY-NC-ND 4.0, research use; commercial permissions not established',
                coordinate_calibration=dict(x_pairs=xp,y_pairs=yp,x_residual=rx,y_residual=ry),
                points=points,minimum_sample=points[imin],
                chip_to_water_map=None,extrapolation_allowed=False)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--pdf',type=Path,default=Path(r'C:\Users\Nouman\Desktop\2606.11163v1.pdf'))
    ap.add_argument('--out',type=Path,default=Path(__file__).resolve().parents[1]/'results/itd_source_lookup.json')
    args=ap.parse_args();out=extract(args.pdf)
    args.out.write_text(json.dumps(out,indent=2),encoding='utf-8')
    print(json.dumps(out,indent=2))
