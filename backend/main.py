"""
FastAPI Backend - Resume Optimizer API
All endpoints for the web application
"""

import os
import io
import json
import traceback
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

from resume_parser import parse_resume
from jd_analyzer import analyze_jd
from optimizer import optimize_resume, calculate_ats_score
from docx_generator import generate_docx

app = FastAPI(title="Resume Optimizer API", version="2.0")

# Allow all origins for local use
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class OptimizeRequest(BaseModel):
    jd_text: str
    resume_json: Optional[dict] = None


class ResumeSections(BaseModel):
    resume_data: dict


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "Resume Optimizer API v2.0"}


@app.post("/parse-resume")
async def parse_resume_endpoint(file: UploadFile = File(...)):
    """
    Upload and parse a resume file (.docx or .pdf)
    Returns structured resume data
    """
    try:
        filename = file.filename or "resume.docx"
        content = await file.read()
        
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        if len(content) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")
        
        result = parse_resume(content, filename)
        
        if "error" in result:
            raise HTTPException(status_code=422, detail=result["error"])
        
        return JSONResponse(content={"success": True, "data": result})
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parse error: {str(e)}")


@app.post("/analyze-jd")
async def analyze_jd_endpoint(body: dict):
    """
    Analyze a job description text
    Returns extracted skills, keywords, requirements
    """
    try:
        jd_text = body.get("jd_text", "")
        if not jd_text or len(jd_text.strip()) < 50:
            raise HTTPException(status_code=400, detail="JD text too short")
        
        analysis = analyze_jd(jd_text)
        return JSONResponse(content={"success": True, "analysis": analysis})
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


@app.post("/optimize")
async def optimize_endpoint(
    jd_text: str = Form(...),
    file: Optional[UploadFile] = File(None),
    resume_json: Optional[str] = Form(None)
):
    """
    Main optimization endpoint
    Takes JD text + resume file (or cached JSON) → returns optimized resume
    """
    try:
        # Parse resume
        if file and file.filename:
            content = await file.read()
            if len(content) == 0:
                raise HTTPException(status_code=400, detail="Empty resume file")
            resume_data = parse_resume(content, file.filename)
        elif resume_json:
            try:
                resume_data = json.loads(resume_json)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid resume JSON")
        else:
            raise HTTPException(status_code=400, detail="No resume provided")
        
        if not jd_text or len(jd_text.strip()) < 50:
            raise HTTPException(status_code=400, detail="JD text too short or empty")
        
        # Analyze JD
        jd_analysis = analyze_jd(jd_text)
        
        # Optimize
        result = optimize_resume(resume_data, jd_analysis)
        
        # Build HTML representation for the editor
        html = build_resume_html(result["optimized"])
        
        return JSONResponse(content={
            "success": True,
            "html": html,
            "optimized_data": result["optimized"],
            "ats": result["ats"],
            "keywords_added": result["keywords_added"],
            "keywords_existing": result["keywords_existing"],
            "jd_analysis": {
                "job_title": result["jd_analysis"].get("job_title", ""),
                "domain": result["jd_analysis"].get("domain", ""),
                "experience_level": result["jd_analysis"].get("experience_level", ""),
                "technical_skills": result["jd_analysis"].get("technical_skills", [])[:15],
                "keywords": result["jd_analysis"].get("keywords", [])[:15],
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Optimization error: {str(e)}")


@app.post("/download-docx")
async def download_docx(body: dict):
    """
    Generate and download DOCX from resume data or HTML
    """
    try:
        resume_data = body.get("resume_data", {})
        
        if not resume_data:
            raise HTTPException(status_code=400, detail="No resume data provided")
        
        docx_bytes = generate_docx(resume_data)
        
        name = resume_data.get("name", "Resume").replace(" ", "_")
        filename = f"{name}_Optimized_Resume.docx"
        
        return StreamingResponse(
            io.BytesIO(docx_bytes),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DOCX generation error: {str(e)}")


@app.post("/download-pdf")
async def download_pdf(body: dict):
    """
    Generate PDF from resume data
    """
    try:
        resume_data = body.get("resume_data", {})
        
        if not resume_data:
            raise HTTPException(status_code=400, detail="No resume data provided")
        
        # First generate DOCX, then convert to PDF
        pdf_bytes = generate_pdf(resume_data)
        
        name = resume_data.get("name", "Resume").replace(" ", "_")
        filename = f"{name}_Optimized_Resume.pdf"
        
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation error: {str(e)}")


def build_resume_html(resume_data: dict) -> str:
    """
    Build a clean Word-style HTML representation for the TipTap editor
    """
    import html as html_lib
    
    def esc(text):
        if not text:
            return ""
        return html_lib.escape(str(text))
    
    parts = []
    
    name = resume_data.get("name", "")
    contact = resume_data.get("contact", {})
    summary = resume_data.get("summary", "")
    skills = resume_data.get("skills", [])
    experience = resume_data.get("experience", [])
    experience_raw = resume_data.get("experience_raw", "")
    education = resume_data.get("education", "")
    projects = resume_data.get("projects", "")
    certifications = resume_data.get("certifications", "")
    
    # Name
    if name:
        parts.append(f'<h1 class="resume-name">{esc(name.upper())}</h1>')
    
    # Contact
    contact_items = []
    for key in ["email", "phone", "location", "linkedin", "github"]:
        if contact.get(key):
            contact_items.append(esc(contact[key]))
    if contact_items:
        parts.append(f'<p class="contact-line">{" | ".join(contact_items)}</p>')
    
    # Summary
    if summary:
        parts.append('<h2 class="section-header">PROFESSIONAL SUMMARY</h2>')
        parts.append(f'<p class="summary-text">{esc(summary)}</p>')
    
    # Skills
    if skills:
        parts.append('<h2 class="section-header">CORE COMPETENCIES &amp; TECHNICAL SKILLS</h2>')
        # Group into rows of 6
        rows = []
        for i in range(0, len(skills), 6):
            chunk = skills[i:i+6]
            rows.append(" &bull; ".join([esc(s) for s in chunk]))
        parts.append(f'<p class="skills-list">{"<br>".join(rows)}</p>')
    
    # Experience
    has_experience = (experience and len(experience) > 0) or experience_raw
    if has_experience:
        parts.append('<h2 class="section-header">PROFESSIONAL EXPERIENCE</h2>')
        
        if experience and isinstance(experience, list) and len(experience) > 0:
            for entry in experience:
                company = entry.get("company", "")
                role = entry.get("role", "")
                dates = entry.get("dates", "")
                location = entry.get("location", "")
                bullets = entry.get("bullets", [])
                raw = entry.get("raw", "")
                
                # Job header
                display_line = ""
                if company and role:
                    display_line = f"{company} &mdash; {role}"
                elif company:
                    display_line = company
                elif role:
                    display_line = role
                elif raw:
                    import re
                    clean_raw = re.sub(r'\d{4}.*', '', raw).strip()
                    display_line = esc(clean_raw[:80])
                
                if display_line:
                    loc_str = f" &nbsp;|&nbsp; {esc(location)}" if location else ""
                    parts.append(f'<p class="job-header"><strong>{display_line}{loc_str}</strong></p>')
                
                if dates:
                    parts.append(f'<p class="job-dates"><em>{esc(dates)}</em></p>')
                
                if bullets:
                    parts.append('<ul class="job-bullets">')
                    for bullet in bullets:
                        if bullet.strip():
                            parts.append(f'<li>{esc(bullet.strip())}</li>')
                    parts.append('</ul>')
                elif raw and not display_line:
                    parts.append(f'<p class="job-raw">{esc(raw)}</p>')
        
        elif experience_raw:
            # Render raw experience as structured HTML
            import re
            for line in experience_raw.split('\n'):
                line = line.strip()
                if not line:
                    continue
                is_bullet = line.startswith(('•', '-', '–', '●', '*'))
                if is_bullet:
                    clean = re.sub(r'^[•\-–●\*·▪]\s*', '', line)
                    parts.append(f'<ul class="job-bullets"><li>{esc(clean)}</li></ul>')
                elif re.search(r'\d{4}', line):
                    parts.append(f'<p class="job-dates"><em>{esc(line)}</em></p>')
                else:
                    parts.append(f'<p class="job-header"><strong>{esc(line)}</strong></p>')
    
    # Education
    if education:
        parts.append('<h2 class="section-header">EDUCATION</h2>')
        import re
        for line in education.split('\n'):
            line = line.strip()
            if line:
                is_degree = any(kw in line.lower() for kw in
                                ['bachelor', 'master', 'phd', 'b.s.', 'm.s.', 'degree', 'diploma'])
                if is_degree:
                    parts.append(f'<p class="edu-degree"><strong>{esc(line)}</strong></p>')
                else:
                    parts.append(f'<p class="edu-detail">{esc(line)}</p>')
    
    # Projects
    if projects:
        parts.append('<h2 class="section-header">KEY PROJECTS</h2>')
        import re
        for line in projects.split('\n'):
            line = line.strip()
            if not line:
                continue
            is_bullet = line.startswith(('•', '-', '–'))
            if is_bullet:
                clean = re.sub(r'^[•\-–●\*·▪]\s*', '', line)
                parts.append(f'<ul class="job-bullets"><li>{esc(clean)}</li></ul>')
            else:
                parts.append(f'<p class="job-header"><strong>{esc(line)}</strong></p>')
    
    # Certifications
    if certifications:
        parts.append('<h2 class="section-header">CERTIFICATIONS &amp; CREDENTIALS</h2>')
        import re
        for line in certifications.split('\n'):
            line = line.strip()
            if not line:
                continue
            is_bullet = line.startswith(('•', '-', '–'))
            if is_bullet:
                clean = re.sub(r'^[•\-–●\*·▪]\s*', '', line)
                parts.append(f'<ul class="job-bullets"><li>{esc(clean)}</li></ul>')
            else:
                parts.append(f'<p class="cert-item">{esc(line)}</p>')
    
    return '\n'.join(parts)


def generate_pdf(resume_data: dict) -> bytes:
    """Generate PDF using reportlab with professional formatting"""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
    from reportlab.platypus import ListFlowable, ListItem
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    
    buffer = io.BytesIO()
    
    # Page setup
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=1*inch,
        rightMargin=1*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    # Colors
    DARK_BLUE = colors.HexColor('#1A3A6B')
    NEAR_BLACK = colors.HexColor('#2C2C2C')
    DARK_GRAY = colors.HexColor('#333333')
    MED_GRAY = colors.HexColor('#555555')
    
    # Styles
    styles = getSampleStyleSheet()
    
    style_name = ParagraphStyle(
        'ResumeName',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=DARK_BLUE,
        alignment=TA_CENTER,
        spaceAfter=4
    )
    
    style_contact = ParagraphStyle(
        'Contact',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=MED_GRAY,
        alignment=TA_CENTER,
        spaceAfter=10
    )
    
    style_section_header = ParagraphStyle(
        'SectionHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        textColor=DARK_BLUE,
        spaceBefore=10,
        spaceAfter=3
    )
    
    style_body = ParagraphStyle(
        'ResumeBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=DARK_GRAY,
        alignment=TA_JUSTIFY,
        spaceAfter=4
    )
    
    style_job_header = ParagraphStyle(
        'JobHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        textColor=NEAR_BLACK,
        spaceBefore=8,
        spaceAfter=1
    )
    
    style_dates = ParagraphStyle(
        'Dates',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9.5,
        textColor=MED_GRAY,
        spaceAfter=2
    )
    
    style_bullet = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=DARK_GRAY,
        leftIndent=15,
        firstLineIndent=0,
        spaceAfter=2,
        bulletIndent=0
    )
    
    # Story builder
    story = []
    
    name = resume_data.get("name", "")
    contact = resume_data.get("contact", {})
    summary = resume_data.get("summary", "")
    skills = resume_data.get("skills", [])
    experience = resume_data.get("experience", [])
    experience_raw = resume_data.get("experience_raw", "")
    education = resume_data.get("education", "")
    projects = resume_data.get("projects", "")
    certifications = resume_data.get("certifications", "")
    
    def add_section_hr(story):
        story.append(HRFlowable(width="100%", thickness=1.5, color=DARK_BLUE, spaceAfter=4))
    
    # Name
    if name:
        story.append(Paragraph(name.upper(), style_name))
    
    # Contact
    contact_items = [contact.get(k, "") for k in ["email", "phone", "location", "linkedin", "github"]]
    contact_str = " | ".join([c for c in contact_items if c])
    if contact_str:
        story.append(Paragraph(contact_str, style_contact))
    
    # Summary
    if summary:
        story.append(Paragraph("PROFESSIONAL SUMMARY", style_section_header))
        add_section_hr(story)
        story.append(Paragraph(summary, style_body))
    
    # Skills
    if skills:
        story.append(Paragraph("CORE COMPETENCIES &amp; TECHNICAL SKILLS", style_section_header))
        add_section_hr(story)
        rows = []
        for i in range(0, len(skills), 6):
            chunk = skills[i:i+6]
            rows.append(" • ".join(chunk))
        story.append(Paragraph("<br/>".join(rows), style_body))
    
    # Experience
    has_experience = (experience and len(experience) > 0) or experience_raw
    if has_experience:
        story.append(Paragraph("PROFESSIONAL EXPERIENCE", style_section_header))
        add_section_hr(story)
        
        if experience and isinstance(experience, list):
            for entry in experience:
                company = entry.get("company", "")
                role = entry.get("role", "")
                dates = entry.get("dates", "")
                raw = entry.get("raw", "")
                bullets = entry.get("bullets", [])
                
                display = ""
                if company and role:
                    display = f"<b>{company} — {role}</b>"
                elif company:
                    display = f"<b>{company}</b>"
                elif role:
                    display = f"<b>{role}</b>"
                elif raw:
                    import re
                    clean_raw = re.sub(r'\d{4}.*', '', raw).strip()[:80]
                    display = f"<b>{clean_raw}</b>"
                
                if display:
                    story.append(Paragraph(display, style_job_header))
                if dates:
                    story.append(Paragraph(f"<i>{dates}</i>", style_dates))
                
                for bullet in bullets:
                    if bullet.strip():
                        story.append(Paragraph(f"• {bullet.strip()}", style_bullet))
        
        elif experience_raw:
            import re
            for line in experience_raw.split('\n'):
                line = line.strip()
                if not line:
                    continue
                if line.startswith(('•', '-', '–')):
                    clean = re.sub(r'^[•\-–●\*·▪]\s*', '', line)
                    story.append(Paragraph(f"• {clean}", style_bullet))
                elif re.search(r'\d{4}', line):
                    story.append(Paragraph(f"<i>{line}</i>", style_dates))
                else:
                    story.append(Paragraph(f"<b>{line}</b>", style_job_header))
    
    # Education
    if education:
        story.append(Paragraph("EDUCATION", style_section_header))
        add_section_hr(story)
        for line in education.split('\n'):
            line = line.strip()
            if line:
                is_degree = any(kw in line.lower() for kw in
                                ['bachelor', 'master', 'phd', 'b.s.', 'm.s.', 'degree'])
                if is_degree:
                    story.append(Paragraph(f"<b>{line}</b>", style_body))
                else:
                    story.append(Paragraph(line, style_body))
    
    # Projects
    if projects:
        story.append(Paragraph("KEY PROJECTS", style_section_header))
        add_section_hr(story)
        import re
        for line in projects.split('\n'):
            line = line.strip()
            if not line:
                continue
            if line.startswith(('•', '-', '–')):
                clean = re.sub(r'^[•\-–●\*·▪]\s*', '', line)
                story.append(Paragraph(f"• {clean}", style_bullet))
            else:
                story.append(Paragraph(f"<b>{line}</b>", style_job_header))
    
    # Certifications
    if certifications:
        story.append(Paragraph("CERTIFICATIONS &amp; CREDENTIALS", style_section_header))
        add_section_hr(story)
        import re
        for line in certifications.split('\n'):
            line = line.strip()
            if not line:
                continue
            if line.startswith(('•', '-', '–')):
                clean = re.sub(r'^[•\-–●\*·▪]\s*', '', line)
                story.append(Paragraph(f"• {clean}", style_bullet))
            else:
                story.append(Paragraph(line, style_body))
    
    doc.build(story)
    buffer.seek(0)
    return buffer.read()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
