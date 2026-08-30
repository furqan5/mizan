"""
MIZAN :: markdown -> PDF for the DTV upload
===========================================
DTV's application form takes PDF uploads. The source documents are
generated markdown (docs/*.md), so this converts them without any manual
step that could let a PDF drift from the evidence behind it.

Route: markdown -> HTML -> fpdf2.write_html. Deliberately plain typography;
the documents are read by technical reviewers scoring a maturity gate, not
by an audience that needs decoration.
"""
from __future__ import annotations

import pathlib
import re
import sys

import matplotlib
import markdown
from fpdf import FPDF
from fpdf.fonts import FontFace

# DejaVu Sans ships with matplotlib and covers the Unicode this package
# actually uses -- en/em dashes, <=, degree, superscripts, and the accents
# in the dataset authors' names. The core PDF fonts are latin-1 only and
# would silently mangle them.
FONT_DIR = pathlib.Path(matplotlib.get_data_path()) / "fonts" / "ttf"

# Times New Roman for the formal report: black-and-white, serif, the
# convention for an engineering proof-of-concept document. Falls back to
# DejaVu where the Windows fonts are unavailable.
WIN_FONTS = pathlib.Path("C:/Windows/Fonts")
SERIF = {
    "": WIN_FONTS / "times.ttf", "B": WIN_FONTS / "timesbd.ttf",
    "I": WIN_FONTS / "timesi.ttf", "BI": WIN_FONTS / "timesbi.ttf",
}
HAVE_SERIF = all(p.exists() for p in SERIF.values())

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUT = ROOT / "submission"
OUT.mkdir(exist_ok=True)

CSS_LIKE = {
    "h1": {"size": 17, "space_before": 6, "space_after": 3},
    "h2": {"size": 13, "space_before": 5, "space_after": 2},
    "h3": {"size": 11, "space_before": 4, "space_after": 2},
}


class Doc(FPDF):
    def __init__(self, footer_text="", serif=False):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.footer_text = footer_text
        self.set_auto_page_break(auto=True, margin=18)
        self.set_margins(18, 16, 18)
        self.add_font("DejaVu", "", FONT_DIR / "DejaVuSans.ttf")
        self.add_font("DejaVu", "B", FONT_DIR / "DejaVuSans-Bold.ttf")
        self.add_font("DejaVu", "I", FONT_DIR / "DejaVuSans-Oblique.ttf")
        self.add_font("DejaVu", "BI", FONT_DIR / "DejaVuSans-BoldOblique.ttf")
        self.body_font = "DejaVu"
        if serif and HAVE_SERIF:
            for style, path_ in SERIF.items():
                self.add_font("Times", style, path_)
            self.body_font = "Times"

    def footer(self):
        self.set_y(-14)
        self.set_font(self.body_font, "I", 8)
        self.set_text_color(120)
        self.cell(0, 5, f"{self.footer_text}", align="L")
        self.cell(0, 5, f"{self.page_no()}", align="R")
        self.set_text_color(0)


# Characters the agents' source documents use that DejaVu Sans has no
# glyph for. Replaced with plain-text equivalents rather than left to
# render as tofu boxes in a submission document.
GLYPH_FALLBACK = {
    "✅": "[YES]", "❌": "[NO]", "⚠️": "[!]",
    "⚠": "[!]", "📌": "*", "⭐": "*",
}


# Times New Roman covers Latin-1 but not the technical glyphs this package
# uses. For the formal serif report these are folded to ASCII equivalents,
# which is standard practice in a black-and-white engineering document.
SERIF_FOLD = {
    "≤": "<=", "≥": ">=", "×": "x", "−": "-",
    "₂": "2", "₃": "3", "²": "^2", "³": "^3",
    "⁹": "", "⁺": "+", "·": "-", "″": "''",
    "′": "'", "≈": "~", "±": "+/-", "→": "->",
    "←": "<-", "—": " - ", "–": "-", "…": "...",
    "µ": "u", "μ": "u", "Δ": "delta", "η": "eta",
    "“": '"', "”": '"', "‘": "'", "’": "'",
}


def md_to_html(md_text, serif=False):
    """Convert markdown to the HTML subset fpdf2 renders."""
    for bad, good in GLYPH_FALLBACK.items():
        md_text = md_text.replace(bad, good)
    if serif:
        for bad, good in SERIF_FOLD.items():
            md_text = md_text.replace(bad, good)
    html = markdown.markdown(md_text, extensions=["tables", "fenced_code"])
    # fpdf2's HTML renderer does not know these; normalise them out
    html = html.replace("<hr />", "<br>")
    html = html.replace("<em>", "<i>").replace("</em>", "</i>")
    html = html.replace("<strong>", "<b>").replace("</strong>", "</b>")
    # inline code -> bold, since fpdf2 has no <code> styling by default
    html = re.sub(r"<code>(.*?)</code>", r"<b>\1</b>", html, flags=re.S)
    html = re.sub(r"<pre>(.*?)</pre>", r"<p>\1</p>", html, flags=re.S)

    # fpdf2 refuses nested inline tags inside table cells. Strip emphasis
    # within cells only -- surrounding prose keeps its formatting, and a
    # cell reading "PASS" rather than a bold "PASS" loses nothing a
    # reviewer needs.
    def _flatten_cell(m):
        inner = re.sub(r"</?(b|i|em|strong|code)>", "", m.group(2))
        return f"<{m.group(1)}>{inner}</{m.group(1)}>"

    html = re.sub(r"<(td|th)>(.*?)</\1>", _flatten_cell, html, flags=re.S)
    return html


def convert(md_path, pdf_path, footer, serif=False):
    md_text = md_path.read_text(encoding="utf8")
    pdf = Doc(footer_text=footer, serif=serif)
    pdf.add_page()
    pdf.set_font(pdf.body_font, size=10.5 if serif else 9)
    if serif:
        # Strictly black and white: fpdf2 colours headings and links by
        # default, which is wrong for a formal engineering report.
        black = (0, 0, 0)
        styles = {t: FontFace(color=black, family="Times",
                              emphasis="BOLD" if t.startswith("h") else None)
                  for t in ("h1", "h2", "h3", "h4", "h5", "h6", "a")}
        pdf.write_html(md_to_html(md_text, serif=True),
                       table_line_separators=True, tag_styles=styles,
                       font_family="Times",
                       heading_sizes={"h1": 17, "h2": 13.5, "h3": 11.5,
                                      "h4": 10.5, "h5": 10.5, "h6": 10.5})
    else:
        pdf.write_html(md_to_html(md_text), table_line_separators=True)
    pdf.output(str(pdf_path))
    kb = pdf_path.stat().st_size / 1024
    print(f"  {pdf_path.name:34s} {pdf.page_no():3d} pages  {kb:7.1f} KB")


def main():
    jobs = [
        ("poc_report.md", "Furqan_Mizan_PoC_Report.pdf",
         "Furqan / Mizan - Proof-of-Concept Report - 29 Aug 2026"),
        ("deck_content.md", "Furqan_Mizan_Deck.pdf",
         "Furqan / Mizan - Application Deck - 29 Aug 2026"),
        ("commercialisation.md", "Furqan_Mizan_Commercialisation.pdf",
         "Furqan / Mizan - Commercialisation Plan and Budget - 29 Aug 2026"),
        ("ai_architecture.md", "Furqan_Mizan_AI_Architecture.pdf",
         "Furqan / Mizan - AI Architecture Decision Record - 29 Aug 2026"),
        ("application_answers.md", "Furqan_Mizan_Application_Answers.pdf",
         "Furqan / Mizan - DTV Application Answer Bank - 29 Aug 2026"),
        ("gemini_research_prompt_2.md", "Furqan_Mizan_Research_Round2.pdf",
         "Furqan / Mizan - Deep Research Prompt Round 2"),
        ("model_robustness.md", "Furqan_Mizan_Model_Robustness.pdf",
         "Furqan / Mizan - Model Robustness vs Literature - 29 Aug 2026"),
        ("linkedin_outreach.md", "Furqan_Mizan_Outreach_Kit.pdf",
         "Furqan / Mizan - Customer Discovery Kit"),
        ("market_dossier.md", "Furqan_Mizan_Market_Dossier.pdf",
         "Furqan / Mizan - Market Dossier - 29 Aug 2026"),
        ("chemistry_evidence.md", "Furqan_Mizan_Chemistry_Evidence.pdf",
         "Furqan / Mizan - Chemistry Evidence Base - 29 Aug 2026"),
    ]
    cv_jobs = [
        ("CV_Furqan_Shakeel.md", "Furqan_Mizan_CV_Furqan_Shakeel.pdf",
         "Furqan / Mizan - CV: Engr. Furqan Shakeel"),
        ("CV_Damia_Baig.md", "Furqan_Mizan_CV_Damia_Baig.pdf",
         "Furqan / Mizan - CV: Engr. Damia Baig"),
        ("CV_Muhammad_Ahsan.md", "Furqan_Mizan_CV_Muhammad_Ahsan.pdf",
         "Furqan / Mizan - CV: Engr. Muhammad Ahsan"),
    ]

    print("generating submission PDFs:")
    for src, dst, footer in cv_jobs:
        p = OUT / src
        if not p.exists():
            print(f"  SKIP {src} (not present)")
            continue
        try:
            convert(p, OUT / dst, footer,
                    serif=(src == "poc_report.md"))
        except Exception as e:
            print(f"  FAIL {src}: {type(e).__name__}: {e}")

    for src, dst, footer in jobs:
        p = DOCS / src
        if not p.exists():
            print(f"  SKIP {src} (not generated yet)")
            continue
        try:
            convert(p, OUT / dst, footer,
                    serif=(src == "poc_report.md"))
        except Exception as e:
            print(f"  FAIL {src}: {type(e).__name__}: {e}")
    print(f"\n-> {OUT}")


if __name__ == "__main__":
    main()
