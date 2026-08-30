"""Fetch the Plataforma Solar de Almeria wet cooling tower dataset (Zenodo 10806201)."""
import hashlib, json, pathlib, sys, zipfile
import requests

REC = "10806201"
DATA = pathlib.Path(__file__).resolve().parents[1] / "data"
DATA.mkdir(exist_ok=True)

meta = requests.get(f"https://zenodo.org/api/records/{REC}", timeout=60).json()
print("TITLE:", meta.get("metadata", {}).get("title"))
print("LICENSE:", json.dumps(meta.get("metadata", {}).get("license", {})))
(DATA / "zenodo_metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf8")

for f in meta.get("files", []):
    key, size = f["key"], f["size"]
    url = f["links"]["self"]
    chk = f.get("checksum", "")
    dest = DATA / key
    print(f"\nFILE {key}  {size/1e6:.2f} MB  checksum={chk}")
    if not dest.exists() or dest.stat().st_size != size:
        r = requests.get(url, timeout=600, stream=True); r.raise_for_status()
        with open(dest, "wb") as fh:
            for c in r.iter_content(1 << 20):
                fh.write(c)
    h = hashlib.md5(dest.read_bytes()).hexdigest()
    print("  md5 local :", h)
    print("  md5 match :", chk.endswith(h))
    if zipfile.is_zipfile(dest):
        with zipfile.ZipFile(dest) as z:
            z.extractall(DATA / "extracted")
            print("  extracted members:")
            for n in z.namelist()[:60]:
                print("   ", n)
