"""
JD Analyzer - Deep analysis of job descriptions
Uses TF-IDF, skill taxonomy matching, and NLP patterns
No external AI APIs - pure algorithmic intelligence
"""

import re
import math
from collections import Counter
from skills_db import SKILLS_DB, ALL_SKILLS, STRONG_VERBS, ATS_PHRASES

# ─── Stopwords ─────────────────────────────────────────────────────────────
STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "must", "shall", "can",
    "our", "your", "their", "its", "we", "you", "they", "he", "she", "it",
    "this", "that", "these", "those", "i", "me", "my", "us", "him", "her",
    "who", "what", "which", "when", "where", "how", "why", "all", "any",
    "both", "each", "few", "more", "most", "other", "some", "such", "no",
    "not", "only", "own", "same", "than", "too", "very", "just", "about",
    "above", "after", "against", "also", "between", "during", "into",
    "through", "while", "within", "without", "including", "across"
}

# ─── Experience Level Detection ─────────────────────────────────────────────
EXPERIENCE_LEVELS = {
    "entry": ["entry level", "entry-level", "junior", "0-1 year", "0-2 year",
              "fresh graduate", "recent graduate", "new grad", "trainee", "intern"],
    "mid": ["mid level", "mid-level", "2-4 year", "2-5 year", "3-5 year",
             "associate", "intermediate"],
    "senior": ["senior", "sr.", "lead", "5+ year", "5-7 year", "7+ year",
                "principal", "staff", "expert", "advanced"],
    "executive": ["director", "vp", "vice president", "cto", "ceo", "head of",
                   "chief", "executive", "c-level", "manager"]
}


def clean_text(text: str) -> str:
    """Clean and normalize text"""
    text = text.lower()
    text = re.sub(r'[^\w\s\-\+\#\.]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def tokenize(text: str) -> list:
    """Tokenize text, preserve multi-word skills"""
    words = text.lower().split()
    return [w.strip('.,;:()[]{}') for w in words if w.strip('.,;:()[]{}')]


def extract_ngrams(tokens: list, n: int) -> list:
    """Extract n-grams from tokens"""
    return [' '.join(tokens[i:i+n]) for i in range(len(tokens)-n+1)]


def compute_tfidf(text: str, corpus_size: int = 100) -> dict:
    """Compute TF-IDF scores for words in text"""
    tokens = tokenize(clean_text(text))
    filtered = [t for t in tokens if t not in STOPWORDS and len(t) > 2]
    
    # Term frequency
    tf = Counter(filtered)
    total = len(filtered)
    
    scores = {}
    for word, count in tf.items():
        # TF * IDF (approximate IDF based on common word lists)
        tf_score = count / max(total, 1)
        # Higher IDF for less common words (technical terms)
        idf = math.log(corpus_size / (1 + tf.get(word, 0)))
        scores[word] = tf_score * idf
    
    return scores


def extract_skills_from_text(text: str) -> dict:
    """
    Extract skills from text by matching against skill taxonomy
    Returns skills organized by category
    """
    text_lower = text.lower()
    found_skills = {}
    
    for category, skills in SKILLS_DB.items():
        matched = []
        for skill in skills:
            # Match whole word/phrase
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, text_lower):
                matched.append(skill)
        if matched:
            found_skills[category] = matched
    
    return found_skills


def extract_experience_level(text: str) -> str:
    """Detect required experience level from JD"""
    text_lower = text.lower()
    
    # Check for year ranges first
    year_patterns = [
        (r'(\d+)\+?\s*(?:to|-)\s*(\d+)\s*years?', 'range'),
        (r'(\d+)\+\s*years?', 'plus'),
        (r'minimum\s+(\d+)\s+years?', 'min'),
        (r'at\s+least\s+(\d+)\s+years?', 'atleast'),
    ]
    
    for pattern, ptype in year_patterns:
        m = re.search(pattern, text_lower)
        if m:
            if ptype == 'range':
                years = int(m.group(2))
            elif ptype in ['plus', 'min', 'atleast']:
                years = int(m.group(1))
            else:
                years = int(m.group(1))
            
            if years <= 2:
                return "junior"
            elif years <= 5:
                return "mid-level"
            elif years <= 8:
                return "senior"
            else:
                return "staff/principal"
    
    # Check keyword-based level
    for level, keywords in EXPERIENCE_LEVELS.items():
        for kw in keywords:
            if kw in text_lower:
                level_map = {
                    "entry": "junior",
                    "mid": "mid-level", 
                    "senior": "senior",
                    "executive": "executive/director"
                }
                return level_map.get(level, "mid-level")
    
    return "mid-level"  # Default


def extract_action_verbs(text: str) -> list:
    """Extract action verbs from JD (responsibilities section)"""
    all_verbs = []
    for verbs in STRONG_VERBS.values():
        all_verbs.extend([v.lower() for v in verbs])
    
    # Additional common JD verbs
    jd_verbs = [
        "design", "develop", "build", "create", "implement", "deploy",
        "manage", "lead", "collaborate", "analyze", "optimize", "maintain",
        "architect", "establish", "drive", "deliver", "scale", "improve",
        "integrate", "automate", "monitor", "troubleshoot", "review"
    ]
    all_verbs.extend(jd_verbs)
    
    text_lower = text.lower()
    found = []
    for verb in set(all_verbs):
        if re.search(r'\b' + verb + r'\b', text_lower):
            found.append(verb.capitalize())
    
    return list(set(found))[:20]


def extract_top_keywords(text: str, top_n: int = 20) -> list:
    """Extract top keywords using TF-IDF, excluding skills (handled separately)"""
    scores = compute_tfidf(text)
    
    # Filter out stopwords and very short words
    filtered = {
        word: score for word, score in scores.items()
        if word not in STOPWORDS and len(word) > 3
    }
    
    # Sort by score
    sorted_kw = sorted(filtered.items(), key=lambda x: x[1], reverse=True)
    return [kw for kw, _ in sorted_kw[:top_n]]


def extract_soft_skills(text: str) -> list:
    """Extract soft skills from JD"""
    soft_skills = SKILLS_DB.get("soft_skills", [])
    text_lower = text.lower()
    found = []
    for skill in soft_skills:
        if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
            found.append(skill)
    return found


def detect_industry_domain(text: str, skills: dict) -> str:
    """Detect the primary industry/domain"""
    text_lower = text.lower()
    
    domain_keywords = {
        "Software Engineering": ["software engineer", "software developer", "backend", "frontend", 
                                   "full stack", "fullstack", "web developer", "api", "microservices"],
        "Data Science/ML": ["data scientist", "machine learning", "deep learning", "ml engineer",
                              "ai engineer", "data engineer", "analytics"],
        "DevOps/Cloud": ["devops", "cloud", "infrastructure", "kubernetes", "ci/cd", 
                           "site reliability", "sre", "platform engineer"],
        "Product Management": ["product manager", "product owner", "roadmap", "go-to-market",
                                  "stakeholder", "product strategy"],
        "Cybersecurity": ["security", "cybersecurity", "penetration", "compliance", "soc", "siem"],
        "Finance/Fintech": ["financial", "banking", "fintech", "trading", "risk", "compliance"],
        "Design/UX": ["ux", "ui", "design", "figma", "user research", "product design"],
        "Marketing": ["marketing", "seo", "growth", "campaigns", "analytics", "brand"],
        "Data Engineering": ["data pipeline", "etl", "data warehouse", "spark", "airflow", "kafka"],
    }
    
    scores = Counter()
    for domain, keywords in domain_keywords.items():
        for kw in keywords:
            if kw in text_lower:
                scores[domain] += 1
    
    if scores:
        return scores.most_common(1)[0][0]
    return "Technology"


def extract_requirements_sections(text: str) -> dict:
    """Split JD into logical sections"""
    sections = {
        "responsibilities": "",
        "requirements": "",
        "nice_to_have": "",
        "about_company": ""
    }
    
    # Section detection patterns
    resp_patterns = [
        r'(?:responsibilities|what you.ll do|role responsibilities|key responsibilities|'
        r'duties|your role|job duties|what we.re looking for you to do)(.*?)(?=\n[A-Z]|\Z)',
    ]
    
    req_patterns = [
        r'(?:requirements|qualifications|what you.ll need|what we need|'
        r'skills required|required skills|minimum qualifications|you have)(.*?)(?=\n[A-Z]|\Z)',
    ]
    
    nice_patterns = [
        r'(?:nice to have|preferred|bonus|plus|desired|would be great)(.*?)(?=\n[A-Z]|\Z)',
    ]
    
    text_lower = text.lower()
    
    for pattern in resp_patterns:
        m = re.search(pattern, text_lower, re.DOTALL | re.IGNORECASE)
        if m:
            sections["responsibilities"] = m.group(1).strip()[:2000]
            break
    
    for pattern in req_patterns:
        m = re.search(pattern, text_lower, re.DOTALL | re.IGNORECASE)
        if m:
            sections["requirements"] = m.group(1).strip()[:2000]
            break
    
    return sections


def analyze_jd(jd_text: str) -> dict:
    """
    Main JD analysis function
    Returns comprehensive analysis for use by optimizer
    """
    if not jd_text or len(jd_text.strip()) < 50:
        return {}
    
    # Extract all components
    skills = extract_skills_from_text(jd_text)
    experience_level = extract_experience_level(jd_text)
    action_verbs = extract_action_verbs(jd_text)
    keywords = extract_top_keywords(jd_text, top_n=25)
    soft_skills = extract_soft_skills(jd_text)
    domain = detect_industry_domain(jd_text, skills)
    sections = extract_requirements_sections(jd_text)
    
    # Flatten all technical skills
    all_tech_skills = []
    for cat, skill_list in skills.items():
        if cat != "soft_skills":
            all_tech_skills.extend(skill_list)
    
    # Get primary job title
    title_patterns = [
        r'(?:we.re looking for|hiring a|seeking a|position:?|role:?|job title:?)\s*([^\n,\.]+)',
        r'^([A-Z][a-zA-Z\s]+(?:engineer|developer|manager|analyst|designer|scientist|architect))',
    ]
    job_title = ""
    for pattern in title_patterns:
        m = re.search(pattern, jd_text, re.IGNORECASE | re.MULTILINE)
        if m:
            job_title = m.group(1).strip()[:60]
            break
    
    if not job_title:
        # Extract from first line
        first_line = jd_text.strip().split('\n')[0]
        if len(first_line) < 80:
            job_title = first_line.strip()
    
    return {
        "job_title": job_title,
        "domain": domain,
        "experience_level": experience_level,
        "technical_skills": list(set(all_tech_skills))[:30],
        "soft_skills": soft_skills[:10],
        "keywords": keywords,
        "action_verbs": action_verbs,
        "skills_by_category": skills,
        "sections": sections,
        "raw_text": jd_text
    }
