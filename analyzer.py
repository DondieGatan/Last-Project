import re
import fitz  # PyMuPDF
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords

# Download required NLTK data (run once)
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)
nltk.download('averaged_perceptron_tagger_eng', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('maxent_ne_chunker', quiet=True)
nltk.download('maxent_ne_chunker_tab', quiet=True)
nltk.download('words', quiet=True)

# ---------------------------------------------------------------------------
# Skills Database – categories and keywords
# ---------------------------------------------------------------------------
SKILLS_DB = {
    'Programming Languages': [
        'python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php', 'swift',
        'kotlin', 'go', 'rust', 'typescript', 'scala', 'r', 'matlab', 'perl',
        'objective-c', 'dart', 'lua', 'haskell', 'sql', 'html', 'css', 'bash',
        'powershell', 'assembly', 'vba', 'groovy', 'elixir', 'clojure'
    ],
    'Web Development': [
        'react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask',
        'spring boot', 'asp.net', 'laravel', 'ruby on rails', 'next.js',
        'nuxt.js', 'gatsby', 'bootstrap', 'tailwind', 'jquery', 'sass',
        'webpack', 'rest api', 'graphql', 'websocket', 'nginx', 'apache'
    ],
    'Data Science & AI': [
        'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'keras',
        'scikit-learn', 'pandas', 'numpy', 'matplotlib', 'seaborn', 'nlp',
        'natural language processing', 'computer vision', 'opencv', 'data mining',
        'data analysis', 'data visualization', 'power bi', 'tableau',
        'statistical analysis', 'regression', 'classification', 'clustering',
        'neural network', 'random forest', 'svm', 'xgboost', 'jupyter'
    ],
    'Database': [
        'mysql', 'postgresql', 'mongodb', 'sqlite', 'oracle', 'sql server',
        'redis', 'elasticsearch', 'cassandra', 'dynamodb', 'firebase',
        'neo4j', 'mariadb', 'couchdb', 'database design', 'data modeling'
    ],
    'Cloud & DevOps': [
        'aws', 'azure', 'google cloud', 'gcp', 'docker', 'kubernetes',
        'jenkins', 'ci/cd', 'terraform', 'ansible', 'git', 'github',
        'gitlab', 'bitbucket', 'linux', 'devops', 'microservices',
        'serverless', 'heroku', 'digitalocean', 'vagrant', 'prometheus'
    ],
    'Mobile Development': [
        'android', 'ios', 'react native', 'flutter', 'xamarin', 'ionic',
        'swift ui', 'kotlin multiplatform', 'cordova', 'mobile app development'
    ],
    'Soft Skills': [
        'leadership', 'teamwork', 'communication', 'problem solving',
        'project management', 'agile', 'scrum', 'time management',
        'critical thinking', 'collaboration', 'presentation', 'mentoring',
        'negotiation', 'strategic planning', 'decision making', 'adaptability'
    ],
    'Tools & Platforms': [
        'jira', 'confluence', 'slack', 'trello', 'figma', 'adobe photoshop',
        'adobe illustrator', 'visual studio', 'intellij', 'eclipse',
        'postman', 'swagger', 'selenium', 'cypress', 'jest', 'mocha',
        'unittest', 'pytest', 'maven', 'gradle', 'npm', 'yarn', 'pip'
    ]
}

# ---------------------------------------------------------------------------
# Degree keywords for education extraction
# ---------------------------------------------------------------------------
DEGREE_KEYWORDS = [
    "b.sc", "b.s.", "bachelor", "bsc", "b.tech", "btech", "b.e.", "be",
    "m.sc", "m.s.", "master", "msc", "m.tech", "mtech", "m.e.",
    "ph.d", "phd", "doctorate", "mba", "diploma", "associate",
    "b.a.", "ba", "m.a.", "ma", "b.com", "m.com", "bca", "mca",
    "b.eng", "m.eng", "llb", "ll.b", "md", "m.d."
]

# ---------------------------------------------------------------------------
# Job title keywords for experience extraction
# ---------------------------------------------------------------------------
JOB_TITLES = [
    'software engineer', 'developer', 'programmer', 'analyst', 'manager',
    'designer', 'architect', 'consultant', 'administrator', 'specialist',
    'coordinator', 'director', 'lead', 'intern', 'trainee', 'associate',
    'senior', 'junior', 'full stack', 'frontend', 'backend', 'devops',
    'data scientist', 'data engineer', 'data analyst', 'project manager',
    'product manager', 'qa engineer', 'test engineer', 'system administrator',
    'network engineer', 'security analyst', 'ux designer', 'ui designer',
    'technical writer', 'scrum master', 'business analyst', 'cto', 'ceo'
]

# ---------------------------------------------------------------------------
# Field recommendations based on skill clusters
# ---------------------------------------------------------------------------
FIELD_RECOMMENDATIONS = {
    'Web Development': ['react', 'angular', 'vue', 'node.js', 'django', 'flask',
                        'html', 'css', 'javascript', 'typescript', 'bootstrap'],
    'Data Science': ['machine learning', 'deep learning', 'tensorflow', 'pandas',
                     'numpy', 'data analysis', 'python', 'r', 'statistical analysis',
                     'data visualization', 'power bi', 'tableau'],
    'Mobile Development': ['android', 'ios', 'react native', 'flutter', 'swift',
                           'kotlin', 'mobile app development'],
    'Cloud Engineering': ['aws', 'azure', 'google cloud', 'docker', 'kubernetes',
                          'terraform', 'devops', 'ci/cd', 'linux'],
    'Database Administration': ['mysql', 'postgresql', 'mongodb', 'oracle',
                                'database design', 'sql', 'data modeling', 'redis'],
    'Cybersecurity': ['security', 'penetration testing', 'firewall', 'encryption',
                      'vulnerability', 'network security', 'security analyst'],
    'UI/UX Design': ['figma', 'adobe photoshop', 'adobe illustrator', 'ux',
                     'ui', 'wireframe', 'prototype', 'user research'],
    'Project Management': ['project management', 'agile', 'scrum', 'jira',
                           'leadership', 'strategic planning', 'confluence']
}


def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file using PyMuPDF."""
    text = ""
    doc = fitz.open(pdf_path)
    for page in doc:
        text += page.get_text()
    doc.close()
    return text


def extract_name(text):
    """Extract candidate name from the top of the resume."""
    lines = text.strip().split('\n')
    for line in lines[:5]:
        line = line.strip()
        if not line:
            continue
        # Skip lines that look like addresses, emails, or phone numbers
        if re.search(r'@|http|www|\d{5,}|phone|email|address|objective|summary', line, re.IGNORECASE):
            continue
        # A name is usually a short line of 2-4 words, all alphabetic
        words = line.split()
        if 1 <= len(words) <= 4 and all(w.isalpha() for w in words):
            return line.title()
    return "Unknown Candidate"


def extract_email(text):
    """Extract email address from resume text."""
    match = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', text)
    return match.group(0) if match else ""


def extract_phone(text):
    """Extract phone number from resume text."""
    patterns = [
        r'[\+]?[(]?[0-9]{1,4}[)]?[-\s.]?[0-9]{1,4}[-\s.]?[0-9]{4,6}',
        r'\+?\d{1,3}[-.\s]?\(?\d{2,3}\)?[-.\s]?\d{3,4}[-.\s]?\d{4}',
        r'\d{10,}'
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return ""


def extract_skills(text):
    """Extract skills from resume text using NLP and keyword matching."""
    text_lower = text.lower()

    found_skills = []
    seen = set()

    # Short skills that need word-boundary matching to avoid false positives
    short_skills = {'r', 'go', 'c#', 'c++', 'lua', 'dart', 'rust', 'java', 'ui', 'ux'}

    for category, skills in SKILLS_DB.items():
        for skill in skills:
            if skill in seen:
                continue
            if skill in short_skills:
                # Use word boundary regex for short/ambiguous skill names
                pattern = r'\b' + re.escape(skill) + r'\b'
                if re.search(pattern, text_lower):
                    found_skills.append((skill.title(), category))
                    seen.add(skill)
            else:
                if skill in text_lower and skill not in seen:
                    found_skills.append((skill.title(), category))
                    seen.add(skill)

    return found_skills


def extract_education(text):
    """Extract education information from resume text."""
    education = []
    lines = text.split('\n')

    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        for degree in DEGREE_KEYWORDS:
            if degree in line_lower:
                degree_text = line.strip()
                institution = ""
                # Check surrounding lines for institution name
                for j in range(max(0, i - 2), min(len(lines), i + 3)):
                    if j != i:
                        candidate = lines[j].strip()
                        if candidate and len(candidate) > 3:
                            university_keywords = ['university', 'college', 'institute',
                                                   'school', 'academy', 'polytechnic']
                            if any(kw in candidate.lower() for kw in university_keywords):
                                institution = candidate
                                break
                education.append((degree_text, institution))
                break

    return education


def extract_experience(text):
    """Extract work experience from resume text."""
    experience = []
    lines = text.split('\n')
    text_lower = text.lower()

    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        for title in JOB_TITLES:
            if title in line_lower:
                job_title = line.strip()
                company = ""
                description = ""
                # Look for company in nearby lines
                for j in range(max(0, i - 1), min(len(lines), i + 3)):
                    if j != i:
                        candidate = lines[j].strip()
                        if candidate and not any(t in candidate.lower() for t in JOB_TITLES):
                            if len(candidate) > 3 and len(candidate) < 100:
                                company = candidate
                                break
                # Collect description from subsequent lines
                desc_lines = []
                for j in range(i + 1, min(len(lines), i + 5)):
                    if lines[j].strip().startswith(('•', '-', '*', '–')):
                        desc_lines.append(lines[j].strip())
                description = ' '.join(desc_lines)

                experience.append((job_title, company, description))
                break

    return experience


def calculate_scores(text, skills, education, experience):
    """Calculate resume scores across multiple dimensions."""
    scores = {}

    # --- Skills Score (0-100) ---
    skill_count = len(skills)
    if skill_count >= 15:
        scores['skills'] = 100
    elif skill_count >= 10:
        scores['skills'] = 85
    elif skill_count >= 6:
        scores['skills'] = 70
    elif skill_count >= 3:
        scores['skills'] = 50
    else:
        scores['skills'] = max(20, skill_count * 15)

    # Bonus for diverse skill categories
    categories = set(cat for _, cat in skills)
    if len(categories) >= 4:
        scores['skills'] = min(100, scores['skills'] + 10)

    # --- Education Score (0-100) ---
    if not education:
        scores['education'] = 20
    else:
        text_lower = text.lower()
        if any(kw in text_lower for kw in ['ph.d', 'phd', 'doctorate']):
            scores['education'] = 100
        elif any(kw in text_lower for kw in ['master', 'm.sc', 'msc', 'm.tech', 'mba', 'mca']):
            scores['education'] = 85
        elif any(kw in text_lower for kw in ['bachelor', 'b.sc', 'bsc', 'b.tech', 'b.e.', 'bca']):
            scores['education'] = 70
        elif any(kw in text_lower for kw in ['diploma', 'associate']):
            scores['education'] = 50
        else:
            scores['education'] = 40

    # --- Experience Score (0-100) ---
    exp_count = len(experience)
    if exp_count >= 5:
        scores['experience'] = 100
    elif exp_count >= 3:
        scores['experience'] = 80
    elif exp_count >= 1:
        scores['experience'] = 60
    else:
        scores['experience'] = 20

    # Check for years of experience mentions
    year_match = re.findall(r'(\d+)\+?\s*years?', text, re.IGNORECASE)
    if year_match:
        max_years = max(int(y) for y in year_match)
        if max_years >= 10:
            scores['experience'] = min(100, scores['experience'] + 20)
        elif max_years >= 5:
            scores['experience'] = min(100, scores['experience'] + 10)

    # --- Formatting Score (0-100) ---
    formatting_score = 50  # Base score
    word_count = len(text.split())
    sentences = sent_tokenize(text)

    # Good length (300-1500 words)
    if 300 <= word_count <= 1500:
        formatting_score += 15
    elif 200 <= word_count <= 2000:
        formatting_score += 8

    # Has sections
    section_headers = ['education', 'experience', 'skills', 'projects',
                       'summary', 'objective', 'certifications', 'achievements']
    found_sections = sum(1 for s in section_headers if s in text.lower())
    formatting_score += min(20, found_sections * 5)

    # Has bullet points
    bullet_count = text.count('•') + text.count('- ') + text.count('* ')
    if bullet_count >= 5:
        formatting_score += 10
    elif bullet_count >= 2:
        formatting_score += 5

    # Has contact info
    if extract_email(text):
        formatting_score += 5

    scores['formatting'] = min(100, formatting_score)

    # --- Overall Score ---
    scores['overall'] = round(
        scores['skills'] * 0.30 +
        scores['education'] * 0.20 +
        scores['experience'] * 0.30 +
        scores['formatting'] * 0.20
    )

    return scores


def recommend_field(skills):
    """Recommend a career field based on extracted skills."""
    if not skills:
        return "General IT"

    skill_names = set(s.lower() for s, _ in skills)
    field_scores = {}

    for field, keywords in FIELD_RECOMMENDATIONS.items():
        score = sum(1 for kw in keywords if kw in skill_names)
        if score > 0:
            field_scores[field] = score

    if field_scores:
        return max(field_scores, key=field_scores.get)
    return "General IT"


def generate_recommendations(scores, skills, education, experience, text):
    """Generate improvement recommendations for the resume."""
    recommendations = []

    # Skills recommendations
    if scores['skills'] < 60:
        recommendations.append(
            "Add more technical skills to your resume. Include programming languages, "
            "frameworks, and tools you are proficient in."
        )

    categories = set(cat for _, cat in skills)
    if 'Soft Skills' not in categories:
        recommendations.append(
            "Include soft skills such as leadership, communication, and teamwork "
            "to make your profile well-rounded."
        )

    # Education recommendations
    if scores['education'] < 60:
        recommendations.append(
            "Consider adding relevant certifications or courses to strengthen "
            "your educational background."
        )

    # Experience recommendations
    if scores['experience'] < 60:
        recommendations.append(
            "Add more detail to your work experience section. Include specific "
            "achievements, metrics, and responsibilities."
        )

    if not any('•' in line or '- ' in line for line in text.split('\n')):
        recommendations.append(
            "Use bullet points to describe your experience and achievements "
            "for better readability."
        )

    # Formatting recommendations
    if scores['formatting'] < 60:
        recommendations.append(
            "Improve your resume formatting: ensure clear section headers, "
            "consistent styling, and a professional layout."
        )

    word_count = len(text.split())
    if word_count < 200:
        recommendations.append(
            "Your resume appears too short. Aim for at least 300-500 words "
            "with detailed descriptions of your skills and experience."
        )
    elif word_count > 1500:
        recommendations.append(
            "Your resume may be too long. Try to keep it concise — ideally "
            "1-2 pages — by focusing on the most relevant information."
        )

    if not extract_email(text):
        recommendations.append(
            "Add your email address to ensure recruiters can contact you."
        )

    section_headers = ['education', 'experience', 'skills', 'projects', 'summary']
    missing = [s.title() for s in section_headers if s not in text.lower()]
    if missing:
        recommendations.append(
            f"Consider adding these sections: {', '.join(missing[:3])}."
        )

    if not recommendations:
        recommendations.append(
            "Great resume! Keep it updated with your latest projects and skills."
        )

    return recommendations


def analyse_resume(pdf_path):
    """Main function: analyse a resume PDF and return all extracted data and scores."""
    # Step 1: Extract text
    text = extract_text_from_pdf(pdf_path)

    if not text.strip():
        return {
            'error': 'Could not extract text from the PDF. Please ensure the file is not scanned/image-only.'
        }

    # Step 2: Extract information
    name = extract_name(text)
    email = extract_email(text)
    phone = extract_phone(text)
    skills = extract_skills(text)
    education = extract_education(text)
    experience = extract_experience(text)

    # Step 3: Calculate scores
    scores = calculate_scores(text, skills, education, experience)

    # Step 4: Recommend career field
    field = recommend_field(skills)

    # Step 5: Generate recommendations
    recommendations = generate_recommendations(scores, skills, education, experience, text)

    return {
        'name': name,
        'email': email,
        'phone': phone,
        'raw_text': text,
        'skills': skills,
        'education': education,
        'experience': experience,
        'scores': scores,
        'recommended_field': field,
        'recommendations': recommendations
    }
