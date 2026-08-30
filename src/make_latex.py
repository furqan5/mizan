"""
MIZAN :: generated markdown -> LaTeX -> PDF
===========================================
The fpdf2 route in `make_pdf.py` lays text out in a single linear stream
with no float model, so a figure that does not fit in the space remaining
is simply cut at the page break. That is the "half a graph on every page"
problem. LaTeX has a float model, so this module routes the same generated
markdown through XeLaTeX instead.

Nothing here is typed by hand either. `make_report.py` builds the markdown
from `results/*.json` and `results/*.csv`; this converts that markdown to
LaTeX. Re-run the gates, re-run make_report, re-run this, and the PDF
cannot disagree with the evidence.

Typography, to the brief:
  * Times New Roman, 12 pt body, single column, A4.
  * Floats placed by LaTeX and fenced per section with `placeins`, so a
    figure never straddles a page break and never drifts out of the
    section that discusses it.
  * `booktabs` rules; prose columns become `tabularx` X columns so long
    cells wrap instead of running off the page.

Requires XeLaTeX (MiKTeX on this machine) for real Times New Roman via
fontspec. Falls back to a Latin Modern preamble if the font is missing.
"""
from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import brand as BR

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUT = ROOT / "submission"
BUILD = ROOT / "build_tex"

# The project path contains a space and an apostrophe. TeX tolerates
# neither in \includegraphics, so every figure is copied to a flat build
# directory under an ASCII name before it is referenced.
FIG_COUNTER = {"n": 0}

# The tabularx prose-column spec, ">{BSraggedright BSarraybackslash}X",
# assembled from chr(92) so that no later editing pass through this
# file can mangle the two backslashes.
BS = chr(92)
RAGGED = ">{" + BS + "raggedright" + BS + "arraybackslash}X"


# --- character and escaping ----------------------------------------------
# Order matters: backslash first, then the rest.
ESCAPES = [
    ("\\", r"\textbackslash{}"),
    ("&", r"\&"), ("%", r"\%"), ("$", r"\$"), ("#", r"\#"),
    ("_", r"\_"), ("{", r"\{"), ("}", r"\}"),
    ("~", r"\textasciitilde{}"), ("^", r"\textasciicircum{}"),
]

# Glyphs the generated markdown uses that Times New Roman either lacks or
# renders inconsistently. Mapped to LaTeX rather than trusted to the font.
UNICODE = [
    ("\u2014", "---"), ("\u2013", "--"),
    ("\u2192", r"$\rightarrow$"), ("\u2264", r"$\leq$"),
    ("\u2265", r"$\geq$"), ("\u2212", r"$-$"),
    ("\u00b7", r"$\cdot$"), ("\u00b0", r"\textdegree{}"),
    ("\u00b2", r"\textsuperscript{2}"), ("\u00b3", r"\textsuperscript{3}"),
    ("\u207a", r"\textsuperscript{+}"),
    ("\u2082", r"\textsubscript{2}"), ("\u2083", r"\textsubscript{3}"),
    ("\u2033", r"\textquotedbl{}"),
    ("\u00a0", "~"),
]


def esc(s: str) -> str:
    for a, b in ESCAPES:
        s = s.replace(a, b)
    for a, b in UNICODE:
        s = s.replace(a, b)
    # The source carries the Arabic spelling of both names alongside a
    # transliteration. Setting Arabic properly needs a right-to-left engine
    # and a font that covers the script; the transliteration already carries
    # the meaning, so the script is dropped here rather than risking a run
    # of missing glyphs. It stays intact in the markdown and on the web.
    s = re.sub(r"[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]+",
               "", s)
    s = re.sub(r"\s*\(\s*\)", "", s)       # tidy the emptied parentheses
    s = re.sub(r"[ \t]{2,}", " ", s)
    return re.sub(r"\s+([,.;:!?])", r"\1", s)   # and the space they left


def inline(s: str) -> str:
    """Inline markdown -> LaTeX. Code spans are escaped first and parked in
    placeholders so their contents are never treated as markup."""
    spans: list[str] = []

    def park(m):
        spans.append(m.group(1))
        return f"\x00{len(spans) - 1}\x00"

    s = re.sub(r"`([^`]+)`", park, s)
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", s)
    s = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"\\emph{\1}", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r"\\href{\2}{\1}", s)

    def unpark(m):
        return r"\texttt{" + esc(spans[int(m.group(1))]) + "}"

    return re.sub(r"\x00(\d+)\x00", unpark, s)


# --- block conversion ----------------------------------------------------
def split_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def table(rows: list[list[str]]) -> str:
    """Markdown table -> booktabs. Columns whose widest cell is long are
    given as tabularx X columns so the text wraps; short columns stay
    natural width. Without this, a table with one prose column runs off
    the right margin, which is the other half of the layout complaint."""
    ncol = len(rows[0])
    widths = [max(len(r[i]) for r in rows) if i < min(len(r) for r in rows)
              else 0 for i in range(ncol)]
    long_cols = [i for i, w in enumerate(widths) if w > 28]
    if long_cols:
        # ragged-right, not justified: a narrow X column that is justified
        # opens rivers of white space between words, which is what makes a
        # generated table look amateur.
        spec = "".join(RAGGED if i in long_cols
                       else "l" for i in range(ncol))
        env, opt = "tabularx", r"{\linewidth}"
    else:
        spec = "l" * ncol
        env, opt = "tabular", ""

    out = [r"\begin{table}[htbp]", r"\centering", r"\small",
           rf"\begin{{{env}}}{opt}{{{spec}}}", r"\toprule"]
    out.append(" & ".join(rf"\textbf{{{inline(c)}}}" for c in rows[0])
               + r" \\")
    out.append(r"\midrule")
    for r in rows[1:]:
        r = (r + [""] * ncol)[:ncol]
        out.append(" & ".join(inline(c) for c in r) + r" \\")
    out += [r"\bottomrule", rf"\end{{{env}}}", r"\end{table}"]
    return "\n".join(out)


def figure(alt: str, path: str) -> str:
    src = pathlib.Path(path)
    if not src.exists():
        src = ROOT / path
    if not src.exists():
        return ""
    FIG_COUNTER["n"] += 1
    dst = BUILD / f"fig{FIG_COUNTER['n']}{src.suffix}"
    shutil.copyfile(src, dst)
    cap = re.sub(r"^Fig\.?\s*\d+[.:]?\s*", "", alt).strip()
    cap_line = rf"\caption{{{inline(cap)}}}" if cap else ""
    # [htbp] plus the per-section \FloatBarrier from placeins: the figure
    # may move within its section to avoid a bad break, but cannot leave it.
    return "\n".join([
        r"\begin{figure}[htbp]", r"\centering",
        rf"\includegraphics[width=\linewidth,height=0.42\textheight,"
        rf"keepaspectratio]{{{dst.name}}}",
        cap_line, r"\end{figure}",
    ])


HEAD = {1: "section", 2: "section", 3: "subsection", 4: "subsubsection"}


def convert(md: str) -> str:
    lines = md.split("\n")
    out: list[str] = []
    i, n = 0, len(lines)
    in_list = False

    def close_list():
        nonlocal in_list
        if in_list:
            out.append(r"\end{itemize}")
            in_list = False

    while i < n:
        ln = lines[i]
        st = ln.strip()

        if not st:
            close_list()
            out.append("")
            i += 1
            continue

        if st in ("---", "***", "___"):
            close_list()
            i += 1
            continue

        m = re.match(r"^(#{1,4})\s+(.*)$", st)
        if m:
            close_list()
            lvl = len(m.group(1))
            # strip a leading manual number, including forms like "6b."
            title = re.sub(r"^\d+[a-z]?(\.\d+)*\.?\s+", "",
                           m.group(2)).strip()
            if lvl == 1:
                i += 1
                continue                      # the title page carries this
            out.append(rf"\{HEAD[lvl]}{{{inline(title)}}}")
            i += 1
            continue

        m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$", st)
        if m:
            close_list()
            # A generated report writes the caption as the paragraph
            # immediately after the image ("**Fig. 2.** ..."). Consume it as
            # the LaTeX caption instead of leaving it as loose body text,
            # which is how Fig. 2's caption ended up on the page before
            # Fig. 2 itself.
            cap = m.group(1)
            j = i + 1
            while j < n and not lines[j].strip():
                j += 1
            if j < n:
                cm = re.match(r"^\*\*Fig\.?\s*\d+\.?\*\*\s*(.+)$",
                              lines[j].strip())
                if cm:
                    cap = cm.group(1)
                    i = j
            out.append(figure(cap, m.group(2)))
            i += 1
            continue

        if st.startswith("|") and i + 1 < n and re.match(
                r"^\|[\s:|-]+\|$", lines[i + 1].strip()):
            close_list()
            rows = [split_row(st)]
            i += 2
            while i < n and lines[i].strip().startswith("|"):
                rows.append(split_row(lines[i].strip()))
                i += 1
            out.append(table(rows))
            continue

        if st.startswith("```"):
            close_list()
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append(r"\begin{quote}\footnotesize\ttfamily\raggedright")
            for b in buf:
                out.append(esc(b).replace(" ", "~") + r"\\")
            out.append(r"\end{quote}")
            continue

        m = re.match(r"^[-*]\s+(.*)$", st)
        if m:
            if not in_list:
                out.append(r"\begin{itemize}[leftmargin=1.4em,itemsep=2pt,"
                           r"topsep=3pt,parsep=0pt]")
                in_list = True
            out.append(rf"\item {inline(m.group(1))}")
            i += 1
            continue

        m = re.match(r"^(\d+)\.\s+(.*)$", st)
        if m:
            if not in_list:
                out.append(r"\begin{itemize}[leftmargin=1.6em,itemsep=2pt,"
                           r"topsep=3pt,parsep=0pt]")
                in_list = True
            out.append(rf"\item[{m.group(1)}.] {inline(m.group(2))}")
            i += 1
            continue

        if st.startswith(">"):
            close_list()
            out.append(r"\begin{quote}\itshape")
            while i < n and lines[i].strip().startswith(">"):
                out.append(inline(lines[i].strip().lstrip(">").strip()))
                i += 1
            out.append(r"\end{quote}")
            continue

        close_list()
        # a markdown hard break (two trailing spaces) becomes a real break
        out.append(inline(st) + (r"\\" if ln.endswith("  ") else ""))
        i += 1

    close_list()
    return "\n".join(out)


# --- document ------------------------------------------------------------
def preamble(title: str, subtitle: str, have_times: bool) -> str:
    font = (r"\setmainfont{Times New Roman}" if have_times
            else r"\usepackage{newtxtext,newtxmath}")
    return r"""\documentclass[12pt,a4paper]{article}
\usepackage{fontspec}
""" + font + r"""
\usepackage[a4paper,top=25mm,bottom=24mm,left=25mm,right=25mm]{geometry}
\usepackage{booktabs}
\usepackage{tabularx}
\usepackage{array}
\usepackage{graphicx}
\usepackage{float}
\usepackage[section]{placeins}
\usepackage[font=small,labelfont=bf,skip=6pt]{caption}
\usepackage{fancyhdr}
\usepackage{enumitem}
\usepackage{textcomp}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{microtype}
\usepackage[hidelinks]{hyperref}
\usepackage{titlesec}

\titleformat{\section}{\normalfont\large\bfseries}{\thesection}{0.7em}{}
\titleformat{\subsection}{\normalfont\normalsize\bfseries}{\thesubsection}{0.6em}{}
\titlespacing*{\section}{0pt}{14pt plus 3pt minus 2pt}{7pt}
\titlespacing*{\subsection}{0pt}{11pt plus 2pt minus 2pt}{5pt}

\renewcommand{\arraystretch}{1.18}
\setlength{\parskip}{5pt plus 1pt}
\setlength{\parindent}{0pt}
\linespread{1.10}

% Long unbreakable tokens (file names, identifiers) would otherwise run
% into the margin rather than being allowed to stretch a line.
\setlength{\emergencystretch}{3em}

% Floats are given room to be placed properly rather than shoved to the
% end; combined with placeins this keeps every figure whole and in section.
\renewcommand{\topfraction}{0.9}
\renewcommand{\bottomfraction}{0.7}
\renewcommand{\textfraction}{0.08}
\renewcommand{\floatpagefraction}{0.75}

\pagestyle{fancy}
\fancyhf{}
\renewcommand{\headrulewidth}{0.4pt}
\fancyhead[L]{\footnotesize """ + title + r"""}
\fancyhead[R]{\footnotesize\thepage}
\fancyfoot[C]{\footnotesize\itshape """ + subtitle + r"""}

\begin{document}
"""


def titlepage(title: str, meta: list[str]) -> str:
    """Parent brand above the rule, venture brand below it, so page one
    shows the group and the product in the right relation."""
    body = r"\\[4pt]".join(meta)
    return r"""\begin{titlepage}
\centering
\vspace*{2.3cm}
{\Huge\bfseries """ + BR.PARENT_TEX["name"] + r"""\par}
\vspace{9pt}
{\large\itshape """ + BR.PARENT_TEX["tagline"] + r"""\par}
\vspace{7pt}
{\small """ + BR.PARENT_TEX["line"] + r"""\par}

\vspace{1.5cm}
\rule{\linewidth}{0.6pt}\\[14pt]
{\LARGE\bfseries """ + BR.SUBSIDIARY_TEX["name"] + r"""\par}
\vspace{5pt}
{\large\itshape """ + BR.SUBSIDIARY_TEX["tagline"] + r"""\par}
\vspace{13pt}
{\LARGE\bfseries """ + title + r"""\par}
\vspace{11pt}
\rule{\linewidth}{0.6pt}
\vspace{1.2cm}

{\large """ + body + r"""\par}
\vfill
{\footnotesize """ + BR.PARENT_TEX["meaning"] + r"""\\[3pt]
""" + BR.SUBSIDIARY_TEX["meaning"] + r"""\par}
\vspace{9pt}
{\small Mizan is a venture of Furqan \quad\textbullet\quad Lahore, Pakistan\par}
\end{titlepage}
"""


def build(md_path: pathlib.Path, out_pdf: pathlib.Path, title: str,
          subtitle: str, meta: list[str], toc: bool = True) -> bool:
    BUILD.mkdir(exist_ok=True)
    FIG_COUNTER["n"] = 0
    md = md_path.read_text(encoding="utf-8")
    have_times = pathlib.Path("C:/Windows/Fonts/times.ttf").exists()

    body = convert(md)
    doc = preamble(title, subtitle, have_times)
    doc += titlepage(title, meta)
    if toc:
        doc += "\\tableofcontents\n\\clearpage\n"
    doc += body + "\n\\end{document}\n"

    tex = BUILD / (out_pdf.stem + ".tex")
    tex.write_text(doc, encoding="utf-8")

    for _ in range(2):
        r = subprocess.run(
            ["xelatex", "-interaction=nonstopmode", "-halt-on-error",
             tex.name],
            cwd=BUILD, capture_output=True, text=True, encoding="utf-8",
            errors="replace")
    produced = BUILD / (out_pdf.stem + ".pdf")
    if not produced.exists():
        tail = (r.stdout or "")[-2500:]
        print(f"  FAILED {out_pdf.name}\n{tail}")
        return False
    OUT.mkdir(exist_ok=True)
    shutil.copyfile(produced, out_pdf)
    print(f"  written -> {out_pdf}")
    return True


DATE = "29 August 2026"
COMMON = [r"Prepared for the Deep-Tech Ventures Program (.dvp) Cohort 2",
          r"Dhahran Techno Valley \textbullet\ KFUPM",
          DATE]

# (source, output, title, running footer, extra title-page lines, ToC?)
JOBS = [
    (DOCS / "poc_report.md", "Furqan_Mizan_PoC_Report.pdf",
     "Proof-of-Concept Report",
     [r"Condenser-water supervisory control for Gulf district cooling"]
     + COMMON + [r"Claimed maturity: TRL 3"], True),
    (DOCS / "commercialisation.md", "Furqan_Mizan_Commercialisation.pdf",
     "Commercialisation Plan and Budget", COMMON, True),
    (DOCS / "market_dossier.md", "Furqan_Mizan_Market_Dossier.pdf",
     "Market Dossier", COMMON, True),
    (DOCS / "chemistry_evidence.md", "Furqan_Mizan_Chemistry_Evidence.pdf",
     "Chemistry Evidence Base", COMMON, True),
    (DOCS / "model_robustness.md", "Furqan_Mizan_Model_Robustness.pdf",
     "Model Robustness against the Literature", COMMON, True),
    (DOCS / "ai_architecture.md", "Furqan_Mizan_AI_Architecture.pdf",
     "AI Architecture Decision Record", COMMON, True),
    (DOCS / "application_answers.md", "Furqan_Mizan_Application_Answers.pdf",
     "DTV Application Answer Bank", COMMON, True),
    (DOCS / "dtv_intelligence.md", "Furqan_Mizan_DTV_Intelligence.pdf",
     "Programme Intelligence Dossier", COMMON, True),
    (DOCS / "toolchain_plan.md", "Furqan_Mizan_Toolchain_Plan.pdf",
     "Simulation and CAD Toolchain", COMMON, True),
    # Read the MATLAB README where it LIVES, not a copy of it. A copy in
    # docs/ was identical the day it was made and would have gone stale the
    # first time the README was edited, silently, with the PDF still saying
    # the old thing. One source, one document.
    (ROOT / "matlab" / "README.md", "Furqan_Mizan_MATLAB_Model.pdf",
     "The MATLAB and Simulink Model", COMMON, True),
    (DOCS / "defect_register.md", "Furqan_Mizan_Defect_Register.pdf",
     "Defect Register and Gate Outcomes", COMMON, True),
    (DOCS / "threshold_revision_memo.md", "Furqan_Mizan_Threshold_Memo.pdf",
     "Two Failed Gates: a Decision Memo", COMMON, True),
    (DOCS / "linkedin_outreach.md", "Furqan_Mizan_Outreach_Kit.pdf",
     "Customer Discovery Kit", COMMON, False),
    (DOCS / "deck_content.md", "Furqan_Mizan_Deck.pdf",
     "Application Deck — Narrative", COMMON, False),
    (DOCS / "gemini_research_prompt_2.md", "Furqan_Mizan_Research_Round2.pdf",
     "Deep Research Brief — Round 2", [DATE], False),
    (DOCS / "gemini_research_prompt_4_chiller.md",
     "Furqan_Mizan_Research_Chiller.pdf",
     "Deep Research Brief — Chiller Performance Curves", [DATE], False),
    (OUT / "CV_Furqan_Shakeel.md", "Furqan_Mizan_CV_Furqan_Shakeel.pdf",
     "Curriculum Vitae — Engr. Furqan Shakeel", [DATE], False),
    (OUT / "CV_Damia_Baig.md", "Furqan_Mizan_CV_Damia_Baig.pdf",
     "Curriculum Vitae — Engr. Damia Baig", [DATE], False),
    (OUT / "CV_Muhammad_Ahsan.md", "Furqan_Mizan_CV_Muhammad_Ahsan.pdf",
     "Curriculum Vitae — Engr. Muhammad Ahsan", [DATE], False),
]

FOOTER = ("Furqan \\textbullet\\ Mizan condenser-water controller "
          "\\textbullet\\ DTV .dvp Cohort 2")


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    failed = []
    for src, dst, title, meta, toc in JOBS:
        if only and only not in src.name:
            continue
        if not src.exists():
            print(f"  SKIP {src.name} (not present)")
            continue
        print(f"{src.name}")
        if not build(src, OUT / dst, title, FOOTER, meta, toc=toc):
            failed.append(src.name)
    if failed:
        print("FAILED:", ", ".join(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
