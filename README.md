# ResumeAI Pro 🚀
### Smart Resume Optimizer — Personal Edition
**Zero API Keys. Zero Cost. Pure Algorithmic Intelligence.**

---

## ✨ What It Does

Upload your resume → Paste a Job Description → Click **Optimize** → Get a perfectly tailored, ATS-optimized resume.

- **No OpenAI, No Claude, No paid APIs**
- Runs 100% locally on your machine
- Processes in seconds, not minutes

---

## 🧠 The Intelligence Inside

### JD Analysis Engine
- **TF-IDF keyword extraction** — identifies high-value keywords
- **Skill taxonomy matching** — 600+ skills across 15 domains
- **Experience level detection** — junior / mid / senior / executive
- **Domain identification** — Software, Data, DevOps, Finance, etc.
- **Action verb extraction** — matches JD's expected language

### Resume Parser
- Parses `.docx` and `.pdf` files
- Auto-detects section headers (Summary, Skills, Experience, Education, etc.)
- Extracts contact info, years of experience, bullet points
- Works on most standard and modern resume formats

### Optimization Engine
- **Smart verb transformation**: "Responsible for building" → "Built"
  - 15+ transformation patterns with grammatical correctness
- **Keyword insertion**: Inserts JD keywords where contextually appropriate
  - DB keywords only in database bullets
  - Cloud keywords only in deployment bullets
  - Frontend keywords only in UI bullets
- **Summary rewriting**: Domain-specific templates + dynamic keyword insertion
- **Skills augmentation**: Adds missing JD skills from same domain you work in (truthful only)

### ATS Scoring
- Technical skills match (40 pts)
- Keyword coverage (30 pts)
- Soft skills (15 pts)
- Format compliance (15 pts)
- Grade: A / B / C / D with before/after comparison

---

## 📦 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Vite + Tailwind CSS |
| Editor | TipTap (Word-style rich text editor) |
| Backend | FastAPI (Python) |
| NLP | Custom algorithms + NLTK (local, free) |
| Resume Parser | python-docx + pdfplumber + PyPDF2 |
| DOCX Export | python-docx (professionally formatted) |
| PDF Export | ReportLab (pixel-perfect layout) |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+

### Installation & Launch

```bash
# 1. Run setup (once)
chmod +x setup.sh start.sh stop.sh
./setup.sh

# 2. Start everything
./start.sh

# 3. Open browser
open http://localhost:3000
```

### Stopping
```bash
./stop.sh
```

---

## 📋 How to Use

1. **Paste Job Description** — Full JD in the left panel text area
2. **Upload Resume** — Drag & drop or click (.docx or .pdf)
3. **Click Optimize** — Watch the ATS score jump
4. **Review & Edit** — Full Word-style editor on the right
   - Bold, italic, underline
   - Align, bullet lists
   - Full undo/redo
5. **Download** — .DOCX (Microsoft Word) or .PDF

---

## 📁 Project Structure

```
resume-optimizer/
├── backend/
│   ├── main.py              # FastAPI server + all endpoints
│   ├── jd_analyzer.py       # JD analysis engine (TF-IDF + skill taxonomy)
│   ├── resume_parser.py     # DOCX/PDF parser + section detector
│   ├── optimizer.py         # Core optimization engine (smart NLP)
│   ├── docx_generator.py    # Professional DOCX formatter
│   ├── skills_db.py         # 600+ skills taxonomy database
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.jsx           # Main application (split-panel UI)
│       └── index.css         # Word-style resume rendering CSS
├── setup.sh                  # One-time setup
├── start.sh                  # Start both servers
└── stop.sh                   # Stop servers
```

---

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/parse-resume` | POST | Upload & parse resume file |
| `/analyze-jd` | POST | Analyze job description |
| `/optimize` | POST | Run full optimization |
| `/download-docx` | POST | Generate & download .docx |
| `/download-pdf` | POST | Generate & download .pdf |

---

## 💡 Tips for Best Results

1. **Paste the COMPLETE JD** — Don't truncate. More context = better optimization
2. **Use a structured resume** — Clear section headers help the parser
3. **DOCX format preferred** — Better parsing than PDF for complex layouts
4. **Review before sending** — Check all bullets make sense in context
5. **Re-optimize with different JDs** — Takes seconds, helps you apply to multiple roles

---

## 📊 ATS Score Interpretation

| Score | Grade | Meaning |
|-------|-------|---------|
| 85-100 | A | Excellent - strong ATS match |
| 70-84 | B | Good - minor improvements possible |
| 55-69 | C | Fair - needs more keyword alignment |
| < 55 | D | Poor - major optimization needed |

---

*Built with pure algorithmic intelligence — no API keys, no subscriptions, no data sent anywhere.*
