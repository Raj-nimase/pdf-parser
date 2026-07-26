import re
from typing import List, Optional

# Major standalone document sections that should always be Level 1 Headings (#)
MAJOR_SECTIONS = {
    "ABSTRACT",
    "ACKNOWLEDGEMENT",
    "ACKNOWLEDGEMENTS",
    "INDEX",
    "TABLE OF CONTENTS",
    "TOC",
    "CONTENT",
    "CONTENTS",
    "LIST OF FIGURES",
    "LIST OF FIGURE",
    "LIST OF TABLES",
    "LIST OF TABLE",
    "INTRODUCTION",
    "OBJECTIVES",
    "OBJECTIVE",
    "PROJECT SPECIFICATION",
    "PROJECT SPECIFICATION / TOOLS REQUIRED",
    "TOOLS REQUIRED",
    "FEATURES OF THE PROJECT",
    "FEATURES",
    "ADVANTAGES",
    "DISADVANTAGES",
    "ADVANTAGES AND DISADVANTAGES",
    "METHODS / STEPS IMPLEMENTED",
    "METHODS AND STEPS IMPLEMENTED",
    "METHODOLOGY",
    "SOURCE CODE",
    "OUTPUT",
    "OUTPUTS",
    "RESULT",
    "RESULTS",
    "RESULTS AND DISCUSSION",
    "RESULT AND APPLICATION",
    "CONCLUSION",
    "CONCLUSIONS",
    "CONCLUSION AND FUTURE SCOPE",
    "REFERENCES",
    "REFERENCE",
    "REFERENCES AND BIBLIOGRAPHY",
    "APPENDIX",
    "APPENDICES",
    "IEEE RESEARCH PAPER"
}

# Known subheading titles that often appear after numbers like 1.Specifications, 2.Working Principle
SUBHEADING_TITLE_KEYWORDS = re.compile(
    r"^(?:Specifications|Working Principle|Role in\b.*|Operation in\b.*|Types of\b.*|Applications|Advantages|Disadvantages|Importance in\b.*|Functional Requirements|Hardware Requirements|Input Specifications|Output Specifications|Connector Type|Protection Features|Physical Features|Circuit Layout|Component Arrangement|Testing Methodology|Performance Testing|System Testing|Evaluation Criteria|Feedback Control System|Microcontroller-Based PWM|Protection Circuits|Digital Display System|High Power Design|Compact PCB Design|Renewable Energy Integration|Project Overview|Project Scope|Voltage Conversion|Input Controls|Target Applications|Project Limitations|Future Scope|System Design|Hardware Requirements:|Software Requirements:|Technical Requirements:)$",
    re.IGNORECASE
)

def unwrap_toc_and_pseudo_tables(markdown_text: str) -> str:
    """
    Detects false tables created by PyMuPDF4LLM around Table of Contents / INDEX lists
    or single-column text boxes and unwraps them into clean Markdown list items / text lines.
    Also removes synthetic PyMuPDF table captions like 'Table 2.3: Table'.
    """
    lines = markdown_text.splitlines()
    cleaned_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]
        trimmed = line.strip()

        # Remove PyMuPDF synthetic table captions like 'Table 2.3: Table'
        if re.match(r"^\s*Table\s+\d+(?:\.\d+)?:\s*Table\s*$", trimmed, re.IGNORECASE):
            i += 1
            continue

        # Check if line is start of a Markdown table (| ... |)
        if trimmed.startswith("|") and trimmed.endswith("|") and trimmed.count("|") >= 2:
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                table_lines.append(lines[i].strip())
                i += 1

            # Analyze table contents to see if it's a TOC / INDEX pseudo-table or list table
            cell_texts = []
            for tl in table_lines:
                # Skip separator lines like | --- | --- |
                if re.match(r"^\s*\|?\s*:?-+:?\s*(\|?\s*:?-+:?\s*)*\|?\s*$", tl):
                    continue
                cells = [c.strip() for c in tl.strip("|").split("|") if c.strip()]
                cell_texts.extend(cells)

            # Check if table cells contain list/TOC items (e.g. 1.INTRODUCTION, 2. OBJECTIVES, etc.)
            has_list_items = any(re.match(r"^\d+[.)]\s*", c) for c in cell_texts)
            has_toc_headers = any(re.search(r"\b(INTRODUCTION|OBJECTIVES|SPECIFICATION|FEATURES|ADVANTAGES|METHODS|SOURCE CODE|OUTPUT|CONCLUSION|ACKNOWLEDGEMENT)\b", c, re.IGNORECASE) for c in cell_texts)

            if has_list_items or has_toc_headers or len(cell_texts) <= len(table_lines) * 2:
                # Unwrap table cells into clean lines
                for cell in cell_texts:
                    # Skip table header titles like 'Sr.No.', 'Chapter', 'Page No.' if present in TOC
                    if re.match(r"^(Sr\.?\s*No\.?|Name of Student|Enrollment No\.?|Roll No\.?|Exam Seat No\.?|Page No\.?)$", cell, re.IGNORECASE):
                        continue
                    cleaned_lines.append(cell)
                continue
            else:
                # Re-insert standard data table lines
                cleaned_lines.extend(table_lines)
                continue

        cleaned_lines.append(line)
        i += 1

    return "\n".join(cleaned_lines)

def clean_raw_line(line: str) -> str:
    """Strips leading # hashes, bold/italic markers, and surrounding whitespace."""
    s = line.strip()
    s = re.sub(r"^#{1,6}\s*", "", s).strip()
    s = re.sub(r"^\*\*(.+)\*\*$", r"\1", s).strip()
    s = re.sub(r"^_(.+)_$", r"\1", s).strip()
    return s.strip()

def strip_numeric_heading_prefix(title: str) -> str:
    """
    Strips numeric section prefixes from a heading title string.
    Examples:
        '1.1 OVERVIEW OF DC TO DC BOOST CONVERTER' -> 'OVERVIEW OF DC TO DC BOOST CONVERTER'
        '2.1 DC-DC CONVERTERS AND THEIR IMPORTANCE' -> 'DC-DC CONVERTERS AND THEIR IMPORTANCE'
        '5.2.1 Inductor' -> 'Inductor'
        'CHAPTER 4 :- METHODOLOGY' -> 'CHAPTER 4: METHODOLOGY'
        '1.INTRODUCTION' -> 'INTRODUCTION'
    """
    cleaned = clean_raw_line(title)

    # Normalize CHAPTER X :- TITLE -> CHAPTER X: TITLE
    ch_match = re.match(r"^(CHAPTER|Chapter)\s+(\d+|[IVXLCDM]+)\s*[:\-]+\s*(.+)$", cleaned, re.IGNORECASE)
    if ch_match:
        ch_keyword = ch_match.group(1).upper()
        ch_num = ch_match.group(2)
        ch_title = ch_match.group(3).strip()
        return f"{ch_keyword} {ch_num}: {ch_title}"

    # Strip multi-level numbers (e.g. 5.2.10, 3.8.1, 1.1, 2.2)
    cleaned = re.sub(r"^\d+(?:\.\d+)+\s*[:\-\.]?\s*", "", cleaned)
    # Strip single digit + dot if followed by space or title (e.g. 1. Specifications -> Specifications, 1.INTRODUCTION -> INTRODUCTION)
    cleaned = re.sub(r"^\d+[.)]\s*", "", cleaned)

    return cleaned.strip()

def is_chapter_heading(line: str) -> bool:
    """Returns True if line is a Chapter title like CHAPTER 1: INTRODUCTION."""
    cleaned = clean_raw_line(line)
    return bool(re.match(r"^(CHAPTER|Chapter)\s+(\d+|[IVXLCDM]+)\b", cleaned, re.IGNORECASE))

def is_major_section(line: str) -> bool:
    """Returns True if line is a major section title like ABSTRACT, ACKNOWLEDGEMENT, INTRODUCTION, etc."""
    cleaned = clean_raw_line(line)
    cleaned_no_punct = re.sub(r"[^\w\s/]", "", cleaned).strip().upper()
    if cleaned_no_punct in MAJOR_SECTIONS:
        return True
    # Check stripped without digits prefix (e.g. "1.INTRODUCTION" -> "INTRODUCTION")
    stripped = re.sub(r"^\d+[.)]\s*", "", cleaned_no_punct).strip()
    return stripped in MAJOR_SECTIONS

def process_markdown_structure(markdown_text: str) -> str:
    """
    Processes raw Markdown extracted from PDF to produce clean, well-structured
    headings, subheadings, and lists compatible with TipTap.

    Rules applied:
    1. Unwraps false TOC / INDEX tables into clean Markdown lists
    2. Chapter headings (CHAPTER 1: INTRODUCTION) -> Level 1 (# CHAPTER 1: INTRODUCTION)
    3. Major section titles (ABSTRACT, ACKNOWLEDGEMENT, INDEX, INTRODUCTION, OBJECTIVES, etc.) -> Level 1 (# INTRODUCTION)
    4. 2-level section numbers (1.1, 2.1, 2.2) -> Level 2 (## OVERVIEW...)
    5. 3-level section numbers (5.2.1, 3.8.1) -> Level 3 (### Inductor)
    6. Single-digit subheadings (1.Specifications, 2.Working Principle) -> Level 4 (#### Specifications)
    7. Bullet lists (•, ◦, ▪) -> Standard Markdown bullets (- Item)
    8. Numbered lists (1., 2.) -> Standard Markdown numbered items (1. Item)
    9. Letter / Roman lists (a), b), i., ii.) -> Standardized list items
    """
    if not markdown_text:
        return ""

    # Step 0: Unwrap false TOC/INDEX tables and remove synthetic table captions
    unwrapped_text = unwrap_toc_and_pseudo_tables(markdown_text)

    lines = unwrapped_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    processed_lines: List[str] = []
    in_code_block = False
    in_index_section = False
    last_index_num: Optional[int] = None

    for line in lines:
        trimmed = line.strip()

        # Handle Code Fences
        if trimmed.startswith("```"):
            in_code_block = not in_code_block
            processed_lines.append(line)
            continue

        if in_code_block or not trimmed:
            processed_lines.append(line)
            continue

        raw_unhashed = clean_raw_line(trimmed)

        # Detect INDEX section state
        if is_major_section(trimmed) and re.search(r"\b(INDEX|TABLE OF CONTENTS|TOC|CONTENT|CONTENTS)\b", trimmed, re.IGNORECASE):
            in_index_section = True
            last_index_num = None
            clean_title = re.sub(r"^[#\*\_\s]+", "", raw_unhashed).strip(" *_#")
            processed_lines.append(f"# {clean_title}")
            continue

        # If inside INDEX section, treat numbered lines as clean numbered list items (1. INTRODUCTION, 2. OBJECTIVES...)
        if in_index_section:
            num_item_match = re.match(r"^\s*(\d+)[.)]\s*\.?(.*)$", trimmed)
            if num_item_match:
                num = int(num_item_match.group(1))
                content = num_item_match.group(2).strip()

                # If numbering restarts at 1. after reaching 2+, exit INDEX section and treat as body section header
                if last_index_num is not None and last_index_num >= 2 and num == 1:
                    in_index_section = False
                    last_index_num = None
                else:
                    last_index_num = num
                    processed_lines.append(f"{num}. {content}")
                    continue

        # ---------------------------------------------------------------------
        # 1. HEADINGS & SUBHEADINGS RECOGNITION
        # ---------------------------------------------------------------------

        # Case 1: Chapter Headings (CHAPTER 1: INTRODUCTION or #### CHAPTER 1: INTRODUCTION)
        if is_chapter_heading(trimmed):
            clean_title = strip_numeric_heading_prefix(raw_unhashed)
            processed_lines.append(f"# {clean_title}")
            continue

        # Case 2: Major Standalone Document Sections (ABSTRACT, ACKNOWLEDGEMENT, INTRODUCTION, OBJECTIVES, etc.)
        if is_major_section(trimmed):
            clean_title = strip_numeric_heading_prefix(raw_unhashed)
            processed_lines.append(f"# {clean_title}")
            continue

        # Case 3: 4-Level Subsections (3.8.4.1 Title or #### 3.8.4.1 Title)
        match_4 = re.match(r"^\s*(?:#{1,6}\s*)?(\d+\.\d+\.\d+\.\d+)\s*[:\-\.]?\s+(.+)$", trimmed)
        if match_4:
            clean_title = strip_numeric_heading_prefix(match_4.group(2))
            processed_lines.append(f"#### {clean_title}")
            continue

        # Case 4: 3-Level Sub-subheadings (5.2.1 Inductor or ### 5.2.1 Inductor)
        match_3 = re.match(r"^\s*(?:#{1,6}\s*)?(\d+\.\d+\.\d+)\s*[:\-\.]?\s+(.+)$", trimmed)
        if match_3:
            clean_title = strip_numeric_heading_prefix(match_3.group(2))
            processed_lines.append(f"### {clean_title}")
            continue

        # Case 5: 2-Level Subheadings with numbers (1.1 OVERVIEW... or 2.1 DC-DC CONVERTERS... or ## 1.1 OVERVIEW...)
        match_2 = re.match(r"^\s*(?:#{1,6}\s*)?(\d+\.\d+)\s*[:\-\.]?\s+(.+)$", trimmed)
        if match_2:
            clean_title = strip_numeric_heading_prefix(match_2.group(2))
            processed_lines.append(f"## {clean_title}")
            continue

        # Case 6: Subheadings with existing Markdown Hashes (##### OVERVIEW... or #### OVERVIEW...)
        match_existing_hash = re.match(r"^\s*(#{2,6})\s+(.+)$", trimmed)
        if match_existing_hash:
            raw_title = match_existing_hash.group(2)
            clean_title = strip_numeric_heading_prefix(raw_title)
            processed_lines.append(f"## {clean_title}")
            continue

        # Case 7: Single-digit Subheadings (e.g. 1.Specifications, 2.Working Principle)
        match_single_no_space = re.match(r"^\s*(\d+)\.([A-Z][A-Za-z0-9\s&/\-\(\)]+)\s*$", trimmed)
        if match_single_no_space:
            sub_title = match_single_no_space.group(2).strip()
            processed_lines.append(f"#### {sub_title}")
            continue

        match_single_sub = re.match(r"^\s*(\d+)[.)]\s+([A-Z][A-Za-z0-9\s&/\-\(\)]+)\s*$", trimmed)
        if match_single_sub:
            sub_title = match_single_sub.group(2).strip()
            if SUBHEADING_TITLE_KEYWORDS.match(sub_title):
                processed_lines.append(f"#### {sub_title}")
                continue

        # ---------------------------------------------------------------------
        # 2. LISTS IDENTIFICATION & FORMATTING
        # ---------------------------------------------------------------------

        bullet_match = re.match(r"^(\s*)[•◦▪●–—]\s*(.*)$", line)
        if bullet_match:
            indent = bullet_match.group(1)
            content = bullet_match.group(2).strip()
            processed_lines.append(f"{indent}- {content}")
            continue

        std_bullet_match = re.match(r"^(\s*)[*+\-]\s+(.*)$", line)
        if std_bullet_match:
            indent = std_bullet_match.group(1)
            content = std_bullet_match.group(2).strip()
            processed_lines.append(f"{indent}- {content}")
            continue

        num_match = re.match(r"^(\s*)(\d+)[.)]\s*\.?(.*)$", line)
        if num_match:
            indent = num_match.group(1)
            num = num_match.group(2)
            content = num_match.group(3).strip()
            processed_lines.append(f"{indent}{num}. {content}")
            continue

        letter_match = re.match(r"^(\s*)(?:\(?([a-zA-Z])\)?)[.)]\s*(.*)$", line)
        if letter_match:
            indent = letter_match.group(1)
            letter = letter_match.group(2)
            content = letter_match.group(3).strip()
            processed_lines.append(f"{indent}{letter}) {content}")
            continue

        roman_match = re.match(r"^(\s*)(?:\(?([iI][vV]|[vV]?[iI]{1,3}|[iI][xX])\)?)[.)]\s*(.*)$", line)
        if roman_match:
            indent = roman_match.group(1)
            roman = roman_match.group(2)
            content = roman_match.group(3).strip()
            processed_lines.append(f"{indent}{roman}. {content}")
            continue

        processed_lines.append(line)

    result = "\n".join(processed_lines)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result
