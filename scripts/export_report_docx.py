#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/export_report_docx.py
Exports docs/bao_cao_tien_do_lan_2.md into an academic standard Microsoft Word (.docx) document.
Formatting specifications:
- Paper Size: A4
- Margins: Top 2.0 cm, Bottom 2.0 cm, Left 3.0 cm, Right 2.0 cm
- Font: Times New Roman 13 pt
- Line Spacing: 1.3 lines
- Paragraph Spacing: Space after 4 pt
- Headings: Times New Roman, bold, hierarchically sized
- Tables: Full borders, light gray header background, bold text, centered
"""

import re
from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Cm, Pt, RGBColor


def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>'))


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for m, val in [("w:top", top), ("w:bottom", bottom), ("w:left", left), ("w:right", right)]:
        node = OxmlElement(m)
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        tcMar.append(node)
    tcPr.append(tcMar)


def set_table_borders(table, color="B0B0B0", sz="4", val="single"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f"<w:tblBorders {nsdecls('w')}>\n"
        f'  <w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>\n'
        f'  <w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>\n'
        f'  <w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>\n'
        f'  <w:insideV w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>\n'
        f'  <w:left w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>\n'
        f'  <w:right w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>\n'
        f"</w:tblBorders>"
    )
    tblPr.append(borders)


def parse_markdown_table(lines):
    rows = []
    for line in lines:
        line = line.strip()
        if not line.startswith("|"):
            continue
        parts = [p.strip() for p in line.split("|")]
        # Drop leading and trailing empty splits from leading/trailing |
        if len(parts) >= 3:
            row_cells = parts[1:-1]
            # Check if separator row
            if all(re.match(r"^:?-+:?$", c) for c in row_cells):
                continue
            rows.append(row_cells)
    return rows


def clean_inline_md(text):
    # Strip backticks, bold, italics for simple table / text rendering
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"`(.*?)`", r"\1", text)
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"\\times", "×", text)
    text = re.sub(r"\\rightarrow", "→", text)
    text = re.sub(r"\\leftrightarrow", "↔", text)
    text = text.replace("$", "")
    return text.strip()


def export_markdown_to_docx(md_path: Path, docx_path: Path):
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    doc = Document()

    # Page Setup: A4 with standard margins
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(2.0)
    section.left_margin = Cm(3.0)
    section.right_margin = Cm(2.0)

    # Base Normal Style
    normal_style = doc.styles["Normal"]
    normal_style.font.name = "Times New Roman"
    normal_style.font.size = Pt(13)
    normal_style.font.color.rgb = RGBColor(0, 0, 0)
    normal_style.paragraph_format.line_spacing = 1.3
    normal_style.paragraph_format.space_after = Pt(4)
    normal_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    lines = content.split("\n")
    i = 0
    in_code_block = False
    code_block_lines = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Handle Code Blocks
        if stripped.startswith("```"):
            if in_code_block:
                in_code_block = False
                code_text = "\n".join(code_block_lines)
                code_block_lines = []
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Cm(0.8)
                p.paragraph_format.right_indent = Cm(0.8)
                p.paragraph_format.space_before = Pt(4)
                p.paragraph_format.space_after = Pt(6)
                p.paragraph_format.line_spacing = 1.1
                run = p.add_run(code_text)
                run.font.name = "Consolas"
                run.font.size = Pt(9.5)
                run.font.color.rgb = RGBColor(40, 40, 40)
            else:
                in_code_block = True
                code_block_lines = []
            i += 1
            continue

        if in_code_block:
            code_block_lines.append(line)
            i += 1
            continue

        # Handle Tables
        if stripped.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            table_data = parse_markdown_table(table_lines)
            if table_data and len(table_data) > 0:
                n_rows = len(table_data)
                n_cols = max(len(row) for row in table_data)
                tbl = doc.add_table(rows=n_rows, cols=n_cols)
                tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
                set_table_borders(tbl)

                for r_idx, row in enumerate(table_data):
                    for c_idx in range(n_cols):
                        cell = tbl.cell(r_idx, c_idx)
                        set_cell_margins(cell, top=100, bottom=100, left=140, right=140)
                        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                        raw_text = row[c_idx] if c_idx < len(row) else ""
                        clean_text = clean_inline_md(raw_text)
                        cell.text = clean_text

                        p = cell.paragraphs[0]
                        p.paragraph_format.line_spacing = 1.15
                        p.paragraph_format.space_before = Pt(2)
                        p.paragraph_format.space_after = Pt(2)

                        if r_idx == 0:
                            set_cell_background(cell, "EAEAEA")
                            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                            for run in p.runs:
                                run.font.name = "Times New Roman"
                                run.font.size = Pt(11)
                                run.font.bold = True
                        else:
                            if c_idx == 0 and len(clean_text) <= 5:
                                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                            elif any(
                                term in table_lines[0].lower()
                                for term in ["tỉ lệ", "kết quả", "thời gian", "cer", "wer", "mức độ"]
                            ):
                                if c_idx in (1, 2, 3):
                                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                            for run in p.runs:
                                run.font.name = "Times New Roman"
                                run.font.size = Pt(11)

                p_after = doc.add_paragraph()
                p_after.paragraph_format.space_after = Pt(4)
            continue

        # Skip dividers
        if stripped == "---":
            i += 1
            continue

        # Headings
        if stripped.startswith("# "):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(6)
            run = p.add_run(clean_inline_md(stripped[2:]))
            run.font.name = "Times New Roman"
            run.font.size = Pt(16)
            run.font.bold = True
            run.font.color.rgb = RGBColor(0, 32, 96)  # Dark Navy
            i += 1
            continue

        if stripped.startswith("## "):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(4)
            run = p.add_run(clean_inline_md(stripped[3:]))
            run.font.name = "Times New Roman"
            run.font.size = Pt(14)
            run.font.bold = True
            run.font.color.rgb = RGBColor(0, 51, 102)
            i += 1
            continue

        if stripped.startswith("### "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(3)
            run = p.add_run(clean_inline_md(stripped[4:]))
            run.font.name = "Times New Roman"
            run.font.size = Pt(13)
            run.font.bold = True
            i += 1
            continue

        if stripped.startswith("#### "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(2)
            run = p.add_run(clean_inline_md(stripped[5:]))
            run.font.name = "Times New Roman"
            run.font.size = Pt(13)
            run.font.bold = True
            run.font.italic = True
            i += 1
            continue

        # Table Captions (Bảng x.y: ...)
        if stripped.startswith("**Bảng ") or stripped.startswith("**Hình "):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(3)
            run = p.add_run(clean_inline_md(stripped))
            run.font.name = "Times New Roman"
            run.font.size = Pt(12)
            run.font.bold = True
            run.font.italic = True
            i += 1
            continue

        # Bullet list
        if stripped.startswith("* ") or stripped.startswith("- "):
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.8)
            p.paragraph_format.space_after = Pt(3)
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            run_bullet = p.add_run("• ")
            run_bullet.font.bold = True
            # Parse bold runs in item
            raw_item = stripped[2:]
            parts = re.split(r"(\*\*.*?\*\*)", raw_item)
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    r = p.add_run(clean_inline_md(part[2:-2]))
                    r.font.bold = True
                else:
                    p.add_run(clean_inline_md(part))
            i += 1
            continue

        # Numbered list item
        m_num = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if m_num:
            num_str, item_text = m_num.groups()
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.8)
            p.paragraph_format.space_after = Pt(3)
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            run_num = p.add_run(f"{num_str}. ")
            run_num.font.bold = True
            parts = re.split(r"(\*\*.*?\*\*)", item_text)
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    r = p.add_run(clean_inline_md(part[2:-2]))
                    r.font.bold = True
                else:
                    p.add_run(clean_inline_md(part))
            i += 1
            continue

        # Normal paragraph
        if stripped:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.space_after = Pt(4)
            parts = re.split(r"(\*\*.*?\*\*)", stripped)
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    r = p.add_run(clean_inline_md(part[2:-2]))
                    r.font.bold = True
                else:
                    p.add_run(clean_inline_md(part))

        i += 1

    doc.save(docx_path)
    try:
        print(f"Successfully generated academic docx: {docx_path}".encode("utf-8", errors="replace").decode("utf-8"))
    except Exception:
        pass


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    md_file = root / "docs" / "bao_cao_tien_do_lan_2.md"
    docx_file = root / "docs" / "bao_cao_tien_do_lan_2.docx"
    export_markdown_to_docx(md_file, docx_file)
