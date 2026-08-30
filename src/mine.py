"""Targeted search across the sources corpus."""
import pathlib, re, sys, textwrap
CACHE = pathlib.Path(__file__).resolve().parents[1] / "sources_text"
docs = {p.stem: p.read_text(encoding="utf8", errors="replace") for p in CACHE.glob("*.txt")}

def find(pattern, window=230, maxhits=3, files=None):
    rx = re.compile(pattern, re.I)
    n = 0
    for name, txt in docs.items():
        if files and not any(f.lower() in name.lower() for f in files):
            continue
        hits = 0
        for m in rx.finditer(txt):
            a, b = max(0, m.start()-window//2), min(len(txt), m.end()+window)
            s = re.sub(r"\s+", " ", txt[a:b]).strip()
            print(f"  [{name[:40]}] ...{s}...")
            hits += 1; n += 1
            if hits >= maxhits: break
    if n == 0:
        print("  (no hits)")
    print()

q = sys.argv[1] if len(sys.argv) > 1 else None
if q:
    print(f"### {q}\n"); find(q, maxhits=int(sys.argv[2]) if len(sys.argv)>2 else 3)
