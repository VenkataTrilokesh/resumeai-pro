"""
Core Resume Optimizer Engine
Smart algorithmic optimization - NO external AI APIs
Uses NLP patterns, skill taxonomy, verb libraries, and template intelligence
"""

import re
import random
from typing import Dict, List, Optional
from skills_db import (
    VERB_UPGRADES, STRONG_VERBS, WEAK_VERBS,
    ATS_PHRASES, ALL_SKILLS, SKILLS_DB
)

# ─── ING → Past tense conversions for verb-phrase extraction ────────────────
ING_TO_PAST = {
    "building": "Built", "developing": "Developed", "designing": "Designed",
    "implementing": "Implemented", "creating": "Created", "leading": "Led",
    "managing": "Managed", "delivering": "Delivered", "architecting": "Architected",
    "optimizing": "Optimized", "maintaining": "Maintained", "deploying": "Deployed",
    "analyzing": "Analyzed", "improving": "Improved", "establishing": "Established",
    "driving": "Drove", "collaborating": "Collaborated", "coordinating": "Coordinated",
    "mentoring": "Mentored", "reviewing": "Reviewed", "monitoring": "Monitored",
    "automating": "Automated", "integrating": "Integrated", "migrating": "Migrated",
    "launching": "Launched", "scaling": "Scaled", "supporting": "Supported",
    "writing": "Wrote", "testing": "Tested", "debugging": "Debugged",
    "configuring": "Configured", "setting": "Set up", "working": "Worked on",
    "ensuring": "Ensured", "overseeing": "Oversaw", "handling": "Handled",
}

# Smart weak-phrase → strong transformations (ORDER MATTERS: specific first)
SMART_TRANSFORMS = [
    # "Was responsible for VERB-ING X" → "PAST-VERB X"
    (r'^was\s+responsible\s+for\s+(\w+ing)\s+(.+)',
     lambda m: f"{ING_TO_PAST.get(m.group(1).lower(), 'Managed')} {m.group(2)}"),
    
    # "Was responsible for X" (noun phrase)
    (r'^was\s+responsible\s+for\s+(.+)',
     lambda m: f"Managed {m.group(1)}"),
    
    # "Responsible for building/developing X" → "Built/Developed X"
    (r'^responsible\s+for\s+(building|developing|creating|designing|implementing|maintaining|managing|leading)\s+(.+)',
     lambda m: f"{ING_TO_PAST.get(m.group(1).lower(), 'Developed')} {m.group(2)}"),
    
    # "Responsible for X" (noun phrase)
    (r'^responsible\s+for\s+(.+)',
     lambda m: f"Managed {m.group(1)}"),
    
    # "Worked on developing/building X" → "Developed/Built X"
    (r'^worked\s+on\s+(developing|building|creating|designing|implementing)\s+(.+)',
     lambda m: f"{ING_TO_PAST.get(m.group(1).lower(), 'Developed')} {m.group(2)}"),
    
    # "Worked on X development/testing" → remove redundant noun
    (r'^worked\s+on\s+(.+?)\s+(development|implementation|testing)(.*)$',
     lambda m: f"Developed {m.group(1)}{m.group(3)}"),
    
    # "Worked on X" general
    (r'^worked\s+on\s+(.+)',
     lambda m: f"Developed {m.group(1)}"),
    
    # "Was involved in X" → "Contributed to X"
    (r'^was\s+involved\s+in\s+(.+)',
     lambda m: f"Contributed to {m.group(1)}"),
    
    # "Was part of X" → "Served as integral member of X"
    (r'^was\s+part\s+of\s+(.+)',
     lambda m: f"Served as integral member of {m.group(1)}"),
    
    # "Was X" (generic)
    (r'^was\s+(.+)',
     lambda m: f"Operated as {m.group(1)}"),
    
    # "Helped with X" → "Enhanced X"
    (r'^helped\s+with\s+(.+)',
     lambda m: f"Enhanced {m.group(1)}"),
    
    # "Helped to X" → "Supported X"
    (r'^helped\s+to\s+(.+)',
     lambda m: f"Supported {m.group(1)}"),
    
    # "Assisted in X" → "Collaborated on X"
    (r'^assisted\s+in\s+(.+)',
     lambda m: f"Collaborated on {m.group(1)}"),
    
    # "Did X" → "Executed X"
    (r'^did\s+(.+)',
     lambda m: f"Executed {m.group(1)}"),
    
    # "Participated in X" → "Actively contributed to X"
    (r'^participated\s+in\s+(.+)',
     lambda m: f"Actively contributed to {m.group(1)}"),
    
    # "Made X APIs/services/systems" → "Engineered X"
    (r'^made\s+(.+?)\s+(api|apis|service|services|system|systems|pipeline)(.*)$',
     lambda m: f"Engineered {m.group(1)} {m.group(2)}{m.group(3)}"),
    
    # "Made X" general → "Developed X"
    (r'^made\s+(.+)',
     lambda m: f"Developed {m.group(1)}"),
    
    # "Used X for Y" → "Leveraged X for Y"
    (r'^used\s+(.+?)\s+for\s+(.+)',
     lambda m: f"Leveraged {m.group(1)} for {m.group(2)}"),
    
    # "Used X" → "Utilized X"
    (r'^used\s+(.+)',
     lambda m: f"Utilized {m.group(1)}"),
    
    # "Tried to X" → "Successfully X-ed"
    (r'^tried\s+to\s+(.+)',
     lambda m: f"Successfully {m.group(1)}"),
]


def smart_preserve_case(remainder: str) -> str:
    """
    When extracting remainder of sentence, preserve internal capitalizations
    but handle first character intelligently.
    """
    if not remainder:
        return remainder
    
    words = remainder.split()
    if not words:
        return remainder
    
    first_word = words[0]
    
    # If first word is an acronym (all caps, 2-5 chars) → keep it
    if first_word.isupper() and 1 < len(first_word) <= 6:
        return remainder
    
    # If it's a proper noun starting with capital → keep it
    # (Heuristic: contains only letters, starts with capital, not a stop word)
    stopwords = {'the', 'a', 'an', 'this', 'that', 'these', 'those', 'all',
                 'their', 'our', 'its', 'my', 'your', 'his', 'her'}
    if (first_word[0].isupper() and 
        first_word.lower() not in stopwords and
        len(first_word) > 3 and
        first_word[1:].lower() == first_word[1:]):  # only first char is capital
        # Could be a proper noun - check if it's a tech term
        tech_terms = {'PostgreSQL', 'JavaScript', 'TypeScript', 'GitHub', 'MySQL',
                      'MongoDB', 'Redis', 'Docker', 'Kubernetes', 'React', 'Angular',
                      'Python', 'FastAPI', 'Django', 'Flask', 'AWS', 'Azure', 'GCP'}
        if first_word in tech_terms:
            return remainder
    
    # Default: lowercase first char
    return first_word[0].lower() + remainder[1:]


def apply_smart_transform(sentence: str) -> Optional[str]:
    """Try all smart transformations, return the best match"""
    sentence_stripped = sentence.strip()
    sentence_lower = sentence_stripped.lower()
    
    for pattern, replacer in SMART_TRANSFORMS:
        m = re.match(pattern, sentence_lower, re.IGNORECASE)
        if m:
            try:
                result = replacer(m)
                if result:
                    # Now we need to restore original casing for the matched groups
                    # Re-apply from original sentence
                    original_m = re.match(pattern, sentence_stripped, re.IGNORECASE)
                    if original_m:
                        # Rebuild with original group content
                        orig_result = replacer(original_m)
                        if orig_result:
                            # Capitalize first char
                            return orig_result[0].upper() + orig_result[1:]
                    return result[0].upper() + result[1:]
            except Exception:
                continue
    
    return None


def replace_weak_verb(sentence: str) -> str:
    """Replace weak opening verbs with strong action verbs - preserves inner capitalization"""
    sentence = sentence.strip()
    if not sentence:
        return sentence
    
    # Remove leading bullet characters
    clean = re.sub(r'^[•\-–●\*·▪\s]+', '', sentence).strip()
    
    if not clean:
        return sentence
    
    # Try smart transformations first (most accurate)
    smart = apply_smart_transform(clean)
    if smart:
        return smart
    
    # Fallback: simple first-word replacement
    words = clean.split()
    if not words:
        return sentence
    
    first_word_lower = words[0].lower()
    
    for weak in WEAK_VERBS:
        # Exact match or very close match (handles worked/working/works)
        if (first_word_lower == weak or 
            (len(first_word_lower) > 4 and first_word_lower.startswith(weak[:4]) and weak not in ('the', 'was', 'has'))):
            
            context_lower = clean.lower()
            
            if any(w in context_lower for w in ['team', 'cross', 'group', 'stakeholder', 'collaborate']):
                new_verb = random.choice(STRONG_VERBS["collaboration"])
            elif any(w in context_lower for w in ['build', 'develop', 'creat', 'code', 'implement', 
                                                    'deploy', 'architect', 'api', 'service', 'system']):
                new_verb = random.choice(STRONG_VERBS["development"])
            elif any(w in context_lower for w in ['increas', 'grow', 'generat', 'revenue', 'sale', 'boost']):
                new_verb = random.choice(STRONG_VERBS["growth"])
            elif any(w in context_lower for w in ['reduc', 'decreas', 'cut', 'lower', 'minim', 'remov']):
                new_verb = random.choice(STRONG_VERBS["reduction"])
            elif any(w in context_lower for w in ['analyz', 'resear', 'assess', 'evaluat', 'investigat', 'diagnos']):
                new_verb = random.choice(STRONG_VERBS["analysis"])
            elif any(w in context_lower for w in ['lead', 'manag', 'direct', 'mentor', 'supervis', 'overse']):
                new_verb = random.choice(STRONG_VERBS["leadership"])
            elif any(w in context_lower for w in ['automat', 'integrat', 'migrat', 'digit', 'transform']):
                new_verb = random.choice(STRONG_VERBS["automation"])
            elif any(w in context_lower for w in ['optimiz', 'improv', 'enhanc', 'streamlin', 'acceler']):
                new_verb = random.choice(STRONG_VERBS["improvement"])
            else:
                new_verb = random.choice(STRONG_VERBS["development"])
            
            # Keep remaining words WITH their original capitalization
            rest = ' '.join(words[1:])
            if rest:
                return f"{new_verb} {rest}"
            break
    
    return sentence


def is_contextually_relevant(keyword: str, bullet: str) -> bool:
    """
    Check if inserting this keyword makes semantic sense in this bullet.
    Strong relevance checks to avoid nonsensical insertions.
    """
    kw_lower = keyword.lower()
    bullet_lower = bullet.lower()
    
    # Already present
    if kw_lower in bullet_lower:
        return False
    
    # Determine bullet's technology domain
    bullet_is_frontend = any(t in bullet_lower for t in 
                              ['frontend', 'front-end', 'ui', 'react', 'angular', 'vue', 'css', 'html', 'browser'])
    bullet_is_backend = any(t in bullet_lower for t in
                             ['api', 'backend', 'back-end', 'server', 'endpoint', 'microservice',
                              'python', 'node', 'flask', 'django', 'fastapi', 'express', 'spring'])
    bullet_is_data = any(t in bullet_lower for t in
                          ['database', 'data', 'query', 'sql', 'schema', 'table', 'index',
                           'postgresql', 'mysql', 'mongodb', 'redis', 'cache', 'store'])
    bullet_is_devops = any(t in bullet_lower for t in
                            ['deploy', 'pipeline', 'ci', 'cd', 'docker', 'kubernetes', 'container',
                             'infrastructure', 'cloud', 'aws', 'azure', 'gcp', 'server', 'host',
                             'terraform', 'helm', 'jenkins', 'github actions'])
    bullet_is_tech = any(t in bullet_lower for t in
                          ['develop', 'built', 'implemented', 'created', 'designed', 'engineered',
                           'architected', 'leveraged', 'utilized', 'configured', 'integrated'])
    
    # Cloud/infra keywords → ONLY in devops/infrastructure bullets
    infra_kws = ['aws', 'azure', 'gcp', 'ec2', 's3', 'lambda', 'kubernetes', 'k8s',
                 'terraform', 'helm', 'nginx', 'ansible', 'fargate', 'ecs', 'eks']
    if kw_lower in infra_kws:
        return bullet_is_devops
    
    # CI/CD keywords → pipeline/deployment bullets
    if kw_lower in ['ci/cd', 'github actions', 'jenkins', 'gitlab ci', 'circleci']:
        return bullet_is_devops or 'pipeline' in bullet_lower or 'automat' in bullet_lower
    
    # Database keywords → data bullets only
    db_kws = ['postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'sqlite', 
               'oracle', 'cassandra', 'dynamodb', 'influxdb', 'mariadb', 'couchdb']
    if kw_lower in db_kws:
        return bullet_is_data
    
    # Frontend frameworks → frontend bullets
    frontend_kws = ['react', 'angular', 'vue', 'svelte', 'next.js', 'nuxt.js',
                     'tailwind', 'bootstrap', 'css', 'html', 'typescript']
    if kw_lower in frontend_kws:
        return bullet_is_frontend or (bullet_is_tech and not bullet_is_data and not bullet_is_devops)
    
    # Backend frameworks → backend bullets
    backend_kws = ['fastapi', 'django', 'flask', 'spring', 'express', 'nestjs', 'gin',
                    'graphql', 'grpc', 'rest']
    if kw_lower in backend_kws:
        return bullet_is_backend or (bullet_is_tech and not bullet_is_data and not bullet_is_devops)
    
    # Language keywords → only if same language family in bullet
    lang_kws = {'python': ['python', 'flask', 'django', 'fastapi'],
                 'javascript': ['javascript', 'node', 'react', 'express', 'js'],
                 'typescript': ['typescript', 'react', 'angular', 'nestjs', 'ts'],
                 'java': ['java', 'spring', 'maven', 'gradle'],
                 'go': ['golang', 'go ', 'gin', 'fiber']}
    for lang, lang_triggers in lang_kws.items():
        if kw_lower == lang:
            return any(t in bullet_lower for t in lang_triggers)
    
    # Generic tech insertions - only in clearly technical bullets
    return bullet_is_tech and len(keyword) > 3


def insert_keyword_naturally(bullet: str, keyword: str) -> str:
    """Insert a JD keyword naturally into a bullet point - only if semantically appropriate"""
    # Don't insert if keyword already present
    if keyword.lower() in bullet.lower():
        return bullet
    
    # Check semantic relevance first
    if not is_contextually_relevant(keyword, bullet):
        return bullet
    
    bullet_lower = bullet.lower()
    
    # Pattern: technical action verbs → add "using {keyword}"
    if any(w in bullet_lower for w in ['developed', 'built', 'implemented', 'created', 
                                         'designed', 'engineered', 'architected']):
        if not re.search(r'\b' + re.escape(keyword.lower()), bullet_lower):
            if bullet.rstrip().endswith('.'):
                return bullet[:-1] + f", leveraging {keyword}."
            return f"{bullet}, leveraging {keyword}"
    
    # Pattern: optimized/improved → add "leveraging {keyword}"
    if any(w in bullet_lower for w in ['optimized', 'improved', 'enhanced', 'streamlined']):
        if bullet.rstrip().endswith('.'):
            return bullet[:-1] + f" with {keyword}."
        return f"{bullet} with {keyword}"
    
    # Pattern: deployed/configured → add "on {keyword}" for cloud or "using {keyword}" for tools
    if any(w in bullet_lower for w in ['deployed', 'configured', 'containerized', 'migrated']):
        prep = "on" if keyword.lower() in ['aws', 'azure', 'gcp', 'eks', 'gke'] else "using"
        if bullet.rstrip().endswith('.'):
            return bullet[:-1] + f" {prep} {keyword}."
        return f"{bullet} {prep} {keyword}"
    
    return bullet


def calculate_ats_score(resume_data: dict, jd_analysis: dict) -> dict:
    """
    Calculate ATS compatibility score (0-100)
    Returns score + breakdown
    """
    score = 0
    breakdown = {}
    
    resume_text = resume_data.get("full_text", "").lower()
    jd_tech_skills = [s.lower() for s in jd_analysis.get("technical_skills", [])]
    jd_soft_skills = [s.lower() for s in jd_analysis.get("soft_skills", [])]
    jd_keywords = [k.lower() for k in jd_analysis.get("keywords", [])]
    
    # 1. Technical Skills Match (40 points max)
    if jd_tech_skills:
        matched_tech = [s for s in jd_tech_skills if s in resume_text]
        tech_ratio = len(matched_tech) / len(jd_tech_skills)
        tech_score = int(tech_ratio * 40)
        score += tech_score
        breakdown["technical_skills"] = {
            "score": tech_score,
            "max": 40,
            "matched": matched_tech,
            "missing": [s for s in jd_tech_skills if s not in resume_text]
        }
    
    # 2. Keyword Coverage (30 points max)
    if jd_keywords:
        matched_kw = [k for k in jd_keywords if k in resume_text]
        kw_ratio = len(matched_kw) / len(jd_keywords)
        kw_score = int(kw_ratio * 30)
        score += kw_score
        breakdown["keywords"] = {
            "score": kw_score,
            "max": 30,
            "matched": matched_kw[:10],
            "missing": [k for k in jd_keywords if k not in resume_text][:10]
        }
    
    # 3. Soft Skills (15 points max)
    if jd_soft_skills:
        matched_soft = [s for s in jd_soft_skills if s in resume_text]
        soft_ratio = len(matched_soft) / len(jd_soft_skills)
        soft_score = int(soft_ratio * 15)
        score += soft_score
        breakdown["soft_skills"] = {
            "score": soft_score,
            "max": 15,
            "matched": matched_soft
        }
    
    # 4. Format compliance (15 points max)
    format_score = 0
    has_sections = sum(1 for s in ["experience", "education", "skills", "summary"]
                       if s in resume_data.get("raw_sections", {}))
    format_score += min(has_sections * 3, 12)
    
    if resume_data.get("contact", {}).get("email"):
        format_score += 3
    
    score += format_score
    breakdown["format"] = {"score": format_score, "max": 15}
    
    # Add baseline
    score = max(score, 15)
    
    return {
        "total": min(score, 100),
        "breakdown": breakdown,
        "grade": "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 55 else "D"
    }


def rewrite_summary(resume_data: dict, jd_analysis: dict) -> str:
    """
    Intelligently rewrite the professional summary
    Uses template system with dynamic keyword insertion
    """
    years_exp = resume_data.get("years_experience", 3)
    
    job_title = jd_analysis.get("job_title", "professional")
    domain = jd_analysis.get("domain", "Technology")
    experience_level = jd_analysis.get("experience_level", "mid-level")
    tech_skills = jd_analysis.get("technical_skills", [])
    soft_skills = jd_analysis.get("soft_skills", [])
    keywords = jd_analysis.get("keywords", [])
    
    # Get resume's existing skills
    resume_text = resume_data.get("full_text", "").lower()
    resume_skills_list = resume_data.get("skills", [])
    
    # Find skills in BOTH resume and JD (truthful intersection)
    resume_skills_lower = [s.lower() for s in resume_skills_list]
    matching_tech_skills = [
        s for s in tech_skills
        if s.lower() in resume_text or s.lower() in ' '.join(resume_skills_lower)
    ][:5]
    
    if not matching_tech_skills:
        matching_tech_skills = tech_skills[:3] if tech_skills else []
    
    # Skills string - use proper case
    matching_display = []
    for ts in matching_tech_skills:
        # Try to find original case version from resume skills
        found_original = next(
            (s for s in resume_skills_list if s.lower() == ts.lower()),
            None
        )
        if not found_original:
            # Use proper capitalization
            if ts.lower() in ['python', 'react', 'docker', 'kubernetes', 'ansible']:
                found_original = ts.capitalize()
            elif ts.lower() in ['aws', 'api', 'sql', 'html', 'css', 'git', 'ci/cd', 'gcp']:
                found_original = ts.upper()
            elif ts.lower() in ['javascript', 'typescript']:
                found_original = ts.capitalize()
            else:
                found_original = ts.title() if len(ts) > 4 else ts.upper()
        matching_display.append(found_original)
    
    if len(matching_display) >= 2:
        skills_str = ', '.join(matching_display[:-1]) + f", and {matching_display[-1]}"
    elif len(matching_display) == 1:
        skills_str = matching_display[0]
    else:
        skills_str = domain
    
    # Experience level phrase
    exp_phrase_map = {
        "junior": f"with {max(years_exp, 1)}+ year{'s' if years_exp != 1 else ''} of hands-on experience",
        "mid-level": f"with {max(years_exp, 2)}+ years of professional experience",
        "senior": f"with {max(years_exp, 4)}+ years of deep technical expertise",
        "staff/principal": f"with {max(years_exp, 6)}+ years of industry-leading expertise",
        "executive/director": f"with {max(years_exp, 8)}+ years of strategic leadership experience"
    }
    exp_phrase = exp_phrase_map.get(
        experience_level, 
        f"with {max(years_exp, 2)}+ years of professional experience"
    )
    
    # Extract best achievement from experience bullets (one with numbers)
    best_achievement = ""
    for entry in resume_data.get("experience", []):
        bullets = entry.get("bullets", [])
        for bullet in bullets:
            if re.search(r'\d+%|\$[\d,]+|\d+x|\b\d{2,}\b', bullet, re.IGNORECASE):
                best_achievement = bullet[:120]
                break
        if best_achievement:
            break
    
    # Get soft skill
    selected_soft = soft_skills[0].capitalize() if soft_skills else "Results-driven"
    
    # Domain-specific summary templates
    domain_templates = {
        "Software Engineering": [
            "{soft} software engineer {exp} specializing in {skills}. "
            "Proven track record of designing and delivering scalable, high-performance systems "
            "that align with business objectives. Expertise in full-stack development, "
            "cross-functional collaboration, and engineering best practices.",
            
            "Accomplished {domain} professional {exp} in {skills}. "
            "Demonstrated ability to architect and implement robust solutions across the SDLC, "
            "from requirements gathering to production deployment. "
            "Recognized for clean code practices, proactive problem-solving, "
            "and delivering measurable impact in agile environments.",
        ],
        "Data Science/ML": [
            "{soft} data professional {exp} specializing in {skills}. "
            "Proven ability to transform complex datasets into actionable insights "
            "and production-ready machine learning models. "
            "Experienced in building data pipelines, statistical modeling, and A/B testing.",
        ],
        "DevOps/Cloud": [
            "{soft} DevOps/Cloud engineer {exp} with expertise in {skills}. "
            "Proven record of building and maintaining reliable, scalable infrastructure "
            "using infrastructure-as-code and CI/CD best practices. "
            "Committed to improving deployment velocity and system observability.",
        ],
    }
    
    templates = domain_templates.get(domain, domain_templates["Software Engineering"])
    template = random.choice(templates)
    
    summary = template.format(
        soft=selected_soft,
        domain=domain,
        exp=exp_phrase,
        skills=skills_str
    )
    
    # If we have a quantified achievement, append it
    if best_achievement:
        clean_achievement = best_achievement.strip().rstrip('.')
        # Only append if it adds value (has numbers/metrics)
        if re.search(r'\d+', clean_achievement):
            summary = summary.rstrip('.') + f". Notable achievement: {clean_achievement}."
    
    return summary.strip()


def optimize_skills_section(resume_skills: list, jd_analysis: dict) -> list:
    """
    Optimize the skills section:
    - Keep all existing skills
    - Add JD skills that are in same domain as existing skills
    - Remove duplicates, organize logically
    """
    jd_tech_skills = jd_analysis.get("technical_skills", [])
    resume_text_lower = ' '.join([s.lower() for s in resume_skills])
    
    optimized = list(resume_skills)  # Start with existing skills
    
    # Identify what domains the candidate already works in
    existing_domains = set()
    for skill in resume_skills:
        for domain, domain_skills in SKILLS_DB.items():
            if skill.lower() in [s.lower() for s in domain_skills]:
                existing_domains.add(domain)
    
    for jd_skill in jd_tech_skills:
        # Skip if already present (case insensitive)
        if jd_skill.lower() in resume_text_lower:
            continue
        
        # Check if it's in the same domain as existing skills
        skill_domain = None
        for domain, domain_skills in SKILLS_DB.items():
            if jd_skill.lower() in [s.lower() for s in domain_skills]:
                skill_domain = domain
                break
        
        # Only add if domain matches (truthful, not fabrication)
        if skill_domain and skill_domain in existing_domains:
            # Use proper case
            optimized.append(jd_skill)
    
    # Deduplicate (case-insensitive), preserve original case
    seen = set()
    deduped = []
    for skill in optimized:
        key = skill.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(skill)
    
    return deduped


def optimize_experience(experience_list: list, jd_analysis: dict) -> list:
    """
    Optimize experience bullet points:
    - Replace weak verbs with strong action verbs
    - Insert relevant keywords naturally (max one per bullet, no repeats)
    - Improve clarity and impact
    """
    jd_skills = jd_analysis.get("technical_skills", [])[:12]
    jd_keywords = jd_analysis.get("keywords", [])[:10]
    
    optimized_experience = []
    used_keywords_global: List[str] = []  # Track across ALL bullets
    
    for entry in experience_list:
        optimized_entry = dict(entry)
        original_bullets = entry.get("bullets", [])
        optimized_bullets = []
        
        for bullet in original_bullets:
            if not bullet.strip():
                continue
            
            enhanced = enhance_bullet(bullet, jd_keywords, jd_skills, used_keywords_global)
            optimized_bullets.append(enhanced)
        
        optimized_entry["bullets"] = optimized_bullets
        optimized_experience.append(optimized_entry)
    
    return optimized_experience


def enhance_bullet(bullet: str, jd_keywords: list, jd_skills: list,
                   used_keywords: Optional[List[str]] = None) -> str:
    """
    Enhance a single bullet point:
    1. Apply smart transformations (Responsible for → Built)
    2. Insert missing keywords naturally (max one per bullet, no repeats)
    3. Ensure professional tone
    """
    if not bullet or len(bullet) < 5:
        return bullet
    
    if used_keywords is None:
        used_keywords = []
    
    # Step 1: Apply smart verb transformation
    enhanced = replace_weak_verb(bullet)
    
    # Step 2: Try to insert ONE relevant, unused JD skill keyword
    if len(enhanced) < 160:
        for skill in jd_skills:
            if skill in used_keywords:
                continue
            if skill.lower() in enhanced.lower():
                continue
            
            new_enhanced = insert_keyword_naturally(enhanced, skill)
            if new_enhanced != enhanced:
                used_keywords.append(skill)
                enhanced = new_enhanced
                break
    
    # Step 3: Ensure proper capitalization of first letter
    if enhanced:
        enhanced = enhanced[0].upper() + enhanced[1:]
    
    return enhanced


def compute_keyword_diff(before_text: str, after_text: str, jd_keywords: list) -> dict:
    """Compute which keywords were added in optimization"""
    before_lower = before_text.lower()
    after_lower = after_text.lower()
    
    added = []
    already_had = []
    seen = set()
    
    for kw in jd_keywords:
        kw_lower = kw.lower()
        if kw_lower in seen or len(kw_lower) < 3:
            continue
        seen.add(kw_lower)
        
        if kw_lower in after_lower:
            if kw_lower in before_lower:
                already_had.append(kw)
            else:
                added.append(kw)
    
    return {"added": added[:15], "already_had": already_had[:15]}


def optimize_resume(resume_data: dict, jd_analysis: dict) -> dict:
    """
    Main optimization orchestrator
    Takes parsed resume + JD analysis → returns optimized structured data
    """
    original_text = resume_data.get("full_text", "")
    
    # 1. Pre-optimization ATS score
    pre_ats = calculate_ats_score(resume_data, jd_analysis)
    
    # 2. Rewrite summary
    new_summary = rewrite_summary(resume_data, jd_analysis)
    
    # 3. Optimize skills
    original_skills = resume_data.get("skills", [])
    optimized_skills = optimize_skills_section(original_skills, jd_analysis)
    
    # 4. Optimize experience bullets
    original_experience = resume_data.get("experience", [])
    optimized_experience = optimize_experience(original_experience, jd_analysis)
    
    # 5. Build optimized resume structure
    optimized_data = {
        "name": resume_data.get("name", ""),
        "contact": resume_data.get("contact", {}),
        "summary": new_summary,
        "skills": optimized_skills,
        "experience": optimized_experience,
        "experience_raw": resume_data.get("experience_raw", ""),
        "education": resume_data.get("education", ""),
        "projects": resume_data.get("projects", ""),
        "certifications": resume_data.get("certifications", ""),
        "raw_sections": resume_data.get("raw_sections", {}),
        "jd_title": jd_analysis.get("job_title", ""),
        "domain": jd_analysis.get("domain", ""),
    }
    
    # 6. Post-optimization ATS score
    optimized_text_parts = [new_summary, ' '.join(optimized_skills)]
    for entry in optimized_experience:
        optimized_text_parts.extend(entry.get("bullets", []))
    optimized_text = ' '.join(optimized_text_parts).lower()
    
    temp_data = dict(optimized_data)
    temp_data["full_text"] = optimized_text + " " + original_text
    temp_data["raw_sections"] = resume_data.get("raw_sections", {})
    temp_data["contact"] = resume_data.get("contact", {})
    post_ats = calculate_ats_score(temp_data, jd_analysis)
    
    # 7. Keyword diff
    kw_diff = compute_keyword_diff(
        original_text,
        optimized_text,
        jd_analysis.get("technical_skills", []) + jd_analysis.get("keywords", [])
    )
    
    return {
        "optimized": optimized_data,
        "ats": {
            "before": pre_ats["total"],
            "after": post_ats["total"],
            "grade": post_ats["grade"],
            "breakdown": post_ats["breakdown"]
        },
        "keywords_added": kw_diff["added"],
        "keywords_existing": kw_diff["already_had"],
        "jd_analysis": jd_analysis
    }
