import base64
import io
import os
import re
from typing import Any, Dict, List

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor
from PIL import Image

MODULES_META = {
    "kdjk": {
        "name": "Komunikasi Data & Jaringan Komputer",
        "short": "KDJK",
        "meetings": 14,
        "tools": "Cisco Packet Tracer & Winbox",
        "needs_pj": False,
        "topics": [
            "Sistem Perkabelan (Straight & Cross)",
            "Pengalamatan IP (Subnetting & Supernetting)",
            "Konfigurasi Point to Point Menggunakan Ubiquiti",
            "Fiber Optik",
            "LAN dan Aplikasi (Cisco Packet Tracer)",
            "Subnetting dan Superneting (CIDR)",
            "Routing (Static, RIP, EIGRP, OSPF)",
            "DHCP Server dan Domain Name Server (DNS)",
            "Virtual LAN (VLAN)",
            "Web Server dan Proxy Server",
            "Wireless LAN",
            "User Profile (Hotspot MikroTik)",
            "Manajemen Bandwidth",
            "Virtual Private Network (VPN)",
        ],
    },
    "sdata": {
        "name": "Struktur Data",
        "short": "SData",
        "meetings": 11,
        "tools": "C++",
        "needs_pj": True,
        "topics": [
            "Array Statis",
            "Array Dinamis",
            "Linked List",
            "Variasi Linked List (Circular & Doubly Linked List)",
            "Stack dengan Array",
            "Queue",
            "Circular Queue",
            "Priority Queue",
            "Tree (General Tree)",
            "Binary Search Tree (BST)",
            "BST Seimbang (AVL Tree)",
        ],
    },
    "basdat": {
        "name": "Basis Data",
        "short": "BasisData",
        "meetings": 12,
        "tools": "MySQL, ERD & MongoDB",
        "needs_pj": False,
        "topics": [
            "Identifikasi Entitas untuk Studi Proyek",
            "Konversi Model Data ke Tabel",
            "Normalisasi (1NF, 2NF, 3NF)",
            "Data Definition Language (DDL)",
            "Indeks",
            "DML dan Fungsi Agregasi",
            "Relasi Tabel dengan Join",
            "Trigger, Keamanan Data, dan Stored Procedure",
            "Pengenalan NoSQL (MongoDB Atlas & Compass)",
            "Operasi CRUD pada NoSQL",
            "NoSQL Index dan Agregasi",
            "NoSQL - Pemrograman dengan Python (PyMongo)",
        ],
    },
    "statistika": {
        "name": "Statistika Informatika",
        "short": "Statistika",
        "meetings": 14,
        "tools": "SPSS, MS Excel & Python",
        "needs_pj": True,
        "topics": [
            "Pembentukan Distribusi Frekuensi",
            "Pembentukan Distribusi Frekuensi Kumulatif",
            "Ukuran Pemusatan: Mean dan Median",
            "Ukuran Pemusatan: Modus dan Kuartil",
            "Ukuran Penyebaran Data: Deviasi Rata & Standar Deviasi",
            "Ukuran Penyebaran Data dengan Pemrograman Python",
            "Probabilistik Dasar dan Probabilistik Bersyarat",
            "Distribusi Teoritis (Binomial dan Normal)",
            "Distribusi Teoritis (Hipergeometrik dan Poisson)",
            "Uji Hipotesis (Parameter Mean - 1 Sampel)",
            "Uji Hipotesis dengan 2 Sampel Berpasangan",
            "Uji Reliabilitas dan Uji Validitas",
            "Inhal Praktikum",
            "Ujian Responsi Praktikum",
        ],
    },
}

TECHNICAL_TERMS = [
    "Cisco Packet Tracer", "TCP/IP", "IP address", "primary key", "foreign key",
    "linked list", "circular linked list", "doubly linked list", "priority queue",
    "circular queue", "binary search tree", "balance factor", "standar deviasi",
    "stored procedure", "executionStats", "ping", "router", "switch", "server",
    "client", "gateway", "subnet", "subnetting", "supernetting", "protocol",
    "packet", "database", "query", "table", "array", "stack", "queue", "pointer",
    "struct", "tree", "graph", "output", "input", "software", "hardware",
    "browser", "localhost", "syntax", "error", "debug", "compile", "execute",
    "mean", "median", "modus", "kuartil", "varians", "regresi", "korelasi",
    "anova", "hipotesis", "dataset", "flowchart", "topology", "interface",
    "ethernet", "wireless", "DNS", "DHCP", "HTTP", "HTTPS", "SQL", "NoSQL",
    "ERD", "MySQL", "MongoDB", "PyMongo", "Minitab", "SPSS", "VLAN", "OSPF",
    "RIP", "EIGRP", "NAT", "ARP", "ICMP", "UDP", "TCP", "MAC", "CLI", "GUI",
    "SELECT", "INSERT", "UPDATE", "DELETE", "JOIN", "CREATE", "DROP", "ALTER",
    "WHERE", "GROUP BY", "ORDER BY", "TRIGGER", "COLLSCAN", "IXSCAN", "node",
    "root", "leaf", "subtree", "traversal", "push", "pop", "enqueue", "dequeue",
    "nullptr", "null", "boolean", "integer", "string", "float", "double", "char",
    "void", "return", "class", "object", "method", "function", "variable",
    "p-value", "t-test", "z-score", "histogram", "boxplot", "hotspot", "Winbox",
    "MikroTik", "VPN", "PPTP", "fiber optik", "splicer", "cleaver", "stripper",
]

_TERM_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(t) for t in sorted(TECHNICAL_TERMS, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)


def sanitize_filename_part(value: str) -> str:
    """Sanitize a string for safe inclusion in the official .docx filename while preserving spaces."""
    cleaned = re.sub(r'[\\/:*?"<>|]+', "", value.strip())
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned or "TanpaNama"


def build_official_filename(
    module_key: str,
    nim: str,
    student_name: str,
    meeting_number: int,
    pj_assistant: str = "",
    day_name: str = "",
    exec_time: str = "",
) -> str:
    """Build the exact official filename according to LabCraft / LabTIF rules."""
    nim_part = sanitize_filename_part(nim)
    name_part = sanitize_filename_part(student_name)
    meet_part = str(meeting_number).strip() or "1"
    nim_3 = nim_part[-3:] if len(nim_part) >= 3 else nim_part
    slot_raw = f"{day_name.strip()} {exec_time.strip()}".strip()
    slot_part = sanitize_filename_part(slot_raw) if slot_raw else "Slot"
    pj_part = sanitize_filename_part(pj_assistant) if pj_assistant.strip() else "PJ"

    if module_key == "sdata":
        return f"Pert{meet_part}_{nim_3}_{name_part}_SData_{slot_part}_{pj_part}.docx"
    if module_key == "kdjk":
        return f"{nim_part}_{name_part}_{meet_part}_KDJK.docx"
    if module_key == "basdat":
        return f"Pertemuan {meet_part}_{nim_part}_{name_part}.docx"
    if module_key == "statistika":
        return f"{nim_part}_{name_part}_{slot_part}_{pj_part}_STATISTIKA({meet_part}).docx"
    return f"{nim_part}_{name_part}_{meet_part}_Laporan.docx"


def to_capital_each_words(text: str) -> str:
    """Format figure/table/code captions in Capital Each Words per LabTIF rules."""
    return " ".join(w[:1].upper() + w[1:] if w else "" for w in text.strip().split())


def _apply_font(
    run,
    font_name: str = "Calibri",
    size_pt: int = 11,
    bold: bool = False,
    italic: bool = False,
    color=None,
):
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    run.bold = bold
    run.italic = italic
    if color:
        run.font.color.rgb = color


def add_formatted_paragraph(
    doc: Document,
    text: str,
    align=WD_ALIGN_PARAGRAPH.JUSTIFY,
    bold: bool = False,
    size_pt: int = 11,
    line_spacing: float = 1.15,
    space_after_pt: int = 6,
    auto_italic: bool = True,
    left_indent_cm: float = 0.0,
):
    """Add a Calibri 11pt 1.15-spaced paragraph, italicizing foreign/technical terms automatically."""
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.line_spacing = line_spacing
    p.paragraph_format.space_after = Pt(space_after_pt)
    p.paragraph_format.space_before = Pt(0)
    if left_indent_cm:
        p.paragraph_format.left_indent = Cm(left_indent_cm)

    if not text:
        return p

    if not auto_italic:
        run = p.add_run(text)
        _apply_font(run, size_pt=size_pt, bold=bold)
        return p

    pos = 0
    for match in _TERM_PATTERN.finditer(text):
        start, end = match.span()
        if start > pos:
            run = p.add_run(text[pos:start])
            _apply_font(run, size_pt=size_pt, bold=bold, italic=False)
        term_run = p.add_run(text[start:end])
        _apply_font(term_run, size_pt=size_pt, bold=bold, italic=True)
        pos = end

    if pos < len(text):
        run = p.add_run(text[pos:])
        _apply_font(run, size_pt=size_pt, bold=bold, italic=False)

    return p


def add_heading_block(doc: Document, title: str):
    """Add a section heading (never auto-italicized per LabTIF sub-bab rule)."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.keep_with_next = True
    run = p.add_run(title)
    _apply_font(run, size_pt=12, bold=True, italic=False, color=RGBColor(0x11, 0x18, 0x27))
    return p


def add_subheading_block(doc: Document, title: str, left_indent_cm: float = 0.6):
    """Add an indented sub-chapter heading (e.g. A. Alat dan Bahan:)."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    if left_indent_cm:
        p.paragraph_format.left_indent = Cm(left_indent_cm)
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.keep_with_next = True
    run = p.add_run(title)
    _apply_font(run, size_pt=11, bold=True, italic=False)
    return p


def add_numbered_item(doc: Document, idx: int, text: str):
    """Add an indented numbered item (1. ...) with auto-italicized technical terms."""
    return add_formatted_paragraph(
        doc,
        f"{idx}. {text}",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
        space_after_pt=3,
        left_indent_cm=1.2,
    )


def _decode_and_compress_image(data_url: str, max_width: int = 1200) -> io.BytesIO:
    """Decode a base64 image data URL and compress it via Pillow for lightweight .docx."""
    if "," in data_url:
        _, b64_data = data_url.split(",", 1)
    else:
        b64_data = data_url
    raw_bytes = base64.b64decode(b64_data)
    img = Image.open(io.BytesIO(raw_bytes))

    if img.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        bg.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
        img = bg
    elif img.mode != "RGB":
        img = img.convert("RGB")

    if img.width > max_width:
        ratio = max_width / float(img.width)
        new_height = max(1, int(img.height * ratio))
        img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

    out = io.BytesIO()
    img.save(out, format="JPEG", quality=82, optimize=True)
    out.seek(0)
    return out


def _add_figure_block(
    doc: Document,
    image_data: Dict[str, Any],
    caption_label: str,
    left_indent_cm: float = 0.0,
    max_width_cm: float | None = None,
):
    """Insert a compressed image aligned with its caption and description."""
    data_url = image_data.get("dataUrl", "")
    title = to_capital_each_words((image_data.get("title") or "").strip())
    description = (image_data.get("description") or "").strip()
    content_width_cm = 15.0 - left_indent_cm
    if max_width_cm is not None:
        content_width_cm = min(content_width_cm, max_width_cm)

    if data_url:
        try:
            img_stream = _decode_and_compress_image(data_url)
            pic_p = doc.add_paragraph()
            pic_p.alignment = WD_ALIGN_PARAGRAPH.LEFT if left_indent_cm else WD_ALIGN_PARAGRAPH.CENTER
            if left_indent_cm:
                pic_p.paragraph_format.left_indent = Cm(left_indent_cm)
            pic_p.paragraph_format.space_before = Pt(6)
            pic_p.paragraph_format.space_after = Pt(3)
            pic_p.paragraph_format.keep_with_next = True
            run = pic_p.add_run()
            run.add_picture(img_stream, width=Cm(content_width_cm))
        except Exception:
            add_formatted_paragraph(
                doc,
                f"[Gagal memuat gambar untuk {caption_label}]",
                align=WD_ALIGN_PARAGRAPH.CENTER,
                left_indent_cm=left_indent_cm,
            )

    caption_text = f"{caption_label} {title}" if title else caption_label
    cap_p = doc.add_paragraph()
    cap_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if left_indent_cm:
        cap_p.paragraph_format.left_indent = Cm(left_indent_cm)
    cap_p.paragraph_format.space_after = Pt(4)
    cap_p.paragraph_format.line_spacing = 1.15
    cap_run = cap_p.add_run(caption_text)
    _apply_font(cap_run, size_pt=11, bold=True, italic=False)

    if description:
        desc_text = description if re.match(r"^Ket\s*:", description, re.IGNORECASE) else f"Ket : {description}"
        add_formatted_paragraph(
            doc,
            desc_text,
            align=WD_ALIGN_PARAGRAPH.JUSTIFY,
            left_indent_cm=left_indent_cm,
        )


def _set_cell_borders(cell):
    """Apply clean 1pt border around a code frame cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = OxmlElement("w:tcBorders")
    for side in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "6")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "9CA3AF")
        tcBorders.append(el)
    tcPr.append(tcBorders)


def _set_table_left_indent(table, indent_cm: float):
    """Indent a table by indent_cm so its left edge aligns with indented body/images."""
    if not indent_cm:
        return
    tblPr = table._tbl.tblPr
    tblInd = OxmlElement("w:tblInd")
    tblInd.set(qn("w:w"), str(int(round(indent_cm * 567))))
    tblInd.set(qn("w:type"), "dxa")
    tblPr.append(tblInd)


def _add_code_block(
    doc: Document,
    code_data: Dict[str, Any],
    code_label: str,
    left_indent_cm: float = 0.0,
):
    """Render source code in a bordered frame, Courier New 10pt, line-spaced 1.0, numbered lines."""
    title = to_capital_each_words((code_data.get("title") or "").strip())
    code_text = (code_data.get("code") or "").rstrip("\n")
    description = (code_data.get("description") or "").strip()
    if not code_text:
        return

    content_width_cm = 15.0 - left_indent_cm

    caption_text = f"{code_label} {title}" if title else code_label
    cap_p = doc.add_paragraph()
    cap_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if left_indent_cm:
        cap_p.paragraph_format.left_indent = Cm(left_indent_cm)
    cap_p.paragraph_format.space_before = Pt(8)
    cap_p.paragraph_format.space_after = Pt(4)
    cap_p.paragraph_format.line_spacing = 1.15
    cap_p.paragraph_format.keep_with_next = True
    cap_run = cap_p.add_run(caption_text)
    _apply_font(cap_run, size_pt=11, bold=False, italic=False)

    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    table.autofit = False
    _set_table_left_indent(table, left_indent_cm)
    cell = table.cell(0, 0)
    cell.width = Cm(content_width_cm)
    _set_cell_borders(cell)
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)

    lines = code_text.splitlines()
    numbered = "\n".join(f"{idx}. {line}" for idx, line in enumerate(lines, start=1))
    run = p.add_run(numbered)
    _apply_font(run, font_name="Courier New", size_pt=10, bold=False, italic=False)

    if description:
        desc_text = description if re.match(r"^Ket\s*:", description, re.IGNORECASE) else f"Ket : {description}"
        add_formatted_paragraph(
            doc,
            desc_text,
            align=WD_ALIGN_PARAGRAPH.JUSTIFY,
            left_indent_cm=left_indent_cm,
        )


def generate_report_docx(payload: Dict[str, Any], output_path: str) -> str:
    """Generate the formatted Laprakin .docx file following LabTIF UAD 2026 rules."""
    module_key = payload.get("moduleKey", "kdjk")
    module_meta = MODULES_META.get(module_key, MODULES_META["kdjk"])

    nim = (payload.get("nim") or "").strip()
    student_name = (payload.get("studentName") or "").strip()
    meeting_number = int(payload.get("meetingNumber") or 1)
    class_name = (payload.get("className") or "").strip()
    topic_title = (payload.get("topicTitle") or "").strip()
    day_name = (payload.get("dayName") or "").strip()
    exec_date = (payload.get("execDate") or "").strip()
    exec_time = (payload.get("execTime") or "").strip()
    pj_assistant = (payload.get("pjAssistant") or "").strip()

    has_pretest = bool(payload.get("hasPretest", True))
    pretest_images: List[Dict[str, Any]] = payload.get("pretestImages") or []
    pretest_qas: List[Dict[str, Any]] = payload.get("pretestQAs") or []

    result_images: List[Dict[str, Any]] = payload.get("resultImages") or []
    code_blocks: List[Dict[str, Any]] = payload.get("codeBlocks") or []
    tools_materials: List[str] = [
        str(x).strip() for x in (payload.get("toolsMaterials") or []) if str(x).strip()
    ]
    work_steps: List[str] = [
        str(x).strip() for x in (payload.get("workSteps") or []) if str(x).strip()
    ]
    analysis_text = (payload.get("analysisText") or "").strip()
    review_text = (payload.get("reviewText") or "").strip()

    has_posttest = bool(payload.get("hasPosttest", True))
    posttest_images: List[Dict[str, Any]] = payload.get("posttestImages") or []
    posttest_code_blocks: List[Dict[str, Any]] = payload.get("posttestCodeBlocks") or []
    posttest_qas: List[Dict[str, Any]] = payload.get("posttestQAs") or []
    posttest_analysis = (payload.get("posttestAnalysis") or "").strip()

    doc = Document()

    # Format TBLR 3333 (Top, Bottom, Left, Right = 3 cm) on A4 portrait
    for section in doc.sections:
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)
        section.top_margin = Cm(3.0)
        section.bottom_margin = Cm(3.0)
        section.left_margin = Cm(3.0)
        section.right_margin = Cm(3.0)

    normal_style = doc.styles["Normal"]
    normal_style.font.name = "Calibri"
    normal_style.font.size = Pt(11)

    # 1. COVER (Sesuai Template & Contoh Resmi UAD)
    cover_top = [
        ("LAPORAN PRAKTIKUM", 14, True),
        (module_meta["name"], 14, True),
        ("Materi", 12, True),
        (topic_title.upper(), 13, True),
        (f"{day_name}, {exec_date} {exec_time}".strip(), 12, True),
    ]
    for text, size, is_bold in cover_top:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.15
        _apply_font(p.add_run(text), size_pt=size, bold=is_bold)

    # Logo UAD di tengah sampul
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "img", "logo-uad.png")
    logo_p = doc.add_paragraph()
    logo_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    logo_p.paragraph_format.space_before = Pt(36)
    logo_p.paragraph_format.space_after = Pt(36)
    if os.path.exists(logo_path):
        logo_p.add_run().add_picture(logo_path, width=Cm(4.5))

    author_lines = [
        ("Disusun Oleh:", 11, True),
        (student_name, 11, False),
        (nim, 11, False),
    ]

    for text, size, is_bold in author_lines:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.15
        _apply_font(p.add_run(text), size_pt=size, bold=is_bold)

    spacer2 = doc.add_paragraph()
    spacer2.paragraph_format.space_after = Pt(36)

    for inst_line in [
        "PROGRAM STUDI S1 INFORMATIKA",
        "FAKULTAS TEKNOLOGI INDUSTRI",
        "UNIVERSITAS AHMAD DAHLAN",
        "2026",
    ]:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.15
        _apply_font(p.add_run(inst_line), size_pt=12, bold=True)

    doc.add_page_break()

    # 2. I. Pre Test (Bab 1 -> Gambar 1.x)
    add_heading_block(doc, "I. Pre Test")
    if not has_pretest:
        add_formatted_paragraph(doc, "Pada pertemuan praktikum ini tidak dilaksanakan sesi Pre Test.")
    else:
        if pretest_qas:
            for idx, qa in enumerate(pretest_qas, start=1):
                q_text = (qa.get("question") or "").strip()
                a_text = (qa.get("answer") or "").strip()
                if q_text:
                    add_formatted_paragraph(doc, f"Pertanyaan {idx}: {q_text}", bold=False, left_indent_cm=0.6)
                if a_text:
                    add_formatted_paragraph(doc, f"Jawaban: {a_text}", left_indent_cm=0.6)
        if pretest_images:
            for idx, img in enumerate(pretest_images, start=1):
                _add_figure_block(doc, img, f"Gambar 1.{idx}", max_width_cm=11.0)
        elif not pretest_qas:
            add_formatted_paragraph(doc, "Tidak ada salinan hasil Pre Test yang dilampirkan.")

    # 3. II. Hasil Praktikum (A. Alat dan Bahan, B. Langkah Kerja, C. Implementasi/Screenshot, D. Analisis Hasil)
    doc.add_page_break()
    add_heading_block(doc, "II. Hasil Praktikum")

    add_subheading_block(doc, "A. Alat dan Bahan:")
    if tools_materials:
        for idx, item in enumerate(tools_materials, start=1):
            add_numbered_item(doc, idx, item)
    else:
        add_numbered_item(doc, 1, "Laptop / PC")
        add_numbered_item(doc, 2, module_meta["tools"])

    add_subheading_block(doc, "B. Langkah Kerja:")
    if work_steps:
        for idx, step_text in enumerate(work_steps, start=1):
            add_numbered_item(doc, idx, step_text)
    else:
        add_numbered_item(doc, 1, f"Mempersiapkan lingkungan kerja menggunakan {module_meta['tools']}.")
        add_numbered_item(doc, 2, f"Melaksanakan percobaan sesuai materi {topic_title}.")

    add_subheading_block(doc, "C. Implementasi/Screenshot:")
    if result_images:
        for idx, img in enumerate(result_images, start=1):
            _add_figure_block(doc, img, f"Gambar 2.{idx}", left_indent_cm=0.6)
    else:
        add_formatted_paragraph(
            doc,
            "Belum ada tangkapan layar hasil praktikum yang dilampirkan.",
            left_indent_cm=0.6,
        )

    if code_blocks:
        for idx, cb in enumerate(code_blocks, start=1):
            _add_code_block(doc, cb, f"Kode Program 2.{idx}", left_indent_cm=0.6)

    add_subheading_block(doc, "D. Analisis Hasil:")
    if analysis_text:
        for para in analysis_text.splitlines():
            if para.strip():
                add_formatted_paragraph(doc, para.strip(), left_indent_cm=0.6)
    else:
        add_formatted_paragraph(
            doc,
            "Tidak ada analisis hasil praktikum yang dituliskan.",
            left_indent_cm=0.6,
        )

    # 4. III. Post Test (Bab 3 -> Gambar 3.x, Kode Program 3.x)
    doc.add_page_break()
    add_heading_block(doc, "III. Post Test")
    if not has_posttest:
        add_formatted_paragraph(doc, "Pada pertemuan praktikum ini tidak dilaksanakan sesi Post Test.")
    else:
        if posttest_qas:
            for idx, qa in enumerate(posttest_qas, start=1):
                q_text = (qa.get("question") or "").strip()
                a_text = (qa.get("answer") or "").strip()
                if q_text:
                    add_formatted_paragraph(doc, f"Pertanyaan {idx}: {q_text}", bold=True)
                if a_text:
                    add_formatted_paragraph(doc, f"Jawaban: {a_text}")
        if posttest_images:
            for idx, img in enumerate(posttest_images, start=1):
                _add_figure_block(doc, img, f"Gambar 3.{idx}")
        elif not posttest_qas and not posttest_code_blocks:
            add_formatted_paragraph(doc, "Tidak ada luaran Post Test yang dilampirkan.")

        if posttest_code_blocks:
            for idx, cb in enumerate(posttest_code_blocks, start=1):
                _add_code_block(doc, cb, f"Kode Program 3.{idx}")

        if posttest_analysis:
            add_formatted_paragraph(doc, "Analisis hasil :", bold=True, space_after_pt=3)
            for para in posttest_analysis.splitlines():
                if para.strip():
                    add_formatted_paragraph(doc, para.strip())

    # 5. Sub Judul Ulasan Praktikum (di akhir, di bawah Analisis Hasil Post Test)
    add_subheading_block(doc, "Ulasan Praktikum :", left_indent_cm=0.0)
    if review_text:
        for para in review_text.splitlines():
            if para.strip():
                add_formatted_paragraph(doc, para.strip())
    else:
        add_formatted_paragraph(doc, "Tidak ada ulasan praktikum yang dituliskan.")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    return output_path
