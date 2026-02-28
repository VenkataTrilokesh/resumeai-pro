"""
Resume Parser - Parse DOCX and PDF files into structured data
Detects sections, extracts content, preserves structure
"""

import re
import io
from typing import Optional

# ─── Section Headers Detection ─────────────────────────────────────────────
SECTION_PATTERNS = {
    "summary": [
        r"(?:professional\s+)?summary", "objective", "profile",
        "about me", "career objective", "professional profile",
        "executive summary", "overview"
    ],
    "skills": [
        "skills", "technical skills", "core competencies", "expertise",
        "competencies", "technologies", "tech stack", "tools",
        "key skills", "technical expertise", "areas of expertise"
    ],
    "experience": [
        "experience", "work experience", "professional experience",
        "employment history", "work history", "career history",
        "professional background", "employment"
    ],
    "education": [
        "education", "academic background", "educational background",
        "qualifications", "academic qualifications", "degrees"
    ],
    "projects": [
        "projects", "personal projects", "key projects",
        "project experience", "notable projects", "portfolio"
    ],
    "certifications": [
        "certifications", "certificates", "licenses", "credentials",
        "professional certifications", "awards", "achievements"
    ],
    "publications": [
        "publications", "papers", "research", "articles", "patents"
    ],
    "languages": [
        "languages", "language skills"
    ]
}


def detect_section(line: str) -> Optional[str]:
    """Detect if a line is a section header"""
    line_clean = line.strip().lower()
    line_clean = re.sub(r'[^a-z\s]', '', line_clean).strip()
    
    for section, patterns in SECTION_PATTERNS.items():
        for pattern in patterns:
            if re.match(r'^' + pattern + r'\s*$', line_clean):
                return section
            if line_clean == pattern.lower():
                return section
    return None


def is_likely_header(line: str) -> bool:
    """Heuristic to detect section headers"""
    line = line.strip()
    if not line:
        return False
    
    # All caps, short line
    if line.isupper() and len(line) < 60 and len(line) > 2:
        return True
    
    # Title case, short, no punctuation at end
    if line[0].isupper() and len(line) < 50 and not line.endswith('.'):
        words = line.split()
        if all(w[0].isupper() for w in words if w):
            if detect_section(line):
                return True
    
    return False


def extract_name(lines: list) -> str:
    """Extract candidate name from top of resume"""
    for i, line in enumerate(lines[:5]):
        line = line.strip()
        if not line:
            continue
        
        # Skip obvious non-names
        if any(c in line for c in ['@', 'http', 'www', '+', '(']):
            continue
        
        # Name is usually 2-4 words, title case, no special chars
        words = line.split()
        if 1 < len(words) <= 4:
            if all(w[0].isupper() for w in words if w and w[0].isalpha()):
                return line
    
    return ""


def extract_contact_info(text: str) -> dict:
    """Extract contact information"""
    contact = {}
    
    # Email
    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    if email_match:
        contact['email'] = email_match.group()
    
    # Phone
    phone_match = re.search(
        r'(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}',
        text
    )
    if phone_match:
        contact['phone'] = phone_match.group()
    
    # LinkedIn
    linkedin_match = re.search(r'linkedin\.com/in/[\w-]+', text, re.IGNORECASE)
    if linkedin_match:
        contact['linkedin'] = linkedin_match.group()
    
    # GitHub
    github_match = re.search(r'github\.com/[\w-]+', text, re.IGNORECASE)
    if github_match:
        contact['github'] = github_match.group()
    
    # Location (city, state pattern)
    location_match = re.search(
        r'(?:^|\n)([A-Z][a-zA-Z\s]+,\s*[A-Z]{2}(?:\s+\d{5})?)',
        text, re.MULTILINE
    )
    if location_match:
        contact['location'] = location_match.group(1).strip()
    
    return contact


def extract_years_experience(text: str) -> int:
    """Estimate total years of experience from resume"""
    import datetime
    current_year = datetime.datetime.now().year
    
    # Look for year ranges in experience section
    year_pattern = r'\b(19|20)\d{2}\b'
    years = [int(y) for y in re.findall(year_pattern, text)]
    
    if len(years) >= 2:
        years = [y for y in years if 1990 <= y <= current_year]
        if years:
            earliest = min(years)
            return current_year - earliest
    
    # Look for explicit "X years of experience"
    exp_match = re.search(r'(\d+)\+?\s*years?\s*(?:of\s+)?(?:experience|exp)', text, re.IGNORECASE)
    if exp_match:
        return int(exp_match.group(1))
    
    return 3  # Default


def parse_experience_entries(text: str) -> list:
    """Parse work experience entries"""
    entries = []
    
    # Split by common patterns (company names followed by dates)
    # Look for patterns like "Company Name — Role — Location\nDate Range"
    # or "Company Name | Role\nDate"
    
    lines = text.split('\n')
    current_entry = None
    current_bullets = []
    
    date_pattern = re.compile(
        r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|'
        r'April|June|July|August|September|October|November|December)\.?\s+\d{4}|'
        r'\d{4}\s*[-–—]\s*(?:\d{4}|present|current|now)',
        re.IGNORECASE
    )
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if this is a new job entry (has a date)
        if date_pattern.search(line):
            if current_entry:
                current_entry['bullets'] = current_bullets
                entries.append(current_entry)
            
            # Try to extract company/role from context
            current_entry = {
                'raw': line,
                'dates': date_pattern.search(line).group() if date_pattern.search(line) else '',
                'company': '',
                'role': '',
                'location': ''
            }
            current_bullets = []
            
        elif current_entry is not None:
            # Check if it's a bullet point
            if line.startswith(('•', '-', '–', '●', '*', '·', '▪')):
                bullet_text = re.sub(r'^[•\-–●\*·▪]\s*', '', line).strip()
                if bullet_text:
                    current_bullets.append(bullet_text)
            elif line and not line.startswith(('•', '-', '–')):
                # Could be company/role line
                if not current_entry.get('company') and not date_pattern.search(line):
                    current_entry['company'] = line[:100]
    
    # Add last entry
    if current_entry:
        current_entry['bullets'] = current_bullets
        entries.append(current_entry)
    
    return entries


def parse_text_to_sections(text: str) -> dict:
    """
    Parse raw text into structured resume sections
    Returns dict with all identified sections
    """
    lines = text.split('\n')
    
    sections = {
        "name": "",
        "contact": {},
        "summary": "",
        "skills": [],
        "experience": [],
        "education": [],
        "projects": [],
        "certifications": [],
        "raw_sections": {}
    }
    
    # Extract name and contact
    sections["name"] = extract_name(lines)
    sections["contact"] = extract_contact_info(text)
    
    # Parse sections
    current_section = None
    section_content = []
    raw_sections = {}
    
    for line in lines:
        line_stripped = line.strip()
        
        # Check for section header
        detected = detect_section(line_stripped)
        if detected or is_likely_header(line_stripped):
            # Save previous section
            if current_section and section_content:
                raw_sections[current_section] = '\n'.join(section_content)
            
            current_section = detected or current_section
            section_content = []
        else:
            if line_stripped:
                section_content.append(line_stripped)
    
    # Save last section
    if current_section and section_content:
        raw_sections[current_section] = '\n'.join(section_content)
    
    sections["raw_sections"] = raw_sections
    
    # Parse specific sections
    if "summary" in raw_sections:
        sections["summary"] = raw_sections["summary"].strip()
    
    if "skills" in raw_sections:
        skills_text = raw_sections["skills"]
        # Extract skills (split by common delimiters)
        skills = re.split(r'[,|•\n\t]+', skills_text)
        sections["skills"] = [s.strip() for s in skills if s.strip() and len(s.strip()) > 1]
    
    if "experience" in raw_sections:
        exp_text = raw_sections["experience"]
        sections["experience_raw"] = exp_text
        entries = parse_experience_entries(exp_text)
        sections["experience"] = entries
    
    if "education" in raw_sections:
        sections["education"] = raw_sections["education"].strip()
    
    if "projects" in raw_sections:
        sections["projects"] = raw_sections["projects"].strip()
    
    if "certifications" in raw_sections:
        sections["certifications"] = raw_sections["certifications"].strip()
    
    sections["years_experience"] = extract_years_experience(text)
    sections["full_text"] = text
    
    return sections


def parse_docx(file_bytes: bytes) -> dict:
    """Parse a DOCX file into structured resume data"""
    try:
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        
        full_text = []
        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text)
        
        text = '\n'.join(full_text)
        result = parse_text_to_sections(text)
        result["source_format"] = "docx"
        return result
        
    except Exception as e:
        return {"error": str(e), "full_text": ""}


def parse_pdf(file_bytes: bytes) -> dict:
    """Parse a PDF file into structured resume data"""
    text = ""
    
    # Try pdfplumber first
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            pages_text = []
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(page_text)
            text = '\n'.join(pages_text)
    except Exception:
        pass
    
    # Fallback to PyPDF2
    if not text:
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            for page in reader.pages:
                text += page.extract_text() or ''
        except Exception:
            pass
    
    if not text:
        return {"error": "Could not extract text from PDF", "full_text": ""}
    
    result = parse_text_to_sections(text)
    result["source_format"] = "pdf"
    return result


def parse_resume(file_bytes: bytes, filename: str) -> dict:
    """Main entry point for resume parsing"""
    filename_lower = filename.lower()
    
    if filename_lower.endswith('.docx'):
        return parse_docx(file_bytes)
    elif filename_lower.endswith('.pdf'):
        return parse_pdf(file_bytes)
    else:
        return {"error": "Unsupported file format. Use .docx or .pdf"}
