#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/export_report_v2_docx.py
Exports docs/bao_cao_tien_do_lan_2_v2.md into a high-standard academic Word (.docx) document.
Specifications:
- Paper: A4 (21.0 x 29.7 cm)
- Margins: Top 2.0 cm, Bottom 2.0 cm, Left 3.0 cm, Right 2.0 cm
- Font: Times New Roman 13pt, 1.3 line spacing, 4pt space after
- Numbered headings (H1: 15pt Navy bold, H2: 13.5pt bold, H3: 13pt bold italic)
- Tables: Full borders, light gray header background (#EAEAEA), bold headers, 11pt font
- Figures: Auto-inserted PNG charts from docs/figures/ with centered bold captions
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


def set_cell_margins(cell, top=100, bottom=100, left=140, right=140):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for m, val in [("w:top", top), ("w:bottom", bottom), ("w:left", left), ("w:right", right)]:
        node = OxmlElement(m)
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        tcMar.append(node)
    tcPr.append(tcMar)


def set_table_borders(table, color="A0A0A0", sz="4", val="single"):
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
        if len(parts) >= 3:
            row_cells = parts[1:-1]
            if all(re.match(r"^:?-+:?$", c) for c in row_cells):
                continue
            rows.append(row_cells)
    return rows


def clean_inline_md(text):
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"`(.*?)`", r"\1", text)
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"\\times", "×", text)
    text = re.sub(r"\\rightarrow", "→", text)
    text = re.sub(r"\\leftrightarrow", "↔", text)
    text = text.replace("$", "")
    return text.strip()


def export_markdown_to_docx(md_path: Path, docx_path: Path, figures_dir: Path):
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    doc = Document()

    # A4 Margins: Top 2.0cm, Bottom 2.0cm, Left 3.0cm, Right 2.0cm
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(2.0)
    section.left_margin = Cm(3.0)
    section.right_margin = Cm(2.0)

    # Base Style
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

    inserted_figures = set()

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Handle Code Blocks
        if stripped.startswith("```"):
            if in_code_block:
                in_code_block = False
                code_text = "\n".join(code_block_lines)
                code_block_lines = []
                # Check if it was an ASCII diagram that can be replaced by an image
                if "HÌNH 3.1:" in code_text or "SƠ ĐỒ NGUYÊN NHÂN VÀ GIẢI PHÁP OCR" in code_text:
                    fig_p = figures_dir / "hinh_3_1_nguyen_nhan_giai_phap.png"
                    if fig_p.exists() and "hinh_3_1" not in inserted_figures:
                        inserted_figures.add("hinh_3_1")
                        p_img = doc.add_paragraph()
                        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        p_img.paragraph_format.space_before = Pt(8)
                        p_img.paragraph_format.space_after = Pt(3)
                        p_img.add_run().add_picture(str(fig_p), width=Cm(15.5))
                        p_cap = doc.add_paragraph()
                        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        p_cap.paragraph_format.space_after = Pt(8)
                        r_cap = p_cap.add_run(
                            "Hình 3.1: Sơ đồ phân tích nguyên nhân gốc rễ và giải pháp kỹ thuật cho mô hình OCR"
                        )
                        r_cap.font.name = "Times New Roman"
                        r_cap.font.size = Pt(11)
                        r_cap.font.bold = True
                        r_cap.font.italic = True
                    i += 1
                    continue

                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Cm(0.8)
                p.paragraph_format.right_indent = Cm(0.8)
                p.paragraph_format.space_before = Pt(4)
                p.paragraph_format.space_after = Pt(6)
                p.paragraph_format.line_spacing = 1.15
                run = p.add_run(code_text)
                run.font.name = "Consolas"
                run.font.size = Pt(9.5)
                run.font.color.rgb = RGBColor(30, 30, 30)
            else:
                in_code_block = True
                code_block_lines = []
            i += 1
            continue

        if in_code_block:
            code_block_lines.append(line)
            i += 1
            continue

        # Check for figure insertion cues in prose
        if "Hình 3.2" in stripped and "hinh_3_2" not in inserted_figures:
            fig_p = figures_dir / "hinh_3_2_kien_truc_he_thong.png"
            if fig_p.exists():
                inserted_figures.add("hinh_3_2")
                p_img = doc.add_paragraph()
                p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_img.paragraph_format.space_before = Pt(8)
                p_img.paragraph_format.space_after = Pt(3)
                p_img.add_run().add_picture(str(fig_p), width=Cm(15.5))
                p_cap = doc.add_paragraph()
                p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_cap.paragraph_format.space_after = Pt(8)
                r_cap = p_cap.add_run("Hình 3.2: Kiến trúc vi dịch vụ và phân hệ lưu trữ, tra cứu văn bản DocuCTSV")
                r_cap.font.name = "Times New Roman"
                r_cap.font.size = Pt(11)
                r_cap.font.bold = True
                r_cap.font.italic = True

        if "Hình 4.1 và Hình 4.2" in stripped or ("Hình 4.1" in stripped and "hinh_4_1" not in inserted_figures):
            # Insert Hinh 4.1
            fig1_p = figures_dir / "hinh_4_1_latency_throughput.png"
            if fig1_p.exists() and "hinh_4_1" not in inserted_figures:
                inserted_figures.add("hinh_4_1")
                p_img1 = doc.add_paragraph()
                p_img1.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_img1.paragraph_format.space_before = Pt(8)
                p_img1.paragraph_format.space_after = Pt(3)
                p_img1.add_run().add_picture(str(fig1_p), width=Cm(15.5))
                p_cap1 = doc.add_paragraph()
                p_cap1.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_cap1.paragraph_format.space_after = Pt(8)
                r_cap1 = p_cap1.add_run(
                    "Hình 4.1: Biểu đồ thời gian xử lý trang P50 và thông lượng nhận dạng qua các cấu hình TrOCR-Vi"
                )
                r_cap1.font.name = "Times New Roman"
                r_cap1.font.size = Pt(11)
                r_cap1.font.bold = True
                r_cap1.font.italic = True

            # Insert Hinh 4.2
            fig2_p = figures_dir / "hinh_4_2_truncation_cer.png"
            if fig2_p.exists() and "hinh_4_2" not in inserted_figures:
                inserted_figures.add("hinh_4_2")
                p_img2 = doc.add_paragraph()
                p_img2.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_img2.paragraph_format.space_before = Pt(8)
                p_img2.paragraph_format.space_after = Pt(3)
                p_img2.add_run().add_picture(str(fig2_p), width=Cm(15.5))
                p_cap2 = doc.add_paragraph()
                p_cap2.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_cap2.paragraph_format.space_after = Pt(8)
                r_cap2 = p_cap2.add_run(
                    "Hình 4.2: Biểu đồ tỷ lệ cụt đuôi dòng (Truncation Rate) và tỷ lệ lỗi ký tự (CER) trên tập kiểm định 32 trang"
                )
                r_cap2.font.name = "Times New Roman"
                r_cap2.font.size = Pt(11)
                r_cap2.font.bold = True
                r_cap2.font.italic = True

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
                        set_cell_margins(cell, top=90, bottom=90, left=130, right=130)
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
                                run.font.size = Pt(10.5)
                                run.font.bold = True
                        else:
                            if c_idx == 0 and len(clean_text) <= 6:
                                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                            elif any(
                                term in table_lines[0].lower()
                                for term in ["tỉ lệ", "kết quả", "thời gian", "cer", "wer", "mức độ", "trọng số"]
                            ):
                                if c_idx in (1, 2, 3, 4):
                                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                            for run in p.runs:
                                run.font.name = "Times New Roman"
                                run.font.size = Pt(10.5)

                p_after = doc.add_paragraph()
                p_after.paragraph_format.space_after = Pt(4)
            continue

        # Skip horizontal rules
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
            run.font.size = Pt(11.5)
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

        # Numbered list
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
    print("Exported v2 docx successfully.")


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    md_file = root / "docs" / "bao_cao_tien_do_lan_2_v2.md"
    docx_file = root / "docs" / "bao_cao_tien_do_lan_2_v2.docx"
    fig_dir = root / "docs" / "figures"
    export_markdown_to_docx(md_file, docx_file, fig_dir)
