"""Extract text from the sources library and build a searchable cache."""
import pathlib, re, sys, json
import fitz  # PyMuPDF

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "sources"
CACHE = ROOT / "sources_text"
CACHE.mkdir(exist_ok=True)

index = []
for pdf in sorted(SRC.glob("*.pdf")):
    out = CACHE / (pdf.stem + ".txt")
    if out.exists() and out.stat().st_size > 0:
        text = out.read_text(encoding="utf8", errors="replace")
    else:
        try:
            doc = fitz.open(pdf)
            text = "\n".join(p.get_text() for p in doc)
            doc.close()
            out.write_text(text, encoding="utf8")
        except Exception as e:
            print(f"FAIL {pdf.name}: {e}")
            continue
    # first non-trivial lines usually carry the title
    lines = [l.strip() for l in text.split("\n")[:60] if len(l.strip()) > 25]
    title = lines[0][:150] if lines else "(no title found)"
    index.append({"file": pdf.name, "chars": len(text), "pages_est": text.count("\f") + 1,
                  "title_guess": title})
    print(f"{pdf.name[:55]:55s} {len(text):>8,d} chars | {title[:70]}")

(CACHE / "_index.json").write_text(json.dumps(index, indent=2), encoding="utf8")
print(f"\n{len(index)} documents cached -> {CACHE}")
