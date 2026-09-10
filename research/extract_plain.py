"""Companion mechanical scan including rotated text; no pass threshold.

Keep the original layout extraction intact. Apply the original literal regex
also to pypdf plain extraction of each page. The count is text matches, not a
semantic novelty claim, and does not certify OCR or text-layer completeness.
"""
from pathlib import Path
import hashlib,json,re
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]
prior=json.loads((ROOT/'research/source_text/manifest.json').read_text())
rows=[]
for source in prior['sources']:
    p=Path(source['path'])
    assert hashlib.sha256(p.read_bytes()).hexdigest()==source['sha256']
    pages=[page.extract_text() for page in PdfReader(p).pages]
    text='\n'.join(f'\n===== PDF PAGE {i+1} =====\n{t}' for i,t in enumerate(pages))
    (ROOT/'research/source_text'/(p.stem+'.plain.txt')).write_text(text,encoding='utf-8')
    hits=[m.group(0) for m in re.finditer(prior['regex'],text,re.I)]
    rows.append(dict(name=p.name,sha256=source['sha256'],pages=len(pages),
                     characters=len(text),chem_count=len(hits),chem_matches=hits))
(ROOT/'research/source_text/manifest_plain.json').write_text(json.dumps(
    dict(regex=prior['regex'],extractor='pypdf plain',sources=rows),indent=2),encoding='utf-8')
print(json.dumps([dict(name=r['name'],chem_count=r['chem_count']) for r in rows]))
