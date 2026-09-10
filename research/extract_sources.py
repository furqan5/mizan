"""Mechanical local PDF extraction; no summarizer in the evidence path.

This script performs no engineering hypothesis test and sets no pass threshold.
It preserves per-page text and PDF SHA256. Search counts import the literal CHEM
regex from the original scan script; counts are vocabulary occurrences, not
proof of scientific novelty. All extracted source text remains internal.
"""
from pathlib import Path
import hashlib
import json
import re
from pypdf import PdfReader

BASE = Path(__file__).resolve().parents[1]
REPO = Path(r"C:\Users\Nouman\Desktop\Furqan's Docs\Startup\mizan")
DESKTOP = Path(r"C:\Users\Nouman\Desktop")
NAMES = ['2606.11163v1', '2605.15516v4', '2603.01198v4',
         '2606.15408v2', '2608.19552v1', '3575813.3595189',
         'j.jcp.2018.10.045', 'tj_from_transient_rth_data_an-e']
pattern = re.search(r"^CHEM='([^']+)'", (REPO/'docs/prior_art_datacenter_scan.sh').read_text(), re.M).group(1)
out = BASE/'research/source_text'
out.mkdir(exist_ok=True)
records = []
for name in NAMES:
    p = DESKTOP/(name+'.pdf')
    reader = PdfReader(p)
    pages = [page.extract_text(extraction_mode='layout') for page in reader.pages]
    text = '\n'.join(f'\n===== PDF PAGE {i+1} =====\n{t}' for i,t in enumerate(pages))
    (out/(name+'.txt')).write_text(text, encoding='utf-8')
    matches = [m.group(0) for m in re.finditer(pattern,text,re.I)]
    records.append(dict(name=p.name,path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),pages=len(pages),characters=len(text),chem_count=len(matches),chem_matches=matches,extractor='pypdf layout'))
(out/'manifest.json').write_text(json.dumps({'regex':pattern,'sources':records},indent=2),encoding='utf-8')
print(json.dumps(records,indent=2))
