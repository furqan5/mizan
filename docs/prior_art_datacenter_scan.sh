#!/bin/bash
# Reproduces the measurement in prior_art_datacenter.md (6 Sep 2026).
# Downloads full texts and greps them. No summarisation anywhere in the path.
#
#   ./prior_art_datacenter_scan.sh          # fetch + scan
#
# The nine chemistry terms are IDENTICAL to prior_art_esc.md so the two sweeps
# are comparable. Do not silently widen this list: the whole value of the number
# is that it is the same instrument pointed at a different literature.

set -u
WORK="${1:-./dc_prior_art_scan}"
mkdir -p "$WORK/raw" "$WORK/water" "$WORK/vendors"
cd "$WORK" || exit 1

CHEM='saturation index|langelier|ryznar|puckorius|gypsum|caso4|calcium sulfate|calcium sulphate|calcite|calcium carbonate|cycles of concentration|blow-?down|sulfate|sulphate|silica'
CTRL='model predictive control|reinforcement learning|\bMPC\b|setpoint|set-point|objective function|optimi[sz]ation|constraint|control policy'
OPTCTRL='model predictive control|reinforcement learning|\bMPC\b|objective function|optimal control|control policy|setpoint optimi|supervisory control'
WATER='\bwater\b|cooling tower|evaporative|water usage effectiveness|\bWUE\b|makeup water|make-up water'

# ---- control corpus: data-centre cooling control literature -----------------
CONTROL_IDS="1709.05077 1808.10427 2211.07357 2410.05133 2501.15085 2509.16513 2601.02275 2602.02137 2603.01198 2605.15516"
# ---- water corpus: data-centre cooling water literature --------------------
WATER_IDS="2304.03271"

fetch_arxiv() {  # $1 = id, $2 = destination dir
  local id="$1" dir="$2" code sz
  for url in "https://arxiv.org/html/${id}v1" "https://arxiv.org/html/${id}v2" \
             "https://arxiv.org/html/${id}v3" "https://ar5iv.labs.arxiv.org/html/${id}"; do
    code=$(curl -sSL -m 45 -o _raw.html -w "%{http_code}" "$url" 2>/dev/null)
    sz=$(wc -c < _raw.html)
    if [ "$code" = "200" ] && [ "$sz" -gt 20000 ]; then
      sed -e 's/<script[^>]*>.*<\/script>//g' -e 's/<[^>]*>/ /g' _raw.html \
        | tr -s ' \n' ' \n' > "$dir/${id}.txt"
      echo "OK   $id  $(wc -c < "$dir/${id}.txt") chars"
      return 0
    fi
  done
  echo "FAIL $id  (last http $code, size $sz)"
}

fetch_url() {  # $1 = url, $2 = out path
  local code
  code=$(curl -sSL -m 45 -A "Mozilla/5.0 (prior-art scan)" -o _w.html -w "%{http_code}" "$1" 2>/dev/null)
  sed -e 's/<script[^>]*>.*<\/script>//g' -e 's/<style[^>]*>.*<\/style>//g' \
      -e 's/<[^>]*>/ /g' _w.html | tr -s ' \n' ' \n' > "$2"
  echo "$code  $(wc -c < "$2")  $2"
}

echo "== fetching control corpus =="
for id in $CONTROL_IDS; do fetch_arxiv "$id" raw; done
echo "== fetching water corpus =="
for id in $WATER_IDS;   do fetch_arxiv "$id" water; done
fetch_url "https://patents.google.com/patent/US12358820B2/en" water/patent_chemtreat_12358820.txt
fetch_url "https://genesiswatertech.com/blog-post/the-data-center-water-efficiency-paradox-why-your-cooling-tower-is-wasting-more-water-than-you-think/" water/genesis_blowdown.txt
fetch_url "https://amiad.com/blog/data-center-cooling-water-cycles-of-concentration/" water/amiad_coc.txt
fetch_url "https://genesiswatertech.com/blog-post/treated-wastewater-for-data-center-cooling-a-practical-guide-to-alternative-water-sources/" water/genesis_tse.txt
echo "== fetching vendors =="
fetch_url "https://www.ekkosense.com/" vendors/ekkosense.txt
fetch_url "https://www.vigilent.com/" vendors/vigilent.txt
fetch_url "https://deepmind.google/discover/blog/safety-first-ai-for-autonomous-data-centre-cooling-and-industrial-control/" vendors/deepmind.txt
# NOTE: phaidra.ai is a JS-rendered SPA and returns ~38 bytes to curl.
# It was verified manually by full-page read (zero chemistry terms), not by this script.

count() { grep -oEi "$2" "$1" 2>/dev/null | wc -l; }

echo
printf "%-34s %9s %7s %9s %7s\n" "CONTROL SIDE" "chars" "CHEM" "control" "water"
for f in raw/*.txt; do
  printf "%-34s %9s %7s %9s %7s\n" "$(basename "$f" .txt)" "$(wc -c < "$f")" \
    "$(count "$f" "$CHEM")" "$(count "$f" "$CTRL")" "$(count "$f" "$WATER")"
done

echo
printf "%-34s %9s %7s %9s\n" "WATER SIDE (mirror)" "chars" "CHEM" "OPT-CTRL"
for f in water/*.txt; do
  [ "$(wc -c < "$f")" -lt 5000 ] && { echo "  skip (bad fetch): $f"; continue; }
  printf "%-34s %9s %7s %9s\n" "$(basename "$f" .txt)" "$(wc -c < "$f")" \
    "$(count "$f" "$CHEM")" "$(count "$f" "$OPTCTRL")"
done

echo
printf "%-34s %9s %7s %9s\n" "VENDORS" "chars" "CHEM" "control"
for f in vendors/*.txt; do
  [ "$(wc -c < "$f")" -lt 5000 ] && { echo "  skip (bad fetch): $f"; continue; }
  printf "%-34s %9s %7s %9s\n" "$(basename "$f" .txt)" "$(wc -c < "$f")" \
    "$(count "$f" "$CHEM")" "$(count "$f" "$CTRL")"
done

echo
echo "== MANDATORY disambiguation: every scale/scaling hit must be inspected =="
echo "   (in the 6 Sep 2026 run, 71 of 72 meant 'scale up'; the 1 real one is"
echo "    the DeepMind BCOOLER mineral-scaling passage quoted in the write-up)"
grep -ohEi ".{55}\bscal(e|ing)\b.{55}" raw/*.txt | head -30
