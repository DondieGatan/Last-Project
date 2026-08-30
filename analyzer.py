import re
import os
import fitz  # PyMuPDF
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords

# Configure Tesseract OCR path (Windows default install location)
TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
if os.path.exists(TESSERACT_PATH):
    try:
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
    except ImportError:
        pass

# Download required NLTK data (only if not already present)
def _ensure_nltk_data():
    packages = ['punkt', 'punkt_tab', 'averaged_perceptron_tagger',
                'averaged_perceptron_tagger_eng', 'stopwords',
                'maxent_ne_chunker', 'maxent_ne_chunker_tab', 'words']
    for pkg in packages:
        try:
            nltk.data.find(f'tokenizers/{pkg}' if 'punkt' in pkg else
                          f'taggers/{pkg}' if 'tagger' in pkg else
                          f'chunkers/{pkg}' if 'chunker' in pkg else
                          f'corpora/{pkg}')
        except LookupError:
            nltk.download(pkg, quiet=True)

_ensure_nltk_data()

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
        # Communication & Interpersonal
        'communication', 'verbal communication', 'written communication',
        'public speaking', 'active listening', 'interpersonal skills',
        'presentation', 'storytelling', 'persuasion', 'influencing',
        # Leadership & Management
        'leadership', 'team leadership', 'mentoring', 'coaching',
        'delegation', 'strategic planning', 'decision making',
        'conflict resolution', 'change management', 'people management',
        'stakeholder management', 'cross-functional collaboration',
        # Teamwork & Collaboration
        'teamwork', 'collaboration', 'team building', 'team player',
        'cooperative', 'group work',
        # Problem Solving & Thinking
        'problem solving', 'critical thinking', 'analytical thinking',
        'creative thinking', 'logical thinking', 'innovation',
        'research', 'attention to detail', 'troubleshooting',
        # Organization & Time
        'time management', 'multitasking', 'prioritization',
        'organizational skills', 'planning', 'scheduling',
        'deadline management', 'self-management',
        # Work Ethic & Character
        'adaptability', 'flexibility', 'self-motivated', 'work ethic',
        'reliability', 'punctuality', 'dependability', 'integrity',
        'professionalism', 'accountability', 'initiative',
        'willingness to learn', 'fast learner', 'quick learner',
        'self-starter', 'proactive', 'goal oriented',
        # Business & Professional
        'project management', 'agile', 'scrum', 'negotiation',
        'customer service', 'client relations', 'relationship building',
        'networking', 'business acumen', 'report writing',
        'documentation', 'training', 'onboarding',
        # Emotional Intelligence
        'empathy', 'emotional intelligence', 'patience', 'resilience',
        'stress management', 'composure', 'cultural awareness',
        'diversity and inclusion',
    ],
    'Tools & Platforms': [
        'jira', 'confluence', 'slack', 'trello', 'figma', 'adobe photoshop',
        'adobe illustrator', 'visual studio', 'intellij', 'eclipse',
        'postman', 'swagger', 'selenium', 'cypress', 'jest', 'mocha',
        'unittest', 'pytest', 'maven', 'gradle', 'npm', 'yarn', 'pip',
        'notion', 'asana', 'monday.com', 'basecamp', 'clickup',
        'adobe indesign', 'adobe xd', 'canva', 'sketch', 'invision',
        'microsoft office', 'microsoft excel', 'microsoft word',
        'microsoft powerpoint', 'google workspace', 'google sheets',
        'sharepoint', 'sap', 'salesforce', 'hubspot', 'zoho',
        'quickbooks', 'autocad', 'solidworks', 'revit', 'sketchup',
        'premiere pro', 'after effects', 'final cut pro', 'audacity',
        'obs studio', 'blender', '3ds max', 'unity', 'unreal engine',
        'wordpress', 'shopify', 'wix', 'squarespace',
        'zoom', 'microsoft teams', 'google meet',
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
    "b.eng", "beng", "m.eng", "meng", "llb", "ll.b", "md", "m.d.",
    "btec", "hnd", "hnc", "stem",
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
# Field recommendations — weighted skill mapping with experience context
# ---------------------------------------------------------------------------
FIELD_RECOMMENDATIONS = {
    # --- Technical IT Fields ---
    'Web Development': {
        'core': ['react', 'angular', 'vue', 'node.js', 'django', 'flask',
                 'next.js', 'express', 'laravel', 'spring boot', 'asp.net',
                 'ruby on rails', 'nuxt.js', 'gatsby'],
        'supporting': ['html', 'css', 'javascript', 'typescript', 'bootstrap',
                       'tailwind', 'sass', 'webpack', 'rest api', 'graphql',
                       'jquery', 'websocket', 'nginx', 'apache'],
        'experience_keywords': ['web developer', 'frontend developer', 'backend developer',
                                'full stack developer', 'full-stack developer',
                                'web application', 'web engineer'],
    },
    'Data Science & AI': {
        'core': ['machine learning', 'deep learning', 'tensorflow', 'pytorch',
                 'keras', 'scikit-learn', 'data mining', 'natural language processing',
                 'computer vision', 'neural network', 'random forest', 'svm',
                 'xgboost', 'data analysis', 'statistical analysis'],
        'supporting': ['pandas', 'numpy', 'matplotlib', 'seaborn', 'jupyter',
                       'data visualization', 'power bi', 'tableau', 'regression',
                       'classification', 'clustering'],
        'experience_keywords': ['data scientist', 'data analyst', 'machine learning engineer',
                                'ai engineer', 'data engineer', 'research scientist'],
    },
    'Mobile Development': {
        'core': ['android', 'ios', 'react native', 'flutter', 'xamarin',
                 'ionic', 'swift ui', 'kotlin multiplatform', 'cordova',
                 'mobile app development'],
        'supporting': ['swift', 'kotlin', 'dart', 'java', 'objective-c'],
        'experience_keywords': ['mobile developer', 'android developer',
                                'ios developer', 'app developer', 'mobile engineer'],
    },
    'Cloud & DevOps Engineering': {
        'core': ['aws', 'azure', 'google cloud', 'gcp', 'docker', 'kubernetes',
                 'terraform', 'ansible', 'jenkins', 'ci/cd', 'devops',
                 'serverless', 'microservices', 'prometheus'],
        'supporting': ['linux', 'git', 'github', 'gitlab', 'bitbucket',
                       'heroku', 'digitalocean', 'vagrant'],
        'experience_keywords': ['devops engineer', 'cloud engineer', 'site reliability engineer',
                                'infrastructure engineer', 'platform engineer', 'sre'],
    },
    'Database Administration': {
        'core': ['database design', 'data modeling', 'database administration',
                 'redis', 'elasticsearch', 'cassandra', 'dynamodb', 'neo4j',
                 'oracle', 'mongodb'],
        'supporting': ['mysql', 'postgresql', 'sql', 'sql server', 'firebase',
                       'mariadb', 'couchdb', 'sqlite'],
        'experience_keywords': ['database administrator', 'dba', 'database engineer',
                                'data architect'],
    },
    'Cybersecurity': {
        'core': ['security', 'penetration testing', 'firewall', 'encryption',
                 'vulnerability', 'network security', 'security analyst',
                 'ethical hacking', 'intrusion detection', 'siem'],
        'supporting': ['linux', 'python', 'bash', 'networking', 'compliance'],
        'experience_keywords': ['security analyst', 'security engineer',
                                'penetration tester', 'cybersecurity analyst', 'infosec'],
    },
    'UI/UX Design': {
        'core': ['figma', 'adobe photoshop', 'adobe illustrator',
                 'wireframe', 'prototype', 'user research', 'usability testing',
                 'interaction design', 'design system', 'adobe xd'],
        'supporting': ['sketch', 'invision', 'canva'],
        'experience_keywords': ['ux designer', 'ui designer', 'product designer',
                                'visual designer', 'graphic designer', 'ui/ux designer'],
    },
    'Software Engineering': {
        'core': ['python', 'java', 'c++', 'c#', 'typescript', 'git',
                 'rest api', 'microservices', 'design patterns',
                 'object oriented', 'algorithms', 'data structures'],
        'supporting': ['sql', 'linux', 'docker', 'testing', 'debugging',
                       'code review', 'agile', 'scrum'],
        'experience_keywords': ['software engineer', 'software developer',
                                'programmer', 'backend engineer'],
    },
    # --- Non-IT / Broader Career Fields ---
    'Business Administration': {
        'core': ['strategic planning', 'project management', 'business analysis',
                 'operations management', 'risk management', 'stakeholder management',
                 'pmp', 'prince2', 'six sigma', 'lean management'],
        'supporting': ['leadership', 'communication', 'teamwork', 'negotiation',
                       'decision making', 'time management', 'presentation',
                       'microsoft office', 'excel', 'powerpoint'],
        'experience_keywords': ['project manager', 'operations manager', 'business analyst',
                                'program manager', 'team lead', 'office manager',
                                'administrative', 'coordinator', 'executive assistant'],
    },
    'Customer Service & Hospitality': {
        'core': ['customer service', 'client relations', 'guest relations',
                 'hospitality management', 'front desk', 'concierge',
                 'conflict resolution', 'crm'],
        'supporting': ['communication', 'teamwork', 'adaptability', 'presentation',
                       'time management', 'problem solving', 'multitasking'],
        'experience_keywords': ['customer service', 'receptionist', 'front desk',
                                'hospitality', 'guest service', 'event staff',
                                'event coordinator', 'vendor', 'cashier', 'barista',
                                'waiter', 'waitress', 'hotel', 'restaurant'],
    },
    'Accounting & Finance': {
        'core': ['accounting', 'financial analysis', 'bookkeeping', 'auditing',
                 'tax preparation', 'financial reporting', 'budgeting',
                 'accounts payable', 'accounts receivable', 'quickbooks'],
        'supporting': ['excel', 'sap', 'financial modeling', 'data analysis',
                       'communication', 'attention to detail'],
        'experience_keywords': ['accountant', 'financial analyst', 'bookkeeper',
                                'auditor', 'tax', 'finance officer', 'accounts',
                                'billing', 'payroll', 'comptroller'],
    },
    'Mechanical Engineering': {
        'core': ['mechanical engineering', 'thermodynamics', 'fluid mechanics',
                 'solidworks', 'autocad', 'mechanical design', 'cad',
                 'manufacturing', 'cnc', '3d printing', 'hvac', 'plc',
                 'finite element analysis', 'fea', 'gd&t'],
        'supporting': ['matlab', 'project management', 'technical writing',
                       'problem solving', 'quality control', 'safety management'],
        'experience_keywords': ['mechanical engineer', 'maintenance technician',
                                'maintenance engineer', 'manufacturing engineer',
                                'quality engineer', 'production engineer',
                                'design engineer', 'process engineer'],
    },
    'Electrical & Electronics Engineering': {
        'core': ['electrical engineering', 'circuit design', 'pcb design',
                 'embedded systems', 'microcontroller', 'arduino', 'raspberry pi',
                 'power systems', 'signal processing', 'vhdl', 'verilog',
                 'plc programming', 'scada', 'control systems'],
        'supporting': ['matlab', 'autocad', 'problem solving', 'technical writing',
                       'project management', 'testing', 'debugging'],
        'experience_keywords': ['electrical engineer', 'electronics engineer',
                                'hardware engineer', 'power engineer',
                                'control engineer', 'instrumentation engineer',
                                'automation engineer', 'engineering technician'],
    },
    'Civil Engineering': {
        'core': ['civil engineering', 'structural analysis', 'autocad',
                 'structural design', 'construction management', 'surveying',
                 'geotechnical', 'concrete design', 'steel design',
                 'building information modeling', 'bim', 'revit', 'etabs',
                 'staad pro', 'primavera'],
        'supporting': ['project management', 'quality control', 'safety management',
                       'technical writing', 'problem solving', 'cad'],
        'experience_keywords': ['civil engineer', 'structural engineer', 'site engineer',
                                'construction manager', 'project engineer',
                                'geotechnical engineer', 'quantity surveyor',
                                'construction engineer', 'building inspector'],
    },
    'Aerospace & Aviation': {
        'core': ['aerospace', 'aerodynamics', 'aircraft maintenance', 'avionics',
                 'flight mechanics', 'propulsion', 'composites',
                 'wind tunnel', 'gas turbine', 'ansys', 'catia'],
        'supporting': ['matlab', 'solidworks', 'autocad', 'project management',
                       'safety management', 'quality control', 'technical writing'],
        'experience_keywords': ['aerospace engineer', 'aviation', 'aircraft maintenance',
                                'flight engineer', 'avionics technician',
                                'aircraft technician', 'pilot', 'airline',
                                'aviation maintenance'],
    },
    'Chemical & Industrial Engineering': {
        'core': ['chemical engineering', 'process engineering', 'industrial engineering',
                 'lean manufacturing', 'six sigma', 'process optimization',
                 'quality assurance', 'supply chain', 'aspen plus',
                 'process simulation', 'hazop'],
        'supporting': ['matlab', 'project management', 'problem solving',
                       'quality control', 'safety management', 'excel'],
        'experience_keywords': ['chemical engineer', 'process engineer',
                                'industrial engineer', 'quality engineer',
                                'plant engineer', 'production engineer',
                                'lab technician', 'research scientist'],
    },
    'Marketing & Communications': {
        'core': ['digital marketing', 'seo', 'sem', 'social media marketing',
                 'content marketing', 'email marketing', 'google analytics',
                 'brand management', 'copywriting', 'public relations'],
        'supporting': ['canva', 'photoshop', 'communication', 'presentation',
                       'creativity', 'writing', 'analytics'],
        'experience_keywords': ['marketing manager', 'marketing coordinator',
                                'social media manager', 'content creator',
                                'communications specialist', 'brand manager',
                                'copywriter', 'pr specialist'],
    },
    'Education & Training': {
        'core': ['curriculum development', 'lesson planning', 'classroom management',
                 'educational technology', 'student assessment', 'tutoring',
                 'e-learning', 'instructional design'],
        'supporting': ['communication', 'presentation', 'leadership', 'patience',
                       'mentoring', 'microsoft office'],
        'experience_keywords': ['teacher', 'instructor', 'tutor', 'professor',
                                'trainer', 'academic advisor', 'teaching assistant',
                                'lecturer', 'education coordinator'],
    },
    # --- Healthcare & Medical ---
    'Nursing & Patient Care': {
        'core': ['patient care', 'vital signs', 'medication administration',
                 'wound care', 'intravenous therapy', 'patient assessment',
                 'clinical documentation', 'infection control', 'cpr',
                 'basic life support', 'advanced cardiac life support'],
        'supporting': ['communication', 'teamwork', 'empathy', 'time management',
                       'critical thinking', 'problem solving'],
        'experience_keywords': ['nurse', 'registered nurse', 'licensed practical nurse',
                                'nursing assistant', 'patient care', 'clinical nurse',
                                'charge nurse', 'staff nurse', 'caregiver',
                                'healthcare assistant', 'medical assistant'],
    },
    'Medicine & Healthcare': {
        'core': ['diagnosis', 'treatment planning', 'clinical research',
                 'patient management', 'medical imaging', 'surgery',
                 'emergency medicine', 'internal medicine', 'radiology',
                 'pathology', 'pharmacology', 'anesthesiology'],
        'supporting': ['research', 'communication', 'leadership', 'teamwork',
                       'critical thinking', 'problem solving'],
        'experience_keywords': ['doctor', 'physician', 'surgeon', 'medical officer',
                                'resident', 'specialist', 'consultant',
                                'medical director', 'general practitioner',
                                'pediatrician', 'cardiologist', 'dermatologist',
                                'hospital', 'clinic'],
    },
    'Pharmacy': {
        'core': ['pharmacology', 'drug dispensing', 'prescription management',
                 'pharmaceutical care', 'drug interactions', 'compounding',
                 'clinical pharmacy', 'medication counseling',
                 'pharmaceutical analysis', 'pharmacokinetics'],
        'supporting': ['attention to detail', 'communication', 'customer service',
                       'chemistry', 'biology'],
        'experience_keywords': ['pharmacist', 'pharmacy technician', 'pharmacy assistant',
                                'clinical pharmacist', 'pharmacy manager',
                                'pharmaceutical', 'drugstore', 'dispensary'],
    },
    'Dentistry': {
        'core': ['dental care', 'oral surgery', 'orthodontics', 'dental hygiene',
                 'dental restoration', 'periodontics', 'endodontics',
                 'prosthodontics', 'dental imaging', 'dental instruments'],
        'supporting': ['patient care', 'communication', 'attention to detail',
                       'infection control', 'sterilization'],
        'experience_keywords': ['dentist', 'dental hygienist', 'dental assistant',
                                'dental technician', 'orthodontist',
                                'dental clinic', 'oral surgeon'],
    },
    'Psychology & Counseling': {
        'core': ['counseling', 'psychotherapy', 'psychological assessment',
                 'cognitive behavioral therapy', 'cbt', 'mental health',
                 'behavioral analysis', 'crisis intervention',
                 'group therapy', 'case management'],
        'supporting': ['communication', 'empathy', 'active listening',
                       'critical thinking', 'research', 'report writing'],
        'experience_keywords': ['psychologist', 'counselor', 'therapist',
                                'mental health', 'social worker', 'case manager',
                                'behavioral analyst', 'psychiatric',
                                'guidance counselor', 'rehabilitation'],
    },
    # --- Law & Legal ---
    'Law & Legal': {
        'core': ['legal research', 'contract drafting', 'litigation',
                 'legal writing', 'case management', 'due diligence',
                 'dispute resolution', 'arbitration', 'mediation',
                 'intellectual property', 'corporate law', 'criminal law',
                 'compliance', 'regulatory affairs'],
        'supporting': ['communication', 'negotiation', 'critical thinking',
                       'research', 'attention to detail', 'presentation'],
        'experience_keywords': ['lawyer', 'attorney', 'legal counsel', 'paralegal',
                                'legal assistant', 'legal advisor', 'solicitor',
                                'barrister', 'law clerk', 'judge', 'magistrate',
                                'legal officer', 'compliance officer', 'notary'],
    },
    # --- Human Resources ---
    'Human Resources': {
        'core': ['recruitment', 'talent acquisition', 'employee relations',
                 'performance management', 'compensation and benefits',
                 'payroll management', 'hr policy', 'onboarding',
                 'training and development', 'workforce planning',
                 'labor law', 'hris', 'workday', 'sap hr'],
        'supporting': ['communication', 'leadership', 'negotiation',
                       'conflict resolution', 'excel', 'presentation'],
        'experience_keywords': ['hr manager', 'human resources', 'recruiter',
                                'talent acquisition', 'hr coordinator',
                                'hr specialist', 'hr officer', 'hr director',
                                'people operations', 'hr business partner',
                                'compensation analyst', 'benefits administrator'],
    },
    # --- Sales & Retail ---
    'Sales & Retail': {
        'core': ['sales strategy', 'business development', 'account management',
                 'crm', 'salesforce', 'lead generation', 'pipeline management',
                 'revenue growth', 'retail management', 'visual merchandising',
                 'inventory management', 'point of sale'],
        'supporting': ['communication', 'negotiation', 'customer service',
                       'teamwork', 'presentation', 'excel'],
        'experience_keywords': ['sales manager', 'sales executive', 'account manager',
                                'business development', 'sales representative',
                                'retail manager', 'store manager', 'sales associate',
                                'sales officer', 'commercial manager',
                                'key account', 'territory manager', 'shop assistant'],
    },
    # --- Logistics & Supply Chain ---
    'Logistics & Supply Chain': {
        'core': ['supply chain management', 'logistics management', 'inventory control',
                 'warehouse management', 'procurement', 'transportation management',
                 'demand planning', 'freight', 'customs clearance',
                 'import export', 'sap mm', 'erp'],
        'supporting': ['excel', 'communication', 'problem solving',
                       'time management', 'negotiation', 'teamwork'],
        'experience_keywords': ['logistics manager', 'supply chain', 'warehouse manager',
                                'procurement officer', 'logistics coordinator',
                                'shipping', 'freight', 'dispatch', 'inventory manager',
                                'supply planner', 'purchasing', 'buyer',
                                'import export', 'customs', 'fleet manager'],
    },
    # --- Architecture & Interior Design ---
    'Architecture & Interior Design': {
        'core': ['architectural design', 'autocad', 'revit', 'sketchup',
                 '3ds max', 'rhino', 'grasshopper', 'building codes',
                 'interior design', 'space planning', 'rendering',
                 'sustainable design', 'leed', 'bim'],
        'supporting': ['photoshop', 'illustrator', 'creativity', 'communication',
                       'project management', 'presentation'],
        'experience_keywords': ['architect', 'interior designer', 'architectural designer',
                                'design architect', 'draftsman', 'space planner',
                                'landscape architect', 'urban planner',
                                'architectural technician', 'bim modeler'],
    },
    # --- Media, Journalism & Creative Arts ---
    'Media & Journalism': {
        'core': ['journalism', 'news writing', 'broadcasting', 'video editing',
                 'audio editing', 'premiere pro', 'final cut pro',
                 'after effects', 'media production', 'photojournalism',
                 'scriptwriting', 'podcasting', 'content creation'],
        'supporting': ['communication', 'writing', 'creativity', 'research',
                       'social media', 'photography'],
        'experience_keywords': ['journalist', 'reporter', 'editor', 'news anchor',
                                'broadcaster', 'media producer', 'video editor',
                                'content creator', 'cameraman', 'photographer',
                                'news writer', 'correspondent', 'producer'],
    },
    'Graphic Design & Creative Arts': {
        'core': ['graphic design', 'adobe photoshop', 'adobe illustrator',
                 'indesign', 'after effects', 'logo design', 'branding',
                 'typography', 'motion graphics', 'visual identity',
                 'print design', 'packaging design', 'illustration'],
        'supporting': ['creativity', 'communication', 'canva', 'figma',
                       'presentation', 'attention to detail'],
        'experience_keywords': ['graphic designer', 'creative director', 'art director',
                                'visual designer', 'brand designer', 'illustrator',
                                'print designer', 'creative lead',
                                'multimedia artist', 'animation'],
    },
    # --- Real Estate & Property ---
    'Real Estate & Property': {
        'core': ['real estate', 'property management', 'property valuation',
                 'lease management', 'real estate law', 'market analysis',
                 'property inspection', 'tenant relations',
                 'real estate marketing', 'mortgage'],
        'supporting': ['negotiation', 'communication', 'customer service',
                       'sales', 'excel', 'presentation'],
        'experience_keywords': ['real estate agent', 'property manager', 'broker',
                                'real estate consultant', 'leasing agent',
                                'real estate analyst', 'property consultant',
                                'estate agent', 'realtor', 'facilities manager'],
    },
    # --- Banking & Insurance ---
    'Banking & Financial Services': {
        'core': ['banking operations', 'credit analysis', 'risk assessment',
                 'financial advisory', 'wealth management', 'investment analysis',
                 'portfolio management', 'anti money laundering', 'aml', 'kyc',
                 'trade finance', 'treasury', 'foreign exchange'],
        'supporting': ['excel', 'communication', 'customer service',
                       'attention to detail', 'negotiation', 'analytics'],
        'experience_keywords': ['bank manager', 'bank teller', 'relationship manager',
                                'credit analyst', 'loan officer', 'financial advisor',
                                'investment analyst', 'wealth manager',
                                'underwriter', 'compliance officer', 'banker',
                                'insurance agent', 'claims analyst', 'actuary'],
    },
    # --- IT Support & Systems Administration ---
    'IT Support & Systems Administration': {
        'core': ['technical support', 'help desk', 'active directory',
                 'windows server', 'network administration', 'tcp/ip',
                 'troubleshooting', 'itil', 'service desk',
                 'vmware', 'system administration', 'office 365'],
        'supporting': ['linux', 'networking', 'communication', 'problem solving',
                       'customer service', 'ticketing systems'],
        'experience_keywords': ['it support', 'help desk', 'system administrator',
                                'network administrator', 'it technician',
                                'desktop support', 'technical support',
                                'it specialist', 'it analyst', 'it officer',
                                'support engineer', 'it coordinator'],
    },
    # --- Social Work & Community Services ---
    'Social Work & Community Services': {
        'core': ['social work', 'community development', 'case management',
                 'advocacy', 'crisis intervention', 'needs assessment',
                 'group facilitation', 'program development',
                 'child welfare', 'family services'],
        'supporting': ['communication', 'empathy', 'leadership', 'teamwork',
                       'problem solving', 'report writing'],
        'experience_keywords': ['social worker', 'community worker', 'case worker',
                                'outreach coordinator', 'program coordinator',
                                'ngo', 'volunteer coordinator', 'charity',
                                'humanitarian', 'youth worker', 'child protection'],
    },
    # --- Agriculture & Environmental Science ---
    'Agriculture & Environmental Science': {
        'core': ['agriculture', 'agronomy', 'crop management', 'soil science',
                 'irrigation', 'environmental impact assessment',
                 'sustainability', 'conservation', 'gis',
                 'remote sensing', 'water management', 'ecology'],
        'supporting': ['research', 'data analysis', 'project management',
                       'report writing', 'problem solving', 'fieldwork'],
        'experience_keywords': ['agricultural', 'agronomist', 'farm manager',
                                'environmental scientist', 'ecologist',
                                'conservation officer', 'forestry',
                                'horticulturist', 'wildlife', 'sustainability'],
    },
    # --- Culinary Arts & Food Industry ---
    'Culinary Arts & Food Industry': {
        'core': ['culinary arts', 'food preparation', 'menu planning',
                 'food safety', 'haccp', 'kitchen management',
                 'pastry', 'baking', 'food presentation', 'nutrition',
                 'catering', 'recipe development'],
        'supporting': ['teamwork', 'time management', 'creativity',
                       'communication', 'customer service', 'leadership'],
        'experience_keywords': ['chef', 'cook', 'sous chef', 'pastry chef',
                                'executive chef', 'kitchen manager',
                                'food and beverage', 'catering manager',
                                'baker', 'culinary', 'restaurant manager',
                                'barista', 'bartender', 'food service'],
    },
    # --- Transportation & Shipping ---
    'Transportation & Shipping': {
        'core': ['fleet management', 'route planning', 'cargo management',
                 'shipping documentation', 'vessel operations',
                 'maritime', 'port operations', 'freight forwarding',
                 'dangerous goods', 'transport planning'],
        'supporting': ['communication', 'problem solving', 'time management',
                       'customer service', 'excel', 'safety management'],
        'experience_keywords': ['driver', 'captain', 'pilot', 'seafarer',
                                'shipping', 'marine', 'transport manager',
                                'fleet manager', 'logistics', 'delivery',
                                'courier', 'freight', 'dispatch',
                                'maritime', 'seaman', 'able bodied seaman'],
    },
    # --- Government & Public Administration ---
    'Government & Public Administration': {
        'core': ['public policy', 'governance', 'public administration',
                 'policy analysis', 'regulatory compliance',
                 'government relations', 'public finance',
                 'program evaluation', 'grant writing'],
        'supporting': ['leadership', 'communication', 'research',
                       'report writing', 'presentation', 'excel'],
        'experience_keywords': ['government', 'public servant', 'civil servant',
                                'policy analyst', 'government officer',
                                'public affairs', 'city planner', 'administrator',
                                'municipal', 'embassy', 'consulate',
                                'regulatory', 'public sector'],
    },
    # --- Research & Academia ---
    'Research & Academia': {
        'core': ['research methodology', 'data analysis', 'statistical analysis',
                 'academic writing', 'peer review', 'literature review',
                 'grant writing', 'spss', 'r programming', 'lab management',
                 'experimental design', 'qualitative research'],
        'supporting': ['communication', 'presentation', 'critical thinking',
                       'excel', 'python', 'writing'],
        'experience_keywords': ['researcher', 'research assistant', 'research associate',
                                'postdoctoral', 'research fellow', 'lab manager',
                                'research scientist', 'academic', 'scholar',
                                'research coordinator', 'principal investigator'],
    },
    # --- Fitness & Sports ---
    'Fitness & Sports': {
        'core': ['personal training', 'fitness assessment', 'exercise programming',
                 'sports coaching', 'nutrition planning', 'strength and conditioning',
                 'rehabilitation', 'sports science', 'kinesiology',
                 'group fitness', 'yoga', 'pilates'],
        'supporting': ['communication', 'motivation', 'leadership', 'first aid',
                       'teamwork', 'time management'],
        'experience_keywords': ['personal trainer', 'fitness instructor',
                                'sports coach', 'gym manager', 'athletic trainer',
                                'fitness manager', 'yoga instructor',
                                'strength coach', 'physical therapist',
                                'physiotherapist', 'sports therapist'],
    },
    # --- Fashion & Beauty ---
    'Fashion & Beauty': {
        'core': ['fashion design', 'pattern making', 'garment construction',
                 'textile knowledge', 'fashion illustration', 'beauty therapy',
                 'makeup artistry', 'hair styling', 'skin care',
                 'fashion merchandising', 'trend forecasting'],
        'supporting': ['creativity', 'communication', 'customer service',
                       'attention to detail', 'teamwork', 'sales'],
        'experience_keywords': ['fashion designer', 'stylist', 'makeup artist',
                                'hair stylist', 'beautician', 'tailor',
                                'fashion buyer', 'visual merchandiser',
                                'beauty therapist', 'nail technician',
                                'salon manager', 'fashion consultant'],
    },
    # --- Telecommunications ---
    'Telecommunications': {
        'core': ['telecommunications', 'rf engineering', 'fiber optics',
                 'network planning', '5g', '4g', 'lte', 'voip',
                 'satellite communication', 'telecom infrastructure',
                 'oss', 'bss', 'nokia', 'ericsson', 'huawei'],
        'supporting': ['networking', 'linux', 'project management',
                       'problem solving', 'communication', 'excel'],
        'experience_keywords': ['telecom engineer', 'rf engineer', 'network engineer',
                                'telecommunications', 'field engineer',
                                'noc engineer', 'transmission engineer',
                                'telecom technician', 'fiber optic',
                                'tower technician', 'network planner'],
    },
}

# ---------------------------------------------------------------------------
# Allowed image extensions for OCR
# ---------------------------------------------------------------------------
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp'}


def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file using PyMuPDF.

    Handles three cases:
    1. Text-based PDFs — direct text extraction
    2. Scanned/image PDFs — renders pages to images and runs OCR
    3. Mixed PDFs — combines both approaches per page
    """
    text = ""
    doc = fitz.open(pdf_path)

    for page in doc:
        # Try normal text extraction first
        page_text = page.get_text()

        if page_text and len(page_text.strip()) > 20:
            text += page_text
        else:
            # Page has no selectable text — it's likely a scanned image
            # Try OCR using pytesseract
            ocr_text = _ocr_page(page)
            if ocr_text:
                text += ocr_text + "\n"

    doc.close()
    return text


def _ocr_page(page):
    """Run OCR on a single PDF page by rendering it to an image."""
    try:
        import pytesseract
        from PIL import Image
        import io as _io

        # Render the page at high resolution for better OCR accuracy
        pix = page.get_pixmap(dpi=300)
        img_data = pix.tobytes("png")
        img = Image.open(_io.BytesIO(img_data))
        return pytesseract.image_to_string(img)
    except ImportError:
        # pytesseract not installed — try basic extraction as last resort
        try:
            return page.get_text("text", flags=fitz.TEXT_PRESERVE_WHITESPACE)
        except Exception:
            return ""
    except Exception:
        return ""


def extract_text_from_image(image_path):
    """Extract text from an image file using pytesseract OCR."""
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text
    except ImportError:
        return ""
    except Exception:
        return ""


def _has_tesseract():
    """Check if Tesseract OCR is available on the system."""
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def extract_text_from_docx(file_path):
    """Extract text from a .docx file using python-docx."""
    try:
        from docx import Document
        doc = Document(file_path)
        return '\n'.join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception:
        return ""


def extract_text(file_path):
    """Extract text from a PDF, Word, or image file, choosing the right method."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext == '.docx':
        return extract_text_from_docx(file_path)
    elif ext in IMAGE_EXTENSIONS:
        return extract_text_from_image(file_path)
    else:
        return ""


def extract_name(text):
    """Extract candidate name from the resume using multiple strategies.

    Uses a layered approach:
    1. Filter out section headers and common resume vocabulary
    2. Identify lines that look like human names (not English words)
    3. Handle multi-line names split across PDF lines
    4. Use NLTK NER as a fallback
    """
    lines = text.strip().split('\n')

    # ── Section headers that are NEVER names ──
    SECTION_HEADERS = {
        'education', 'experience', 'skills', 'projects', 'summary', 'objective',
        'certifications', 'achievements', 'references', 'profile', 'contact',
        'interests', 'hobbies', 'languages', 'awards', 'training', 'volunteer',
        'publications', 'activities', 'qualifications', 'technical skills',
        'work experience', 'professional experience', 'personal information',
        'curriculum vitae', 'resume', 'cv', 'portfolio', 'about me', 'about',
        'personal details', 'career objective', 'professional summary',
        'profile summary', 'work history', 'key skills', 'core competencies',
        'soft skills', 'hard skills', 'relevant coursework', 'coursework',
        'extracurricular', 'extracurricular activities', 'leadership',
        'professional skills', 'additional information', 'declaration',
    }

    # ── Common English words found in resumes that are NOT names ──
    # If ALL words in a line are common English words, it's NOT a name
    NOT_NAME_WORDS = {
        # Resume section/descriptor words
        'adaptability', 'leadership', 'problem', 'solving', 'skills', 'communication',
        'fast', 'learner', 'ability', 'multi', 'task', 'hard', 'working', 'social',
        'media', 'time', 'management', 'motivated', 'eager', 'learn', 'seeking',
        'entry', 'level', 'opportunity', 'strong', 'work', 'ethic', 'passion',
        'continuous', 'growth', 'committed', 'contributing', 'team', 'success',
        'gaining', 'valuable', 'professional', 'environment', 'detail', 'oriented',
        'creative', 'analytical', 'critical', 'thinking', 'interpersonal',
        'organizational', 'self', 'driven', 'proactive', 'flexible', 'reliable',
        'dedicated', 'enthusiastic', 'innovative', 'strategic', 'collaborative',
        # Job/activity description words
        'performed', 'demonstrated', 'applied', 'conducted', 'maintained',
        'developed', 'designed', 'managed', 'organized', 'implemented',
        'achieved', 'hands', 'practical', 'experience', 'proficiency',
        'workshop', 'training', 'inspection', 'component', 'protocols',
        'free', 'strict', 'accordance', 'relevant', 'technical', 'compliance',
        'ensuring', 'support', 'provided', 'assisted', 'coordinated',
        # Job titles
        'student', 'engineer', 'developer', 'designer', 'manager', 'analyst',
        'consultant', 'specialist', 'coordinator', 'assistant', 'associate',
        'director', 'officer', 'administrator', 'technician', 'supervisor',
        'intern', 'freelancer', 'graduate', 'undergraduate', 'senior', 'junior',
        'lead', 'head', 'chief', 'executive', 'president', 'vice',
        'college', 'university', 'school', 'institute', 'academy',
        'software', 'hardware', 'network', 'system', 'database', 'web', 'mobile',
        'full', 'stack', 'front', 'end', 'back', 'data', 'science', 'information',
        'technology', 'computer', 'business', 'marketing', 'sales', 'finance',
        'accounting', 'human', 'resources', 'operations', 'project',
        # Common filler
        'the', 'and', 'for', 'with', 'from', 'that', 'this', 'are', 'was', 'were',
        'been', 'being', 'have', 'has', 'had', 'having', 'will', 'would', 'could',
        'should', 'may', 'might', 'can', 'shall', 'must', 'need', 'want',
        'new', 'old', 'good', 'best', 'more', 'most', 'very', 'well', 'also',
        'who', 'where', 'when', 'what', 'how', 'why', 'which',
        # Address/location words
        'street', 'road', 'avenue', 'boulevard', 'city', 'state', 'country',
        'floor', 'building', 'tower', 'block', 'unit', 'apartment',
    }

    def is_section_header(line_text):
        """Check if a line is a section header."""
        cleaned = line_text.lower().strip()
        if cleaned in SECTION_HEADERS:
            return True
        # Spaced-out headers: "S K I L L S" -> "skills"
        collapsed = re.sub(r'\s+', '', cleaned)
        if collapsed in SECTION_HEADERS:
            return True
        # Headers with decorators: "--- SKILLS ---" or "| EDUCATION |"
        stripped = re.sub(r'^[\s\-–—=_|*#]+|[\s\-–—=_|*#]+$', '', cleaned)
        if stripped in SECTION_HEADERS:
            return True
        return False

    def is_noise_line(line_text):
        """Check if a line is contact info, URL, date, or other non-name content."""
        line_text = line_text.strip()
        if not line_text or len(line_text) < 2:
            return True
        # Email
        if re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', line_text):
            return True
        # URL
        if re.search(r'(http|www\.|\.com|\.org|\.net|\.edu|linkedin|github|portfolio)', line_text, re.IGNORECASE):
            return True
        # Phone number (digits with separators dominate the line)
        digits_only = re.sub(r'[^\d]', '', line_text)
        if len(digits_only) >= 7 and len(digits_only) / max(len(line_text.replace(' ', '')), 1) > 0.5:
            return True
        # Starts with phone-like pattern
        if re.match(r'^[\s?]*[\+\(]?\d', line_text) and len(digits_only) >= 7:
            return True
        # Address-like
        if re.search(r'\b\d{4,6}\b', line_text) and re.search(
            r'(street|road|ave|blvd|city|state|zip|uae|usa|uk|country|sharjah|dubai|abu dhabi|deira|cavite|imus)',
            line_text, re.IGNORECASE
        ):
            return True
        # Job title lines
        if re.match(
            r'^(college student|student|software engineer|developer|intern|freelancer|'
            r'graduate|undergraduate|full[- ]?stack|front[- ]?end|back[- ]?end|'
            r'data scientist|data analyst|project manager|web developer|'
            r'graphic designer|ui.?ux designer|accountant|teacher|nurse)s?$',
            line_text.strip(), re.IGNORECASE
        ):
            return True
        # Lines containing institutional keywords (universities, schools, companies)
        if re.search(
            r'\b(university|college|school|institute|academy|corporation|company|'
            r'inc\b|ltd\b|llc\b|group|foundation|center|centre|department|faculty|'
            r'hospital|clinic|organization|organisation)\b',
            line_text, re.IGNORECASE
        ):
            return True
        # Degree/certification lines (BSc, MSc, BA, PhD, etc.)
        if re.search(
            r'\b(bsc|msc|ba\b|ma\b|phd|bachelor|master|doctorate|diploma|certificate|'
            r'b\.?s\.?c|m\.?s\.?c|b\.?a\b|m\.?a\b|b\.?eng|m\.?eng|btec|'
            r'engineering|accountancy|management|nursing|medicine|computing|'
            r'expected to graduate|graduated|graduating)\b',
            line_text, re.IGNORECASE
        ):
            return True
        # Lines that look like tech skill lists
        tech_words = {
            'cisco', 'java', 'html', 'python', 'php', 'xampp', 'css', 'javascript',
            'sql', 'power', 'bi', 'jupyter', 'notebook', 'react', 'angular', 'vue',
            'node', 'express', 'django', 'flask', 'typescript', 'mongodb', 'mysql',
            'postgresql', 'docker', 'kubernetes', 'aws', 'azure', 'git', 'linux',
            'windows', 'macos', 'figma', 'photoshop', 'excel', 'word', 'tableau',
            'tensorflow', 'pytorch', 'numpy', 'pandas', 'matplotlib', 'seaborn',
            'spring', 'boot', 'laravel', 'ruby', 'rails', 'swift', 'kotlin',
            'flutter', 'dart', 'rust', 'go', 'scala', 'redis', 'firebase',
            'supabase', 'vercel', 'heroku', 'jira', 'trello', 'agile', 'scrum',
        }
        line_words_lower = [w.lower() for w in line_text.split()]
        if len(line_words_lower) >= 2 and any(w in tech_words for w in line_words_lower):
            if sum(1 for w in line_words_lower if w in tech_words) >= len(line_words_lower) * 0.5:
                return True
        # Lines that are entirely common English words (descriptions, not names)
        if len(line_words_lower) >= 2 and all(w in NOT_NAME_WORDS for w in line_words_lower):
            return True
        return False

    def is_name_like(line_text, allow_single_word=False):
        """Check if a line looks like a person's name.

        A name must:
        - Be 1-5 alphabetic words (2-5 by default)
        - NOT have all words be common English / resume vocabulary
        - Each word starts with a letter (unicode-aware)
        """
        clean = re.sub(r'^[\s\-–—|:?•·]+|[\s\-–—|:?•·]+$', '', line_text).strip()
        if not clean or len(clean) < 2:
            return False, ""
        # Remove pipe separators
        if '|' in clean:
            parts = clean.split('|')
            clean = parts[0].strip()
        words = clean.split()
        min_words = 1 if allow_single_word else 2
        if len(words) < min_words or len(words) > 5:
            return False, ""

        # All words must be alphabetic
        name_word_re = re.compile(r"^[A-Za-z\u00C0-\u024F\u0600-\u06FF][A-Za-z\u00C0-\u024F\u0600-\u06FF'\-\.]*$")
        if not all(name_word_re.match(w) for w in words):
            return False, ""

        # Key filter: if ALL words are common English/resume words, it's NOT a name
        words_lower = [w.lower().rstrip('.') for w in words]
        if all(w in NOT_NAME_WORDS for w in words_lower):
            return False, ""

        # Single common words alone are not names (e.g., "Adaptability", "Leadership")
        if len(words) == 1 and words_lower[0] in NOT_NAME_WORDS:
            return False, ""

        return True, clean

    candidates = []

    # ── Strategy 1: Scan first 25 lines for name-like lines ──
    # Some resumes have descriptions/experience before the name (creative PDF layouts)
    for idx, raw_line in enumerate(lines[:25]):
        line = raw_line.strip()
        if is_section_header(line):
            continue
        if is_noise_line(line):
            continue

        is_name, clean_name = is_name_like(line)
        if is_name:
            position_score = 25 - min(idx, 24)
            word_count = len(clean_name.split())
            length_score = 5 if 2 <= word_count <= 3 else (3 if word_count == 4 else 1)
            # Bonus: ALL CAPS names are very likely the candidate name
            if clean_name.isupper() and word_count >= 2:
                length_score += 3
            candidates.append((clean_name.title(), position_score + length_score))

    # ── Strategy 2: Multi-line names ──
    # e.g., "ADNAN ESAM MOHAMMED" line 0, "AHMED GHALEB" line 1
    # or "ROBIN" line 0, "PADUA" line 1, blank, "VILLAREAL" line 3
    for idx in range(min(len(lines), 25)):
        line1 = lines[idx].strip()
        if not line1 or is_section_header(line1) or is_noise_line(line1):
            continue
        is_name1, clean1 = is_name_like(line1, allow_single_word=True)
        if not is_name1:
            continue

        name_parts = [clean1]
        blanks_seen = 0
        look_ahead = min(idx + 6, len(lines))
        for j in range(idx + 1, look_ahead):
            next_line = lines[j].strip()
            if not next_line:
                blanks_seen += 1
                if blanks_seen > 2:
                    break
                continue
            if is_section_header(next_line) or is_noise_line(next_line):
                break
            is_name_j, clean_j = is_name_like(next_line, allow_single_word=True)
            if is_name_j:
                name_parts.append(clean_j)
                blanks_seen = 0
            else:
                break

        if len(name_parts) >= 2:
            combined = ' '.join(name_parts)
            combined_words = combined.split()
            if 2 <= len(combined_words) <= 5:
                position_score = 15 - min(idx, 14)
                # Bonus for ALL CAPS multi-line
                caps_bonus = 3 if all(p.isupper() for p in name_parts) else 0
                candidates.append((combined.title(), position_score + 8 + caps_bonus))

    # ── Strategy 3: Explicit "Name:" label ──
    name_label_match = re.search(r'(?:name|full name)\s*[:\-–]\s*(.+)', text, re.IGNORECASE)
    if name_label_match:
        label_name = name_label_match.group(1).strip()
        label_name = re.sub(r'\s*[|].*$', '', label_name)
        words = label_name.split()
        if 2 <= len(words) <= 4:
            name_word_re = re.compile(r"^[A-Za-z\u00C0-\u024F][A-Za-z\u00C0-\u024F'\-\.]*$")
            if all(name_word_re.match(w) for w in words):
                candidates.append((label_name.title(), 25))

    # ── Strategy 4: NLTK Named Entity Recognition ──
    try:
        usable_lines = []
        for line in lines[:12]:
            stripped = line.strip()
            if stripped and not is_section_header(stripped) and not is_noise_line(stripped):
                usable_lines.append(stripped)
        if usable_lines:
            first_chunk = ' '.join(usable_lines[:6])
            tokens = word_tokenize(first_chunk)
            tagged = nltk.pos_tag(tokens)
            chunks = nltk.ne_chunk(tagged)
            for chunk in chunks:
                if hasattr(chunk, 'label') and chunk.label() == 'PERSON':
                    person_name = ' '.join(c[0] for c in chunk)
                    words = person_name.split()
                    if 2 <= len(words) <= 4:
                        # Verify it's not all common words
                        words_lower = [w.lower() for w in words]
                        if not all(w in NOT_NAME_WORDS for w in words_lower):
                            candidates.append((person_name.title(), 15))
    except Exception:
        pass

    # ── Strategy 5: Spaced-out name lines ──
    # Some PDFs render names as "K I TH  RAI LEY  G." or "M ARAMAG"
    # Scan entire document for spaced-out text that matches the email
    email_for_check = extract_email(text)
    email_local = email_for_check.split('@')[0].lower() if email_for_check else ""

    def collapse_spaced(line_text):
        """Collapse spaced-out text: 'K I TH  RAI LEY  G.' -> 'KITH RAILEY G.'"""
        text_s = line_text.strip()
        tokens = text_s.split()
        single_char_count = sum(1 for t in tokens if len(t) == 1 and t.isalpha())
        if single_char_count >= len(tokens) * 0.3 and single_char_count >= 2:
            groups = re.split(r'\s{2,}', text_s)
            words = []
            for group in groups:
                word = group.replace(' ', '')
                if word:
                    words.append(word)
            if not words:
                words = [text_s.replace(' ', '')]
            return ' '.join(words), True
        return text_s, False

    def try_finalize_spaced_parts(parts):
        """Check if accumulated spaced-out parts form a valid name."""
        if not parts:
            return
        combined = ' '.join(parts)
        words = combined.split()
        if 2 <= len(words) <= 5:
            name_word_re = re.compile(r"^[A-Za-z\u00C0-\u024F][A-Za-z\u00C0-\u024F'\-\.]*$")
            words_lower = [w.lower().rstrip('.') for w in words]
            if all(name_word_re.match(w) for w in words):
                if email_local:
                    match_count = sum(1 for w in words_lower if len(w) > 2 and w in email_local)
                    if match_count >= 1:
                        candidates.append((combined.title(), 18))

    spaced_name_parts = []
    for idx in range(len(lines)):
        line = lines[idx].strip()
        if not line or len(line) < 3:
            try_finalize_spaced_parts(spaced_name_parts)
            spaced_name_parts = []
            continue

        collapsed, is_spaced = collapse_spaced(line)
        collapsed_clean = re.sub(r'^[\s\-–—|:?•·]+|[\s\-–—|:?•·]+$', '', collapsed)

        if is_spaced:
            # Check if it's a section header
            collapsed_lower = collapsed_clean.lower()
            collapsed_no_space = re.sub(r'\s+', '', collapsed_lower)
            if collapsed_lower in SECTION_HEADERS or collapsed_no_space in SECTION_HEADERS:
                try_finalize_spaced_parts(spaced_name_parts)
                spaced_name_parts = []
                continue
            spaced_name_parts.append(collapsed_clean)
        else:
            # Non-spaced line adjacent to spaced parts — might be part of name
            # e.g., "M ARAMAG" (not detected as spaced) after "K I TH  RAI LEY  G." (spaced)
            if spaced_name_parts and len(line.split()) <= 2:
                clean_word = re.sub(r'^[\s\-–—|:?•·]+|[\s\-–—|:?•·]+$', '', line)
                # Also try collapsing spaces in this adjacent line
                clean_collapsed = clean_word.replace(' ', '') if len(clean_word.split()) <= 2 else clean_word
                name_word_re = re.compile(r"^[A-Za-z\u00C0-\u024F][A-Za-z\u00C0-\u024F'\-\.]*$")
                coll_words = clean_collapsed.split()
                if coll_words and all(name_word_re.match(w) for w in coll_words):
                    # Try with collapsed continuation
                    try_finalize_spaced_parts(spaced_name_parts + [clean_collapsed])
                    try_finalize_spaced_parts(spaced_name_parts)
                    spaced_name_parts = []
                    continue
            try_finalize_spaced_parts(spaced_name_parts)
            spaced_name_parts = []
    # Flush remaining
    try_finalize_spaced_parts(spaced_name_parts)

    # ── Strategy 6: Extract name from email as last resort ──
    # Email like "maramagkithrailey@gmail.com" or "john.doe@gmail.com"
    if not candidates:
        email = extract_email(text)
        if email:
            local_part = email.split('@')[0].lower()
            # Handle dot-separated: john.doe -> John Doe
            if '.' in local_part:
                parts = local_part.replace('_', '.').split('.')
                if 2 <= len(parts) <= 3 and all(p.isalpha() and len(p) >= 2 for p in parts):
                    name_from_email = ' '.join(p.capitalize() for p in parts)
                    candidates.append((name_from_email, 5))

    if candidates:
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]

    return "Unknown Candidate"


def extract_email(text):
    """Extract email address from resume text.

    Searches the entire document, handles OCR noise, and picks the best match.
    """
    # Pre-clean OCR artifacts around email patterns
    # Handle cases like "&@ robinvillareal? @gmail.com" or "email : user @gmail.com"
    cleaned_text = text
    # Remove stray spaces around @ sign
    cleaned_text = re.sub(r'\s*@\s*', '@', cleaned_text)
    # Remove common OCR noise characters adjacent to email
    cleaned_text = re.sub(r'[&?!#|\\]', '', cleaned_text)

    # Find all email addresses
    emails = re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', cleaned_text)

    if not emails:
        # Also try the original text in case cleaning was too aggressive
        emails = re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', text)

    if not emails:
        return ""

    # Clean up any remaining noise from found emails
    cleaned_emails = []
    for email in emails:
        # Remove leading/trailing dots or hyphens
        email = email.strip('.-')
        # Validate basic structure
        if re.match(r'^[\w.+-]+@[\w-]+\.\w{2,}', email):
            cleaned_emails.append(email)

    if not cleaned_emails:
        return emails[0] if emails else ""

    if len(cleaned_emails) == 1:
        return cleaned_emails[0]

    # If multiple emails, prefer personal email providers
    personal_domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com',
                        'icloud.com', 'mail.com', 'protonmail.com', 'live.com',
                        'aol.com', 'zoho.com', 'ymail.com', 'me.com']

    for email in cleaned_emails:
        domain = email.split('@')[1].lower()
        if domain in personal_domains:
            return email

    return cleaned_emails[0]


def extract_phone(text):
    """Extract phone number from resume text.

    Handles international formats, parentheses, separators, and unicode prefixes.
    Searches the entire document.
    """
    # Clean common unicode symbols that PDFs insert (phone icons, etc.)
    cleaned = re.sub(r'[?\uf0e0\uf095\u260e\u2706\U0001f4de\U0001f4f1\U0001f4f2\\]', '', text)
    # Normalize various dash types to standard hyphen
    cleaned = re.sub(r'[–—−]', '-', cleaned)

    # Comprehensive phone patterns, ordered from most specific to least
    patterns = [
        # International with parens: (+971) 544758408 or (+971) 54-475-8408
        r'\(\+?\d{1,4}\)[\s\-.]?\d[\d\s\-.]{5,12}\d',
        # International: +971 52 161 1925 or +971-52-161-1925 or +971521611925
        r'\+\d{1,4}[\s\-.]?\d[\d\s\-.]{5,14}\d',
        # Standard with leading zero: 054-358-2924 or 09369364322
        r'\b0\d[\d\s\-.]{6,13}\d\b',
        # Generic: 3+ digits, separators, 7+ total digits
        r'\b\d{3,4}[\s\-.]?\d{3,4}[\s\-.]?\d{3,4}\b',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, cleaned)
        for match in matches:
            digits = re.sub(r'[^\d]', '', match)
            if 7 <= len(digits) <= 15:
                return match.strip()

    return ""


def extract_skills(text):
    """Extract skills from resume text using NLP and keyword matching.

    Uses context-aware matching to avoid false positives:
    - 'C#' won't match 'R' or 'C'
    - Short skills (R, Go, C) require stronger context
    - Skills found in the SKILLS section get priority
    """
    text_lower = text.lower()

    found_skills = []
    seen = set()

    # Skills that need special regex patterns to avoid false positives
    # These are too short or ambiguous for simple substring matching
    SPECIAL_PATTERNS = {
        'c#':   r'\bc\s*#',                    # "C#" or "C #"
        'c++':  r'\bc\s*\+\s*\+',              # "C++" or "C + +"
        'r':    r'(?<![a-z])\br\b(?:\s+(?:programming|language|studio|markdown|shiny)|\s*[,;|/])',
        'go':   r'(?<![a-z])\bgo(?:lang)?\b(?:\s*[,;|/]|\s+(?:programming|language))',
        'c':    r'(?<![a-z#\+])\bc\b(?:\s+(?:programming|language)|\s*[,;|/])',
        'ui':   r'\bui\b(?:\s*[/]\s*ux|\s+design)',
        'ux':   r'\bux\b(?:\s*[/]\s*ui|\s+design|\s+research)',
    }

    # Skills that are safe with word-boundary matching (not too ambiguous)
    WORD_BOUNDARY_SKILLS = {
        'lua', 'dart', 'rust', 'java', 'swift', 'kotlin', 'scala', 'perl',
        'ruby', 'php', 'bash', 'sql', 'html', 'css', 'sass', 'vba',
        'haskell', 'elixir', 'clojure', 'groovy', 'matlab',
    }

    for category, skills in SKILLS_DB.items():
        for skill in skills:
            if skill in seen:
                continue

            matched = False

            if skill in SPECIAL_PATTERNS:
                # Use special context-aware pattern
                pattern = SPECIAL_PATTERNS[skill]
                if re.search(pattern, text_lower):
                    matched = True
            elif skill in WORD_BOUNDARY_SKILLS:
                # Use word-boundary matching
                pattern = r'\b' + re.escape(skill) + r'\b'
                if re.search(pattern, text_lower):
                    matched = True
            else:
                # Standard substring matching for longer/unambiguous skills
                if skill in text_lower:
                    matched = True

            if matched and skill not in seen:
                found_skills.append((skill.title(), category))
                seen.add(skill)

    return found_skills


def extract_education(text):
    """Extract education information from resume text.

    Returns a list of dicts with 'institution' and 'degree' keys.
    Only includes lines that are actual institution names and degree titles,
    not bullet points, coursework descriptions, or other noise.
    """
    education = []
    lines = text.split('\n')
    seen_institutions = set()

    # Keywords that identify institution lines
    INSTITUTION_KEYWORDS = [
        'university', 'college', 'institute', 'school', 'academy',
        'polytechnic', 'conservatory', 'seminary',
    ]

    # Splits a line into logical segments on '|' or runs of 2+ spaces (the
    # latter shows up where a PDF's tab/column layout collapses on extraction)
    SEGMENT_SPLIT_RE = re.compile(r'\s*\|\s*|\s{2,}')

    # Patterns to SKIP — these are NOT institution/degree lines
    SKIP_PATTERNS = re.compile(
        r'(^\s*[\•\-\*\–\◦\▪\uf0d8\uf0b7\®]'  # bullet points
        r'|^relevant\s+coursework'               # coursework listings
        r'|^projects?\s*:'                        # project listings
        r'|^achievement'                          # achievement lines
        r'|^gpa|^grade'                           # GPA lines
        r'|^leader\b|^led\b|^managed\b'          # activity descriptions
        r'|^designed\b|^developed\b|^built\b'     # project descriptions
        r'|^collaborated\b|^implemented\b'        # work descriptions
        r'|^presented\b|^conducted\b'             # activity descriptions
        r'|@|\.com|\.org'                         # email/URL lines
        r'|^\d{4}\s*$'                            # just a year
        r')',
        re.IGNORECASE
    )

    def is_institution_line(line_text):
        """Check if a line is an institution name, not a sentence that mentions one.

        Handles pipe-separated formats like:
        'University of Manchester | BEng (Hons) Software Engineering | Location'
        """
        stripped = line_text.strip()
        line_lower = stripped.lower()

        # Must contain an institution keyword
        if not any(kw in line_lower for kw in INSTITUTION_KEYWORDS):
            return False

        # For pipe- or column-separated lines, check just the institution segment.
        # Runs of 2+ spaces show up where a PDF's tab/column layout collapses
        # during text extraction (e.g. "BEng ... Software Engineering   University of X"),
        # so treat those as segment breaks too, not just '|'.
        check_text = stripped
        segments = [s for s in SEGMENT_SPLIT_RE.split(stripped) if s]
        if len(segments) > 1:
            # Find the segment that contains the institution keyword
            for seg in segments:
                if any(kw in seg.lower() for kw in INSTITUTION_KEYWORDS):
                    check_text = seg
                    break

        check_lower = check_text.lower()
        word_count = len(check_text.split())

        # If the institution segment is very long (>12 words), it's likely a sentence
        if word_count > 12:
            return False

        # If line starts with common sentence starters, it's a description
        if re.match(r'^(a |an |the |i |my |our |we |to |in |at |is |am |was |were |has |had |'
                     r'motivated|detail|science|experienced|seeking|looking|'
                     r'participated|maintained|presented|designed|developed)',
                    check_lower):
            return False

        # Lines with too many lowercase words in sequence are sentences
        words = check_text.split()
        lowercase_words = sum(1 for w in words if w[0].islower() and w not in
                             ('of', 'the', 'and', 'in', 'for', 'at', 'de', 'la', 'al', 'el'))
        if word_count >= 5 and lowercase_words > word_count * 0.5:
            return False

        # Filter out lines that are clearly job titles, roles, or degree labels
        # "College Student", "High School Graduate" are NOT institution names
        if re.search(r'\b(student|engineer|developer|designer|manager|analyst|staff|assistant|intern|graduate|diploma|receptionist)\b',
                    check_lower):
            if word_count <= 3:
                return False

        # Filter out standalone degree labels like "HIGH SCHOOL GRADUATE", "Bachelor of Science"
        degree_only_patterns = [
            r'^high\s+school\s+graduate',
            r'^(bachelor|master|doctor|diploma|associate|btec)',
            r'^(bsc|msc|phd|mba|bca|mca)\b',
        ]
        for dp in degree_only_patterns:
            if re.match(dp, check_lower):
                return False

        return True

    # First pass: find all institution lines
    institution_lines = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or len(stripped) < 5:
            continue
        if SKIP_PATTERNS.search(stripped):
            continue
        if not is_institution_line(stripped):
            continue

        # Clean the institution name
        # For pipe- or column-separated lines like "University of X | BEng Engineering | Location"
        # extract just the institution segment
        segments = [s for s in SEGMENT_SPLIT_RE.split(stripped) if s]
        if len(segments) > 1:
            inst_segment = None
            for seg in segments:
                if any(kw in seg.lower() for kw in INSTITUTION_KEYWORDS):
                    inst_segment = seg
                    break
            clean_inst = inst_segment or segments[0]
        else:
            clean_inst = stripped

        # Remove trailing dates
        clean_inst = re.sub(r'\s*[|,]\s*\d{4}\s*[-–]\s*\d{0,4}\s*$', '', clean_inst)
        clean_inst = re.sub(r'\s*\d{4}\s*[-–]\s*(present|\d{4})\s*$', '', clean_inst, flags=re.IGNORECASE)
        clean_inst = clean_inst.strip().rstrip('|,;: ')
        if clean_inst and clean_inst.lower() not in seen_institutions:
            institution_lines.append((i, clean_inst))
            seen_institutions.add(clean_inst.lower())

    # Degree keywords that need word-boundary matching (short/ambiguous)
    SHORT_DEGREE_KW = {'ba', 'be', 'ma', 'md', 'bsc', 'msc', 'beng', 'meng', 'hnd', 'hnc'}

    def line_has_degree(line_text):
        """Check if a line contains a degree keyword (word-boundary safe)."""
        lower = line_text.lower()
        for deg_kw in DEGREE_KEYWORDS:
            if deg_kw in SHORT_DEGREE_KW:
                # Use word-boundary match for short keywords
                if re.search(r'\b' + re.escape(deg_kw) + r'\b', lower):
                    return True
            else:
                if deg_kw in lower:
                    return True
        return False

    def is_degree_line(line_text):
        """Check if a line is a degree description, not a random sentence."""
        stripped = line_text.strip()
        if not stripped or len(stripped) < 5:
            return False
        if SKIP_PATTERNS.search(stripped):
            return False
        if not line_has_degree(stripped):
            return False
        # Must not be a long descriptive sentence
        if len(stripped.split()) > 15:
            return False
        # Must not start with sentence starters
        lower = stripped.lower()
        if re.match(r'^(a |an |the |i |my |our |we |to |motivated|detail|experienced|seeking|looking)',
                    lower):
            return False
        return True

    # Build index of all institution line positions for proximity checking
    inst_line_indices = set(idx for idx, _ in institution_lines)

    def is_closer_to_other_institution(degree_line_idx, current_inst_idx):
        """Check if a degree line is closer to a different institution than the current one."""
        current_dist = abs(degree_line_idx - current_inst_idx)
        for other_idx in inst_line_indices:
            if other_idx == current_inst_idx:
                continue
            if abs(degree_line_idx - other_idx) < current_dist:
                return True
        return False

    # Second pass: for each institution, find the associated degree
    for inst_idx, institution in institution_lines:
        degree = ""
        # Look within 2 lines above and 3 below for a degree keyword
        search_range = list(range(max(0, inst_idx - 2), min(len(lines), inst_idx + 4)))
        for j in search_range:
            candidate = lines[j].strip()
            if not is_degree_line(candidate):
                continue
            # Don't use the institution line itself as the degree
            if candidate.strip().lower() == institution.lower():
                continue
            # Skip if it's another institution
            if is_institution_line(candidate):
                continue
            # Skip if this degree line is closer to a different institution
            if is_closer_to_other_institution(j, inst_idx):
                continue
            # Clean the degree text
            clean_degree = re.sub(r'\s*[|,]\s*\d{4}\s*[-–]\s*\d{0,4}\s*$', '', candidate)
            clean_degree = re.sub(r'\s*\d{4}\s*[-–]\s*(present|\d{4})\s*$', '', clean_degree, flags=re.IGNORECASE)
            clean_degree = clean_degree.strip().rstrip('|,;: ')
            if clean_degree:
                degree = clean_degree
                break

        # Also check if the degree is embedded in the original line (pipe- or
        # column-separated), e.g. "University of Manchester | BEng (Hons) Software
        # Engineering | Location" or "BEng (Hons) Software Engineering   University of X"
        if not degree:
            original_line = lines[inst_idx].strip()
            segments = [s for s in SEGMENT_SPLIT_RE.split(original_line) if s]
            if len(segments) > 1:
                for seg in segments:
                    # Skip the institution segment itself and location segments
                    if seg.lower() == institution.lower():
                        continue
                    if line_has_degree(seg):
                        degree = seg
                        break

        education.append({
            'institution': institution,
            'degree': degree,
        })

    # Third pass: find degree lines that weren't near any institution
    # (some resumes list degree without mentioning an institution keyword)
    found_degree_lines = set()
    for entry in education:
        if entry['degree']:
            for i, line in enumerate(lines):
                if line.strip() == entry['degree']:
                    found_degree_lines.add(i)

    for i, line in enumerate(lines):
        if i in found_degree_lines:
            continue
        stripped = line.strip()
        if not is_degree_line(stripped):
            continue
        line_lower = stripped.lower()
        # Only standalone degree lines (not inside institution lines already found)
        if any(kw in line_lower for kw in INSTITUTION_KEYWORDS):
            continue
        # Only add if it's clearly a degree line (has specific format)
        if re.search(r'\b(bachelor|master|doctor|diploma|associate|bsc|msc|phd|b\.?eng|m\.?eng|btec)\b', line_lower):
            clean_degree = re.sub(r'\s*[|,]\s*\d{4}\s*[-–]\s*\d{0,4}\s*$', '', stripped)
            clean_degree = clean_degree.strip().rstrip('|,;: ')
            # Check nearby lines for institution
            nearby_inst = ""
            for j in range(max(0, i - 2), min(len(lines), i + 3)):
                if j != i:
                    cand = lines[j].strip()
                    if is_institution_line(cand):
                        nearby_inst = re.sub(r'\s*[|,]\s*\d{4}\s*[-–]\s*\d{0,4}\s*$', '', cand)
                        nearby_inst = nearby_inst.strip().rstrip('|,;: ')
                        break
            if nearby_inst and nearby_inst.lower() not in seen_institutions:
                education.append({
                    'institution': nearby_inst,
                    'degree': clean_degree,
                })
                seen_institutions.add(nearby_inst.lower())

    return education


def extract_experience(text):
    """Extract work experience from resume text."""
    experience = []
    lines = text.split('\n')

    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        for title in JOB_TITLES:
            if title in line_lower:
                job_title = line.strip()
                company = ""
                description = ""
                for j in range(max(0, i - 1), min(len(lines), i + 3)):
                    if j != i:
                        candidate = lines[j].strip()
                        if candidate and not any(t in candidate.lower() for t in JOB_TITLES):
                            if 3 < len(candidate) < 100:
                                company = candidate
                                break
                desc_lines = []
                for j in range(i + 1, min(len(lines), i + 5)):
                    if lines[j].strip().startswith(('•', '-', '*', '–')):
                        desc_lines.append(lines[j].strip())
                description = ' '.join(desc_lines)
                experience.append((job_title, company, description))
                break

    return experience


def calculate_scores(text, skills, education, experience):
    """Calculate resume scores with detailed explanations for each dimension."""
    scores = {}
    explanations = {}

    # ===== Skills Score (0-100) =====
    skill_count = len(skills)
    categories = set(cat for _, cat in skills)
    skills_reasons = []
    skills_suggestions = []

    if skill_count >= 15:
        scores['skills'] = 100
        skills_reasons.append(f"Excellent: {skill_count} skills detected across your resume.")
    elif skill_count >= 10:
        scores['skills'] = 85
        skills_reasons.append(f"Very good: {skill_count} skills found. Adding {15 - skill_count} more would reach a perfect score.")
        skills_suggestions.append("List additional tools, frameworks, or certifications you have experience with.")
    elif skill_count >= 6:
        scores['skills'] = 70
        skills_reasons.append(f"Good: {skill_count} skills detected, but there is room for improvement.")
        skills_suggestions.append("Add more specific technical skills — e.g., programming languages, frameworks, or tools you use regularly.")
    elif skill_count >= 3:
        scores['skills'] = 50
        skills_reasons.append(f"Below average: only {skill_count} skills were found.")
        skills_suggestions.append("Create a dedicated 'Skills' section and list all relevant technical and soft skills.")
        skills_suggestions.append("Include programming languages, frameworks, databases, and tools you are proficient in.")
    else:
        scores['skills'] = max(20, skill_count * 15)
        skills_reasons.append(f"Low: only {skill_count} skill(s) detected. Your resume may be missing a skills section.")
        skills_suggestions.append("Add a clear 'Skills' or 'Technical Skills' section at the top of your resume.")
        skills_suggestions.append("Even non-technical roles benefit from listing tools (Excel, SQL, Tableau, etc.).")

    if len(categories) >= 4:
        scores['skills'] = min(100, scores['skills'] + 10)
        skills_reasons.append(f"Bonus: skills span {len(categories)} categories, showing a well-rounded profile.")
    elif len(categories) < 2 and skill_count > 0:
        skills_suggestions.append("Diversify your skills — include soft skills (leadership, communication) alongside technical ones.")

    explanations['skills'] = {'reasons': skills_reasons, 'suggestions': skills_suggestions}

    # ===== Education Score (0-100) =====
    edu_reasons = []
    edu_suggestions = []
    text_lower = text.lower()

    if not education:
        scores['education'] = 20
        edu_reasons.append("No education entries were detected in your resume.")
        edu_suggestions.append("Add an 'Education' section with your degree, institution name, and graduation year.")
        edu_suggestions.append("If you have certifications (AWS, Google, Coursera, etc.), list them too.")
    else:
        if any(kw in text_lower for kw in ['ph.d', 'phd', 'doctorate']):
            scores['education'] = 100
            edu_reasons.append("Doctorate/PhD detected — highest academic qualification.")
        elif any(kw in text_lower for kw in ['master', 'm.sc', 'msc', 'm.tech', 'mba', 'mca']):
            scores['education'] = 85
            edu_reasons.append("Master's degree detected — strong academic background.")
            edu_suggestions.append("Adding relevant certifications or publications can push this to a perfect score.")
        elif any(kw in text_lower for kw in ['bachelor', 'b.sc', 'bsc', 'b.tech', 'b.e.', 'bca']):
            scores['education'] = 70
            edu_reasons.append("Bachelor's degree detected.")
            edu_suggestions.append("Consider pursuing certifications or a master's degree to strengthen this section.")
            edu_suggestions.append("Include relevant coursework, GPA (if strong), or academic projects.")
        elif any(kw in text_lower for kw in ['diploma', 'associate']):
            scores['education'] = 50
            edu_reasons.append("Diploma or associate degree detected.")
            edu_suggestions.append("Highlight any additional certifications, bootcamps, or online courses you've completed.")
        else:
            scores['education'] = 40
            edu_reasons.append("Education found but degree level could not be clearly determined.")
            edu_suggestions.append("Clearly state your degree type (e.g., 'Bachelor of Science in Computer Science').")

        # Check for institution names
        has_institution = any(entry.get('institution') for entry in education)
        if not has_institution:
            edu_suggestions.append("Include the name of your university or institution for credibility.")

    explanations['education'] = {'reasons': edu_reasons, 'suggestions': edu_suggestions}

    # ===== Experience Score (0-100) =====
    exp_count = len(experience)
    exp_reasons = []
    exp_suggestions = []

    if exp_count >= 5:
        scores['experience'] = 100
        exp_reasons.append(f"Excellent: {exp_count} work experience entries found.")
    elif exp_count >= 3:
        scores['experience'] = 80
        exp_reasons.append(f"Good: {exp_count} experience entries detected.")
        exp_suggestions.append("Adding more roles, freelance work, or internships would strengthen this section.")
    elif exp_count >= 1:
        scores['experience'] = 60
        exp_reasons.append(f"Fair: only {exp_count} experience entry/entries found.")
        exp_suggestions.append("Include internships, freelance projects, open-source contributions, or volunteer work.")
        exp_suggestions.append("Add bullet points with specific achievements and metrics (e.g., 'Increased performance by 30%').")
    else:
        scores['experience'] = 20
        exp_reasons.append("No work experience entries were detected.")
        exp_suggestions.append("Add a 'Work Experience' or 'Professional Experience' section with job titles and company names.")
        exp_suggestions.append("Even academic projects or personal projects can be listed under 'Projects' if you lack work experience.")

    # Check for years of experience mentions
    year_match = re.findall(r'(\d+)\+?\s*years?', text, re.IGNORECASE)
    if year_match:
        max_years = max(int(y) for y in year_match)
        if max_years >= 10:
            scores['experience'] = min(100, scores['experience'] + 20)
            exp_reasons.append(f"Bonus: {max_years}+ years of experience mentioned.")
        elif max_years >= 5:
            scores['experience'] = min(100, scores['experience'] + 10)
            exp_reasons.append(f"Bonus: {max_years}+ years of experience mentioned.")

    # Check for bullet points in experience
    bullet_count = sum(1 for line in text.split('\n') if line.strip().startswith(('•', '-', '*', '–')))
    if bullet_count < 3 and exp_count > 0:
        exp_suggestions.append("Use bullet points to describe your responsibilities and achievements for each role.")

    explanations['experience'] = {'reasons': exp_reasons, 'suggestions': exp_suggestions}

    # ===== Formatting Score (0-100) =====
    formatting_score = 50
    fmt_reasons = []
    fmt_suggestions = []
    word_count = len(text.split())
    sentences = sent_tokenize(text)

    # Length check
    if 300 <= word_count <= 1500:
        formatting_score += 15
        fmt_reasons.append(f"Good length: {word_count} words (ideal range is 300-1500).")
    elif 200 <= word_count <= 2000:
        formatting_score += 8
        fmt_reasons.append(f"Acceptable length: {word_count} words.")
        if word_count < 300:
            fmt_suggestions.append(f"Your resume is a bit short ({word_count} words). Aim for at least 300 words with detailed descriptions.")
        else:
            fmt_suggestions.append(f"Your resume is slightly long ({word_count} words). Try to keep it under 1500 words (1-2 pages).")
    else:
        if word_count < 200:
            fmt_reasons.append(f"Very short: only {word_count} words detected.")
            fmt_suggestions.append("Your resume needs more content. Add detailed descriptions of your skills, experience, and projects.")
        else:
            fmt_reasons.append(f"Very long: {word_count} words detected.")
            fmt_suggestions.append("Trim your resume to 1-2 pages. Focus on the most relevant and recent experience.")

    # Section headers
    section_headers = ['education', 'experience', 'skills', 'projects',
                       'summary', 'objective', 'certifications', 'achievements']
    found_sections = [s for s in section_headers if s in text_lower]
    missing_sections = [s for s in ['education', 'experience', 'skills'] if s not in text_lower]
    formatting_score += min(20, len(found_sections) * 5)

    if found_sections:
        fmt_reasons.append(f"Sections found: {', '.join(s.title() for s in found_sections)}.")
    if missing_sections:
        fmt_suggestions.append(f"Missing key sections: {', '.join(s.title() for s in missing_sections)}. Add clear section headers.")

    # Bullet points
    if bullet_count >= 5:
        formatting_score += 10
        fmt_reasons.append(f"Good use of bullet points ({bullet_count} found).")
    elif bullet_count >= 2:
        formatting_score += 5
        fmt_reasons.append(f"Some bullet points found ({bullet_count}).")
        fmt_suggestions.append("Use more bullet points to list responsibilities and achievements for better readability.")
    else:
        fmt_suggestions.append("Add bullet points to your experience section. Recruiters scan resumes quickly — bullets help.")

    # Contact info
    has_email = bool(extract_email(text))
    has_phone = bool(extract_phone(text))
    if has_email:
        formatting_score += 5
    else:
        fmt_suggestions.append("Include your email address so recruiters can contact you.")
    if not has_phone:
        fmt_suggestions.append("Consider adding a phone number for easier contact.")

    if has_email and has_phone:
        fmt_reasons.append("Contact information (email and phone) is present.")
    elif has_email:
        fmt_reasons.append("Email found, but no phone number detected.")

    scores['formatting'] = min(100, formatting_score)
    explanations['formatting'] = {'reasons': fmt_reasons, 'suggestions': fmt_suggestions}

    # ===== Overall Score =====
    scores['overall'] = round(
        scores['skills'] * 0.30 +
        scores['education'] * 0.20 +
        scores['experience'] * 0.30 +
        scores['formatting'] * 0.20
    )

    return scores, explanations


def recommend_field(skills, experience, text):
    """Recommend career fields based on actual skills, experience, and education.

    Scoring approach:
    - Core skills: 4 points each (strongest signal from detected skills)
    - Supporting skills: 1 point each (only if there's at least 1 core skill match)
    - Experience keywords: 5 points each (matched against job titles only, not full text)
    - Education context: 3 points (if degree/education text mentions the field)

    Returns a list of (field_name, confidence, matched_details) sorted by confidence.
    """
    if not skills and not experience:
        return [('General', 0, 'No skills or experience detected to determine a specific field.')]

    skill_names = set(s.lower() for s, _ in skills)

    # Build experience text from actual job titles only (not descriptions)
    # Job titles are the first element of experience tuples
    exp_titles = ' | '.join(title for title, _, _ in experience).lower()

    # Extract education-related text for field context
    edu_keywords_in_text = set()
    text_lower = text.lower()
    # Look specifically in lines near education section headers
    lines = text.split('\n')
    in_edu_section = False
    edu_text = ""
    for line in lines:
        stripped = line.strip().lower()
        if stripped in ('education', 'academic background', 'qualifications'):
            in_edu_section = True
            continue
        if in_edu_section:
            if stripped in ('experience', 'skills', 'projects', 'certifications',
                           'work experience', 'professional experience', 'references'):
                in_edu_section = False
                continue
            edu_text += " " + stripped

    field_results = []

    for field, config in FIELD_RECOMMENDATIONS.items():
        score = 0
        matched_core = []
        matched_supporting = []
        matched_experience = []
        matched_education = []

        # Core skills — worth 4 points each (strongest signal)
        for kw in config['core']:
            if kw in skill_names:
                score += 4
                matched_core.append(kw.title())

        # Supporting skills — worth 1 point each
        # BUT only count if there's at least 1 core skill or experience match
        supporting_matches = []
        for kw in config['supporting']:
            if kw in skill_names:
                supporting_matches.append(kw.title())

        # Experience keywords — worth 5 points each
        # Match against job titles and the broader text, but use word boundaries
        # to avoid false matches (e.g., "engineer" in a sentence about something else)
        for kw in config['experience_keywords']:
            # Match in job title lines (high confidence)
            if kw in exp_titles:
                score += 5
                matched_experience.append(kw.title())
            else:
                # Match in full text but require it to be near a job context
                # Use word-boundary matching for multi-word phrases
                pattern = r'\b' + re.escape(kw) + r'\b'
                if re.search(pattern, text_lower):
                    score += 3
                    matched_experience.append(kw.title())

        # Education context — worth 3 points
        # Check if the education section mentions this field
        field_edu_keywords = {
            'Web Development': ['web development', 'web design', 'internet technology'],
            'Data Science & AI': ['data science', 'artificial intelligence', 'machine learning',
                                  'statistics', 'data analytics'],
            'Software Engineering': ['software engineering', 'computer science', 'computing',
                                     'information technology', 'software development'],
            'Mechanical Engineering': ['mechanical engineering', 'mechatronics',
                                      'manufacturing engineering', 'engineering technology'],
            'Electrical & Electronics Engineering': ['electrical engineering', 'electronics',
                                                      'electronic engineering', 'power engineering',
                                                      'telecommunications engineering'],
            'Civil Engineering': ['civil engineering', 'structural engineering',
                                   'construction management', 'geotechnical engineering',
                                   'environmental engineering'],
            'Aerospace & Aviation': ['aerospace engineering', 'aerospace', 'aviation',
                                      'aircraft maintenance', 'aeronautical engineering'],
            'Chemical & Industrial Engineering': ['chemical engineering', 'industrial engineering',
                                                    'process engineering', 'petroleum engineering'],
            'Accounting & Finance': ['accountancy', 'accounting', 'finance', 'business administration',
                                     'business management', 'economics', 'financial'],
            'Customer Service & Hospitality': ['hospitality', 'tourism', 'hotel management',
                                                'culinary', 'food service'],
            'Marketing & Communications': ['marketing', 'communications', 'journalism',
                                           'public relations', 'advertising', 'media studies'],
            'Education & Training': ['education', 'teaching', 'pedagogy', 'instructional design'],
            'Business Administration': ['business administration', 'management', 'mba',
                                        'organizational management'],
            'Nursing & Patient Care': ['nursing', 'nurse', 'healthcare', 'midwifery',
                                        'patient care', 'clinical nursing'],
            'Medicine & Healthcare': ['medicine', 'medical', 'surgery', 'mbbs',
                                       'clinical medicine', 'biomedical', 'public health'],
            'Pharmacy': ['pharmacy', 'pharmaceutical', 'pharmacology',
                          'pharmaceutical science'],
            'Dentistry': ['dentistry', 'dental surgery', 'dental science',
                           'oral health'],
            'Psychology & Counseling': ['psychology', 'counseling', 'behavioral science',
                                         'clinical psychology', 'social psychology'],
            'Law & Legal': ['law', 'legal studies', 'jurisprudence', 'llb',
                             'criminal justice', 'political science'],
            'Human Resources': ['human resource', 'hr management', 'organizational behavior',
                                 'labor relations', 'industrial relations'],
            'Sales & Retail': ['sales', 'retail management', 'business development',
                                'commercial studies'],
            'Logistics & Supply Chain': ['logistics', 'supply chain', 'operations management',
                                          'transportation', 'shipping management'],
            'Architecture & Interior Design': ['architecture', 'interior design',
                                                'landscape architecture', 'urban planning',
                                                'architectural engineering'],
            'Media & Journalism': ['journalism', 'mass communication', 'media studies',
                                    'broadcasting', 'film studies', 'media production'],
            'Graphic Design & Creative Arts': ['graphic design', 'fine arts', 'visual arts',
                                                'multimedia', 'animation', 'creative arts'],
            'Real Estate & Property': ['real estate', 'property management',
                                        'estate management', 'land management'],
            'Banking & Financial Services': ['banking', 'finance', 'financial services',
                                              'investment', 'insurance', 'actuarial science'],
            'IT Support & Systems Administration': ['information technology', 'computer science',
                                                      'network engineering', 'it management'],
            'Social Work & Community Services': ['social work', 'community development',
                                                   'human services', 'social science'],
            'Agriculture & Environmental Science': ['agriculture', 'environmental science',
                                                      'forestry', 'marine biology', 'ecology',
                                                      'horticulture', 'animal science'],
            'Culinary Arts & Food Industry': ['culinary arts', 'food technology',
                                                'hospitality', 'hotel management',
                                                'food science', 'nutrition'],
            'Transportation & Shipping': ['maritime', 'marine engineering', 'shipping',
                                            'naval architecture', 'transportation'],
            'Government & Public Administration': ['public administration', 'political science',
                                                     'governance', 'public policy',
                                                     'international relations'],
            'Research & Academia': ['research', 'scientific research', 'phd',
                                     'doctoral', 'academic research'],
            'Fitness & Sports': ['sports science', 'physical education', 'kinesiology',
                                  'exercise science', 'sports management'],
            'Fashion & Beauty': ['fashion design', 'textile design', 'cosmetology',
                                  'beauty therapy', 'fashion merchandising'],
            'Telecommunications': ['telecommunications', 'communication engineering',
                                    'electronic communication', 'network engineering'],
        }
        for edu_kw in field_edu_keywords.get(field, []):
            if edu_kw in edu_text or edu_kw in text_lower:
                score += 3
                matched_education.append(edu_kw.title())
                break  # Only count education bonus once per field

        # Only add supporting skill points if there's already some core/experience signal
        if matched_core or matched_experience or matched_education:
            for kw_title in supporting_matches:
                score += 1
                matched_supporting.append(kw_title)

        if score > 0:
            # Build explanation
            details = []
            if matched_core:
                details.append(f"Core skills: {', '.join(matched_core)}")
            if matched_supporting:
                details.append(f"Supporting skills: {', '.join(matched_supporting)}")
            if matched_experience:
                details.append(f"Experience match: {', '.join(matched_experience)}")
            if matched_education:
                details.append(f"Education: {', '.join(matched_education)}")
            field_results.append((field, score, '; '.join(details)))

    if not field_results:
        return [('General', 0, 'Your skill set does not strongly match a specific field. Consider adding more domain-specific skills.')]

    # Sort by score descending
    field_results.sort(key=lambda x: x[1], reverse=True)

    # Calculate confidence as percentage relative to max possible
    max_score = field_results[0][1]
    results_with_confidence = []
    for field, score, details in field_results[:3]:  # Top 3
        confidence = min(100, round((score / max(max_score, 1)) * 100))
        results_with_confidence.append((field, confidence, details))

    return results_with_confidence


def generate_recommendations(scores, explanations, skills, education, experience, text):
    """Generate improvement recommendations from score explanations."""
    recommendations = []

    # Collect all suggestions from score explanations
    for category in ['skills', 'education', 'experience', 'formatting']:
        for suggestion in explanations.get(category, {}).get('suggestions', []):
            recommendations.append(suggestion)

    # Additional cross-cutting recommendations
    categories = set(cat for _, cat in skills)
    if 'Soft Skills' not in categories and skills:
        recommendations.append(
            "Include soft skills such as leadership, communication, and teamwork "
            "to make your profile well-rounded."
        )

    if not recommendations:
        recommendations.append(
            "Great resume! Keep it updated with your latest projects and skills."
        )

    return recommendations


def _cross_validate_name(extracted_name, file_path, email, text):
    """Cross-validate the extracted name against the filename and email.

    If the extracted name doesn't match the filename at all, but the filename
    contains what looks like a real name, prefer the filename-derived name.
    Also use the email local part as a secondary signal.
    """
    # Extract name hints from filename
    # e.g., "Rodson_Napoleon_Ubaldo_-_CV.pdf" -> ["rodson", "napoleon", "ubaldo"]
    basename = os.path.splitext(os.path.basename(file_path))[0]
    # Remove common suffixes/prefixes
    cleaned_filename = re.sub(
        r'[_\-\s]*(cv|resume|r[eé]sum[eé]|curriculum[_\s]*vitae|final|draft|'
        r'updated|new|old|v\d+|copy|\d+)[_\-\s]*',
        ' ', basename, flags=re.IGNORECASE
    )
    # Split by underscores, hyphens, spaces
    filename_parts = [p.strip() for p in re.split(r'[_\-\s]+', cleaned_filename) if p.strip()]
    # Filter out non-name parts (numbers, single chars, common words)
    filename_name_parts = [
        p for p in filename_parts
        if len(p) >= 2 and p.isalpha() and p.lower() not in {
            'cv', 'resume', 'final', 'draft', 'updated', 'new', 'old', 'copy',
            'doc', 'pdf', 'file', 'document', 'the', 'and', 'for', 'rev',
        }
    ]

    # Extract name hints from email
    email_name_parts = []
    if email:
        local = email.split('@')[0].lower()
        # Split by dots, underscores, or detect camelCase
        parts = re.split(r'[._\-]', local)
        email_name_parts = [p for p in parts if p.isalpha() and len(p) >= 2]

    # Check if extracted name matches the filename
    if extracted_name and extracted_name != "Unknown Candidate":
        name_words = [w.lower() for w in extracted_name.split()]
        filename_words = [w.lower() for w in filename_name_parts]

        # If at least one word from the extracted name matches the filename, it's validated
        if filename_words:
            overlap = sum(1 for w in name_words if any(fw.startswith(w[:3]) or w.startswith(fw[:3])
                         for fw in filename_words))
            if overlap >= 1:
                return extracted_name  # Name matches filename — confident

        # If no filename match, check against email
        if email_name_parts:
            email_overlap = sum(1 for w in name_words if any(
                ep.startswith(w[:3].lower()) or w.lower().startswith(ep[:3])
                for ep in email_name_parts
            ))
            if email_overlap >= 1:
                return extracted_name  # Name matches email — confident

    # If extracted name is "Unknown Candidate" or doesn't match filename/email,
    # try to build a name from the filename
    if len(filename_name_parts) >= 2:
        # Verify these filename parts look like name parts (not random words)
        # Cross-check against email
        filename_candidate = ' '.join(p.title() for p in filename_name_parts)
        if email_name_parts:
            fn_lower = [p.lower() for p in filename_name_parts]
            email_match = sum(1 for p in fn_lower if any(
                ep.startswith(p[:3]) or p.startswith(ep[:3]) for ep in email_name_parts
            ))
            if email_match >= 1:
                return filename_candidate

        # Even without email match, if filename has 2-4 name-like parts, use it
        if 2 <= len(filename_name_parts) <= 4:
            # But only if extracted name was clearly wrong (Unknown or doesn't match anything)
            if extracted_name == "Unknown Candidate" or (
                extracted_name and not any(
                    w.lower() in [ep.lower() for ep in email_name_parts]
                    for w in extracted_name.split()
                ) and email_name_parts
            ):
                return filename_candidate

    return extracted_name


def analyse_resume(file_path):
    """Main function: analyse a resume (PDF or image) and return all extracted data."""
    # Step 1: Extract text (supports PDF and images)
    text = extract_text(file_path)

    if not text.strip():
        has_ocr = _has_tesseract()
        ext = os.path.splitext(file_path)[1].lower()
        if ext in IMAGE_EXTENSIONS:
            if not has_ocr:
                return {
                    'error': 'Tesseract OCR is not installed. To scan images, install Tesseract from: '
                             'https://github.com/UB-Mannheim/tesseract/wiki — then restart the server. '
                             'Alternatively, upload a text-based PDF instead.'
                }
            return {
                'error': 'Could not extract text from the image. The image may be too blurry or low resolution. '
                         'Try uploading a clearer image or a PDF version instead.'
            }
        if not has_ocr:
            return {
                'error': 'This PDF appears to be scanned or image-only, and Tesseract OCR is not installed. '
                         'To support scanned PDFs, install Tesseract from: '
                         'https://github.com/UB-Mannheim/tesseract/wiki — then restart the server. '
                         'Alternatively, upload a text-based PDF (created from Word, Google Docs, etc.).'
            }
        return {
            'error': 'Could not extract text from the PDF. The file may be corrupted or contain only images '
                     'that could not be read. Try uploading a different version of your resume.'
        }

    # Step 2: Extract information
    name = extract_name(text)
    email = extract_email(text)
    phone = extract_phone(text)

    # Cross-validate name against filename and email for extra confidence
    name = _cross_validate_name(name, file_path, email, text)
    skills = extract_skills(text)
    education = extract_education(text)
    experience = extract_experience(text)

    # Step 3: Calculate scores with explanations
    scores, explanations = calculate_scores(text, skills, education, experience)

    # Step 4: Recommend career fields (improved)
    field_recommendations = recommend_field(skills, experience, text)
    primary_field = field_recommendations[0][0] if field_recommendations else 'General IT'

    # Step 5: Generate recommendations
    recommendations = generate_recommendations(scores, explanations, skills, education, experience, text)

    # Step 6: ATS Simulation
    ats_results = simulate_ats(text, skills, education, experience, scores)

    # Step 7: Career fit roles
    career_roles = suggest_career_roles(skills, experience, education, text)

    # Step 8: Employer summary
    employer_summary = generate_employer_summary(
        name, skills, education, experience, scores, field_recommendations
    )

    return {
        'name': name,
        'email': email,
        'phone': phone,
        'raw_text': text,
        'skills': skills,
        'education': education,
        'experience': experience,
        'scores': scores,
        'explanations': explanations,
        'recommended_field': primary_field,
        'field_recommendations': field_recommendations,
        'recommendations': recommendations,
        'ats_results': ats_results,
        'career_roles': career_roles,
        'employer_summary': employer_summary,
    }


# ---------------------------------------------------------------------------
# Feature 1 & 7: Context-Aware Personalized Feedback / Resume Personalization
# ---------------------------------------------------------------------------

def generate_personalized_feedback(resume_data, career_goal='', experience_level='', target_role=''):
    """Generate tailored feedback based on the user's career goals, experience level, and target role.

    Also serves Feature 7 (Enhanced Resume Personalization) by providing
    role-specific customization suggestions.
    """
    skills = resume_data.get('skills', [])
    education = resume_data.get('education', [])
    experience = resume_data.get('experience', [])
    scores = resume_data.get('scores', {})
    text = resume_data.get('raw_text', '')
    text_lower = text.lower()

    skill_names = set(s.lower() for s, _ in skills) if skills else set()
    feedback = {
        'experience_level_assessment': '',
        'career_alignment': [],
        'strengths': [],
        'gaps': [],
        'action_items': [],
        'personalization_tips': [],
    }

    # --- Determine experience level ---
    exp_level = experience_level.lower() if experience_level else ''
    if not exp_level:
        # Auto-detect from resume
        exp_count = len(experience)
        has_degree = any(
            entry.get('degree', '') for entry in education
        ) if isinstance(education, list) and education else False

        if exp_count == 0:
            exp_level = 'entry'
        elif exp_count <= 2:
            exp_level = 'junior'
        elif exp_count <= 5:
            exp_level = 'mid'
        else:
            exp_level = 'senior'

    level_labels = {
        'entry': 'Entry-Level / Student',
        'junior': 'Junior Professional (0-2 years)',
        'mid': 'Mid-Level Professional (2-5 years)',
        'senior': 'Senior Professional (5+ years)',
    }
    feedback['experience_level_assessment'] = level_labels.get(exp_level, 'Not determined')

    # --- Tailored feedback by experience level ---
    if exp_level == 'entry':
        if scores.get('skills', 0) < 60:
            feedback['gaps'].append(
                'As an entry-level candidate, focus on listing all technical skills you learned '
                'in school, personal projects, and online courses — even basics like Microsoft Office or Google Suite.'
            )
        if scores.get('experience', 0) < 50:
            feedback['gaps'].append(
                'Include internships, volunteer work, university projects, and part-time jobs. '
                'Entry-level employers value any form of work experience.'
            )
        feedback['action_items'].append(
            'Create a "Projects" section highlighting class or personal projects with the technologies used.'
        )
        feedback['action_items'].append(
            'Add relevant coursework that aligns with your target role.'
        )
    elif exp_level == 'junior':
        if scores.get('skills', 0) < 70:
            feedback['gaps'].append(
                'Expand your skills section — junior roles benefit from showing breadth of knowledge.'
            )
        feedback['action_items'].append(
            'Quantify your achievements: "Increased efficiency by 20%" is stronger than "Improved processes."'
        )
    elif exp_level in ('mid', 'senior'):
        if scores.get('skills', 0) < 80:
            feedback['gaps'].append(
                'At your level, employers expect specialized expertise. Highlight advanced skills and certifications.'
            )
        feedback['action_items'].append(
            'Lead with impact metrics: revenue generated, team size managed, systems scaled.'
        )
        feedback['action_items'].append(
            'Consider adding a "Key Achievements" section at the top of your resume.'
        )

    # --- Strengths ---
    for key in ['skills', 'education', 'experience', 'formatting']:
        score_val = scores.get(key, 0)
        if score_val >= 80:
            feedback['strengths'].append(f'Your {key} section is strong (scored {score_val}/100).')

    if len(skill_names) >= 10:
        feedback['strengths'].append(f'Good skill diversity with {len(skill_names)} skills detected.')

    # --- Career goal alignment ---
    if career_goal:
        career_goal_lower = career_goal.lower()
        # Check if skills align with career goal
        goal_skill_map = {
            'web': ['html', 'css', 'javascript', 'react', 'angular', 'vue', 'node.js',
                     'django', 'flask', 'next.js', 'typescript'],
            'data': ['python', 'pandas', 'numpy', 'machine learning', 'data analysis',
                      'tableau', 'power bi', 'sql', 'statistics'],
            'mobile': ['react native', 'flutter', 'android', 'ios', 'swift', 'kotlin'],
            'cloud': ['aws', 'azure', 'docker', 'kubernetes', 'devops', 'terraform'],
            'security': ['security', 'penetration testing', 'firewall', 'encryption'],
            'management': ['leadership', 'project management', 'agile', 'scrum', 'communication'],
        }
        matched_goal = None
        for goal_key, goal_skills in goal_skill_map.items():
            if goal_key in career_goal_lower:
                matched_goal = goal_key
                found = [s for s in goal_skills if s in skill_names]
                missing = [s for s in goal_skills if s not in skill_names][:5]
                if found:
                    feedback['career_alignment'].append(
                        f'Your skills match your "{career_goal}" goal: {", ".join(s.title() for s in found)}.'
                    )
                if missing:
                    feedback['gaps'].append(
                        f'To strengthen your "{career_goal}" profile, consider learning: '
                        f'{", ".join(s.title() for s in missing)}.'
                    )
                break

        if not matched_goal:
            feedback['career_alignment'].append(
                f'Goal noted: "{career_goal}". Focus on acquiring industry-specific certifications '
                f'and gaining relevant experience in this area.'
            )

    # --- Target role personalization (Feature 7) ---
    if target_role:
        feedback['personalization_tips'].append(
            f'For a "{target_role}" position, place your most relevant experience and skills first.'
        )
        target_lower = target_role.lower()
        # Check for keyword gaps
        role_keywords = {
            'software engineer': ['algorithms', 'data structures', 'git', 'testing', 'agile'],
            'data analyst': ['sql', 'excel', 'tableau', 'power bi', 'data visualization'],
            'web developer': ['html', 'css', 'javascript', 'react', 'responsive design'],
            'project manager': ['agile', 'scrum', 'stakeholder management', 'budgeting'],
            'ux designer': ['figma', 'user research', 'wireframe', 'prototype', 'usability'],
        }
        for role_key, role_skills in role_keywords.items():
            if role_key in target_lower:
                missing = [s for s in role_skills if s not in skill_names]
                if missing:
                    feedback['personalization_tips'].append(
                        f'Consider adding these keywords for ATS compatibility: '
                        f'{", ".join(s.title() for s in missing)}.'
                    )
                break

        feedback['personalization_tips'].append(
            f'Tailor your summary/objective to mention "{target_role}" specifically.'
        )
        feedback['personalization_tips'].append(
            'Reorder your bullet points so the most relevant achievements appear first.'
        )

    # General action items
    if not feedback['action_items']:
        feedback['action_items'].append('Keep your resume updated with your latest accomplishments.')

    return feedback


# ---------------------------------------------------------------------------
# Feature 2: Advanced ATS Simulation with Transparency
# ---------------------------------------------------------------------------

def simulate_ats(text, skills, education, experience, scores):
    """Simulate an Applicant Tracking System scan and report findings.

    Checks for:
    - Required sections (Contact, Summary, Skills, Education, Experience)
    - Formatting issues (special characters, tables, images)
    - Readability and structure
    - Keyword density
    - ATS compatibility score
    """
    text_lower = text.lower()
    lines = text.split('\n')

    results = {
        'ats_score': 0,
        'sections_found': [],
        'sections_missing': [],
        'formatting_issues': [],
        'readability': {},
        'keyword_analysis': {},
        'pass_likely': False,
    }

    # --- Section Detection ---
    required_sections = {
        'Contact Information': ['email', 'phone', '@', 'tel:', 'mobile'],
        'Summary / Objective': ['summary', 'objective', 'profile', 'about me', 'professional summary'],
        'Skills': ['skills', 'technical skills', 'core competencies', 'key skills'],
        'Education': ['education', 'academic', 'qualifications', 'degree'],
        'Experience': ['experience', 'work history', 'employment', 'professional experience'],
    }

    section_score = 0
    for section_name, keywords in required_sections.items():
        found = any(kw in text_lower for kw in keywords)
        if found:
            results['sections_found'].append(section_name)
            section_score += 20
        else:
            results['sections_missing'].append(section_name)

    # --- Formatting Issues ---
    # Check for special/problematic characters
    special_chars = re.findall(r'[\uf0d8\uf0b7\uf0e0\uf095\u2022\u25cf\u25cb\u25aa\u25ab]', text)
    if len(special_chars) > 5:
        results['formatting_issues'].append({
            'issue': 'Special Unicode Characters Detected',
            'detail': f'Found {len(special_chars)} special characters that may not parse correctly in ATS systems.',
            'fix': 'Replace fancy bullet points with standard dashes (-) or asterisks (*).',
            'severity': 'medium',
        })

    # Check line length (very long lines suggest table/column layouts)
    long_lines = [l for l in lines if len(l.strip()) > 120]
    if len(long_lines) > 5:
        results['formatting_issues'].append({
            'issue': 'Complex Layout Detected',
            'detail': f'{len(long_lines)} lines exceed 120 characters, suggesting multi-column or table layout.',
            'fix': 'Use a single-column layout. ATS systems read left-to-right and may scramble multi-column content.',
            'severity': 'high',
        })

    # Check for excessive blank lines (poor structure)
    blank_count = sum(1 for l in lines if not l.strip())
    if blank_count > len(lines) * 0.4:
        results['formatting_issues'].append({
            'issue': 'Excessive Blank Lines',
            'detail': f'{blank_count} out of {len(lines)} lines are blank ({round(blank_count/max(len(lines),1)*100)}%).',
            'fix': 'Remove unnecessary blank lines to improve information density.',
            'severity': 'low',
        })

    # Check for header/footer noise
    if re.search(r'page\s+\d+\s*(of\s+\d+)?', text_lower):
        results['formatting_issues'].append({
            'issue': 'Page Numbers Detected',
            'detail': 'Page numbers can confuse ATS parsers.',
            'fix': 'Remove headers and footers including page numbers from your resume.',
            'severity': 'low',
        })

    # Check for images/graphics mention
    if not text.strip() or len(text.strip()) < 100:
        results['formatting_issues'].append({
            'issue': 'Minimal Text Content',
            'detail': 'Very little text was extracted. Resume may be image-heavy or use graphics for text.',
            'fix': 'Use actual text instead of images. ATS cannot read text embedded in images.',
            'severity': 'high',
        })

    # --- Readability Analysis ---
    words = text.split()
    word_count = len(words)
    sentence_count = len(re.findall(r'[.!?]+', text)) or 1
    avg_sentence_len = word_count / sentence_count

    results['readability'] = {
        'word_count': word_count,
        'line_count': len(lines),
        'avg_sentence_length': round(avg_sentence_len, 1),
    }

    # Word count assessment
    if word_count < 150:
        results['formatting_issues'].append({
            'issue': 'Resume Too Short',
            'detail': f'Only {word_count} words detected. Most ATS-friendly resumes have 300-700 words.',
            'fix': 'Expand your descriptions with specific achievements, metrics, and relevant details.',
            'severity': 'high',
        })
    elif word_count > 1000:
        results['formatting_issues'].append({
            'issue': 'Resume May Be Too Long',
            'detail': f'{word_count} words detected. Consider condensing to 1-2 pages.',
            'fix': 'Focus on the most relevant and recent experience. Remove outdated entries.',
            'severity': 'medium',
        })

    # --- Keyword Analysis ---
    skill_count = len(skills)
    results['keyword_analysis'] = {
        'total_skills_detected': skill_count,
        'skill_density': round(skill_count / max(word_count / 100, 1), 1),
        'has_industry_keywords': skill_count >= 5,
    }

    # --- Calculate ATS Score ---
    ats_score = section_score  # 0-100 from sections

    # Formatting penalty
    high_issues = sum(1 for i in results['formatting_issues'] if i['severity'] == 'high')
    med_issues = sum(1 for i in results['formatting_issues'] if i['severity'] == 'medium')
    ats_score -= (high_issues * 15 + med_issues * 5)

    # Keyword bonus
    if skill_count >= 10:
        ats_score += 10
    elif skill_count >= 5:
        ats_score += 5

    # Readability bonus (word count in good range)
    if 300 <= word_count <= 800:
        ats_score += 10

    results['ats_score'] = max(0, min(100, ats_score))
    results['pass_likely'] = results['ats_score'] >= 60

    return results


# ---------------------------------------------------------------------------
# Feature 3: Smart Job-Match Analysis
# ---------------------------------------------------------------------------

_semantic_model = None


def _get_semantic_model():
    """Lazily load and cache the sentence-embedding model (only on first use,
    so importing analyzer.py or running the rest of the app doesn't pay the
    load cost when job-matching is never used)."""
    global _semantic_model
    if _semantic_model is None:
        from sentence_transformers import SentenceTransformer
        _semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _semantic_model


def _semantic_similarity(resume_text, job_description):
    """Cosine similarity (0-100) between resume and JD embeddings.

    Returns None if the model can't be loaded (e.g. dependency missing or a
    first-run model download failed) so the caller can fall back gracefully
    to lexical-only matching instead of crashing the whole feature.
    """
    try:
        from sentence_transformers import util
        model = _get_semantic_model()
        embeddings = model.encode([resume_text[:2000], job_description[:2000]])
        score = float(util.cos_sim(embeddings[0], embeddings[1])[0][0]) * 100
        return max(0, min(100, round(score)))
    except Exception:
        return None


def match_job_description(resume_text, job_description):
    """Compare a resume against a job description.

    Blends lexical matching (word/phrase overlap and a skills-database
    lookup, via NLTK tokenization and stopword removal) with real semantic
    similarity from sentence embeddings, so e.g. "JS" in a resume can match
    "JavaScript" in a job description even without an exact string match.
    """
    if not job_description.strip():
        return {'error': 'No job description provided.'}

    # Tokenize and clean both texts
    stop_words = set(stopwords.words('english'))

    def extract_meaningful_words(text):
        tokens = word_tokenize(text.lower())
        return set(t for t in tokens if t.isalpha() and len(t) > 2 and t not in stop_words)

    def extract_phrases(text):
        """Extract 2-3 word phrases (bigrams/trigrams) for better matching."""
        tokens = word_tokenize(text.lower())
        clean = [t for t in tokens if t.isalpha() and t not in stop_words]
        phrases = set()
        for i in range(len(clean) - 1):
            phrases.add(f"{clean[i]} {clean[i+1]}")
        for i in range(len(clean) - 2):
            phrases.add(f"{clean[i]} {clean[i+1]} {clean[i+2]}")
        return phrases

    resume_words = extract_meaningful_words(resume_text)
    jd_words = extract_meaningful_words(job_description)

    resume_phrases = extract_phrases(resume_text)
    jd_phrases = extract_phrases(job_description)

    # Word-level matching
    word_matches = resume_words & jd_words
    word_only_in_jd = jd_words - resume_words

    # Phrase-level matching
    phrase_matches = resume_phrases & jd_phrases

    # Extract specific requirements from JD using word-boundary matching
    jd_lower = job_description.lower()
    resume_lower = resume_text.lower()
    required_skills = set()
    matched_skills = set()
    missing_skills = set()

    # Short skills that need strict word-boundary matching to avoid false positives
    SHORT_SKILLS = {'r', 'c', 'go', 'css', 'sql', 'git', 'npm', 'pip', 'lua',
                    'ios', 'aws', 'gcp', 'qa', 'ui', 'ux', 'ai', 'ml', 'nlp',
                    'svm', 'hnd', 'hnc', 'ba', 'ma', 'md', 'vba', 'sre'}

    for category, skill_list in SKILLS_DB.items():
        for skill in skill_list:
            # Use word-boundary regex for accurate matching
            if len(skill) <= 3 or skill in SHORT_SKILLS:
                pattern = r'(?<![a-zA-Z])' + re.escape(skill) + r'(?![a-zA-Z])'
            else:
                pattern = r'\b' + re.escape(skill) + r'\b'

            if re.search(pattern, jd_lower):
                required_skills.add(skill)
                if re.search(pattern, resume_lower):
                    matched_skills.add(skill)
                else:
                    missing_skills.add(skill)

    # Semantic similarity (embeddings) — supplements the lexical signals below
    # with something that understands "JS" and "JavaScript" are related even
    # when the resume and JD don't share the exact same string.
    semantic_similarity = _semantic_similarity(resume_text, job_description)

    # Calculate match score
    if not jd_words:
        match_pct = 0
    else:
        word_pct = len(word_matches) / len(jd_words) * 100
        phrase_pct = min(len(phrase_matches) * 5, 100)  # Each phrase match is worth more
        skill_pct = (len(matched_skills) / max(len(required_skills), 1)) * 100

        if semantic_similarity is not None:
            # word (35%) + phrase (15%) + skill-database (25%) + semantic (25%)
            match_pct = round(word_pct * 0.35 + phrase_pct * 0.15 + skill_pct * 0.25 + semantic_similarity * 0.25)
        else:
            # Semantic model unavailable — fall back to the original lexical-only weights
            match_pct = round(word_pct * 0.5 + phrase_pct * 0.2 + skill_pct * 0.3)
        match_pct = min(100, match_pct)

    # Categorize missing keywords by importance
    all_skills_flat = set(s for sl in SKILLS_DB.values() for s in sl)
    important_missing = []
    nice_to_have_missing = []
    for word in sorted(word_only_in_jd):
        if word in all_skills_flat:
            important_missing.append(word)
        elif len(word) > 4:
            nice_to_have_missing.append(word)

    # Generate recommendations for missing skills
    missing_skill_recommendations = []
    for skill in sorted(missing_skills):
        tip = _get_skill_recommendation(skill)
        missing_skill_recommendations.append({
            'skill': skill.title(),
            'tip': tip,
        })

    return {
        'match_score': match_pct,
        'semantic_similarity': semantic_similarity,
        'matched_keywords': sorted(word_matches)[:30],
        'matched_skills': sorted(s.title() for s in matched_skills),
        'missing_skills': sorted(s.title() for s in missing_skills),
        'missing_skill_recommendations': missing_skill_recommendations,
        'important_missing_keywords': sorted(important_missing)[:15],
        'nice_to_have_keywords': sorted(nice_to_have_missing)[:15],
        'phrase_matches': sorted(phrase_matches)[:10],
        'total_jd_keywords': len(jd_words),
        'total_matched': len(word_matches),
        'recommendation': _get_match_recommendation(match_pct),
    }


def _get_skill_recommendation(skill):
    """Return a brief actionable tip for a missing skill."""
    skill_lower = skill.lower()
    # Programming languages
    if skill_lower in ('python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php',
                       'swift', 'kotlin', 'go', 'rust', 'typescript', 'r', 'dart'):
        return f'Add {skill.title()} to your Skills section if you have any experience with it, even from coursework or personal projects.'
    # Frameworks
    if skill_lower in ('react', 'angular', 'vue', 'django', 'flask', 'node.js',
                       'spring boot', 'laravel', 'flutter', 'react native', 'next.js',
                       'express', 'asp.net', 'bootstrap', 'tailwind'):
        return f'If you have used {skill.title()}, list it under Technical Skills. Even tutorial-level experience counts for entry roles.'
    # Cloud/DevOps
    if skill_lower in ('aws', 'azure', 'docker', 'kubernetes', 'jenkins', 'ci/cd',
                       'terraform', 'linux', 'git', 'devops', 'google cloud', 'gcp'):
        return f'Consider adding {skill.title()} — free certifications or labs (e.g., AWS Free Tier, Docker tutorials) can help you build this skill quickly.'
    # Data
    if skill_lower in ('machine learning', 'deep learning', 'data analysis', 'pandas',
                       'tensorflow', 'pytorch', 'tableau', 'power bi', 'sql'):
        return f'Mention any {skill.title()} projects, even academic ones. Highlight datasets analyzed or models built.'
    # Soft skills
    if skill_lower in ('leadership', 'teamwork', 'communication', 'project management',
                       'agile', 'scrum', 'problem solving', 'time management'):
        return f'Demonstrate {skill.title()} through concrete examples in your Experience section rather than just listing it.'
    # Default
    return f'Consider learning or highlighting {skill.title()} on your resume if relevant to this role.'


def _get_match_recommendation(score):
    # Thresholds match the match-circle CSS tiers in job_match.html (70/50/30)
    # so the visual tier and this verdict text always agree.
    if score >= 70:
        return 'Excellent match! Your resume aligns very well with this job description.'
    elif score >= 50:
        return 'Good match. Add the missing keywords to strengthen your application.'
    elif score >= 30:
        return 'Moderate match. Consider tailoring your resume significantly for this role.'
    else:
        return 'Low match. This role may require skills or experience not reflected in your resume.'


# ---------------------------------------------------------------------------
# Feature 5: Career Fit and Role Recommendation
# ---------------------------------------------------------------------------

def suggest_career_roles(skills, experience, education, text):
    """Suggest specific job roles/titles based on skills, experience, and education.

    Returns a list of role suggestions with reasoning.
    """
    skill_names = set(s.lower() for s, _ in skills) if skills else set()
    text_lower = text.lower()
    exp_text = ' '.join(title for title, _, _ in experience).lower() if experience else ''

    role_database = {
        'Junior Web Developer': {
            'required': ['html', 'css', 'javascript'],
            'bonus': ['react', 'vue', 'angular', 'node.js', 'typescript', 'bootstrap'],
            'level': 'entry',
        },
        'Full-Stack Developer': {
            'required': ['javascript', 'html', 'css'],
            'bonus': ['react', 'node.js', 'python', 'sql', 'mongodb', 'express', 'next.js'],
            'level': 'mid',
        },
        'Software Engineer': {
            'required': ['python', 'git'],
            'bonus': ['java', 'c++', 'c#', 'algorithms', 'data structures', 'sql', 'docker'],
            'level': 'mid',
        },
        'Data Analyst': {
            'required': ['sql', 'excel'],
            'bonus': ['python', 'tableau', 'power bi', 'pandas', 'data analysis', 'data visualization'],
            'level': 'entry',
        },
        'Data Scientist': {
            'required': ['python', 'machine learning'],
            'bonus': ['tensorflow', 'pytorch', 'pandas', 'numpy', 'scikit-learn', 'deep learning'],
            'level': 'mid',
        },
        'Mobile App Developer': {
            'required': ['react native'],
            'bonus': ['flutter', 'android', 'ios', 'swift', 'kotlin', 'dart'],
            'level': 'mid',
        },
        'DevOps Engineer': {
            'required': ['docker', 'linux'],
            'bonus': ['aws', 'kubernetes', 'terraform', 'jenkins', 'ci/cd', 'ansible'],
            'level': 'mid',
        },
        'UI/UX Designer': {
            'required': ['figma'],
            'bonus': ['adobe photoshop', 'sketch', 'wireframe', 'user research', 'prototype'],
            'level': 'entry',
        },
        'Database Administrator': {
            'required': ['sql', 'database design'],
            'bonus': ['mysql', 'postgresql', 'mongodb', 'oracle', 'redis', 'sql server'],
            'level': 'mid',
        },
        'Project Coordinator': {
            'required': ['communication', 'teamwork'],
            'bonus': ['leadership', 'time management', 'agile', 'scrum', 'jira', 'strategic planning'],
            'level': 'entry',
        },
        'Office Administrator': {
            'required': ['communication'],
            'bonus': ['time management', 'teamwork', 'adaptability', 'presentation', 'problem solving'],
            'level': 'entry',
        },
        'Customer Service Representative': {
            'required': ['communication'],
            'bonus': ['teamwork', 'problem solving', 'adaptability', 'time management'],
            'level': 'entry',
        },
        'Business Analyst': {
            'required': ['communication', 'data analysis'],
            'bonus': ['sql', 'excel', 'tableau', 'power bi', 'strategic planning'],
            'level': 'mid',
        },
        'IT Support Specialist': {
            'required': ['communication'],
            'bonus': ['linux', 'networking', 'python', 'bash', 'problem solving'],
            'level': 'entry',
        },
    }

    suggestions = []
    for role, config in role_database.items():
        required = config['required']
        bonus = config['bonus']

        # Check required skills
        req_match = sum(1 for s in required if s in skill_names)
        if req_match < len(required):
            continue  # Must have all required skills

        # Count bonus skills
        bonus_match = sum(1 for s in bonus if s in skill_names)
        total_match = req_match + bonus_match
        max_possible = len(required) + len(bonus)

        fit_score = round((total_match / max_possible) * 100)

        # Experience boost
        if any(role.lower().split()[0] in exp_text for _ in [1]):
            fit_score = min(100, fit_score + 15)

        matched_skills = [s.title() for s in required + bonus if s in skill_names]

        suggestions.append({
            'role': role,
            'fit_score': fit_score,
            'level': config['level'],
            'matched_skills': matched_skills,
            'total_matched': total_match,
        })

    # Sort by fit score
    suggestions.sort(key=lambda x: x['fit_score'], reverse=True)
    return suggestions[:6]  # Top 6 roles


# ---------------------------------------------------------------------------
# Feature 6: Employer-Oriented Insights
# ---------------------------------------------------------------------------

def generate_employer_summary(name, skills, education, experience, scores, field_recommendations):
    """Generate a hiring-manager-friendly summary of the candidate.

    Provides a quick overview for recruiters to assess fit.
    """
    skill_names = [s for s, _ in skills] if skills else []
    categories = set(cat for _, cat in skills) if skills else set()

    # Determine seniority
    exp_count = len(experience) if experience else 0
    if exp_count >= 5:
        seniority = 'Senior'
    elif exp_count >= 2:
        seniority = 'Mid-Level'
    else:
        seniority = 'Entry-Level'

    # Top field
    top_field = field_recommendations[0][0] if field_recommendations else 'General'

    # Build summary
    edu_text = ''
    if education:
        for entry in education:
            if isinstance(entry, dict):
                inst = entry.get('institution', '')
                deg = entry.get('degree', '')
                if inst or deg:
                    edu_text = f"{deg} from {inst}" if deg and inst else (deg or inst)
                    break

    overall = scores.get('overall', 0)
    if overall >= 80:
        verdict = 'Strong Candidate'
        verdict_class = 'excellent'
    elif overall >= 60:
        verdict = 'Good Candidate'
        verdict_class = 'good'
    elif overall >= 40:
        verdict = 'Potential Candidate'
        verdict_class = 'average'
    else:
        verdict = 'Needs Development'
        verdict_class = 'poor'

    # Highlight skills (top 8)
    highlight_skills = skill_names[:8]

    # Key strengths
    strengths = []
    if scores.get('skills', 0) >= 80:
        strengths.append(f'Diverse skill set ({len(skill_names)} skills across {len(categories)} categories)')
    if scores.get('experience', 0) >= 80:
        strengths.append(f'Solid work experience ({exp_count} positions)')
    if scores.get('education', 0) >= 70:
        strengths.append(f'Strong educational background')
    if scores.get('formatting', 0) >= 80:
        strengths.append('Well-formatted, professional resume')

    # Areas of concern
    concerns = []
    if scores.get('skills', 0) < 50:
        concerns.append('Limited technical skills demonstrated')
    if scores.get('experience', 0) < 50:
        concerns.append('Limited work experience')
    if scores.get('education', 0) < 40:
        concerns.append('Education section needs improvement')

    return {
        'candidate_name': name,
        'seniority': seniority,
        'primary_field': top_field,
        'verdict': verdict,
        'verdict_class': verdict_class,
        'overall_score': overall,
        'education_summary': edu_text,
        'highlight_skills': highlight_skills,
        'strengths': strengths,
        'concerns': concerns,
        'scores': scores,
    }


# ---------------------------------------------------------------------------
# Feature 4: Resume Builder Templates
# ---------------------------------------------------------------------------

RESUME_TEMPLATES = {
    'universal': {
        'title': 'Universal Resume',
        'icon': 'document',
        'sections': [
            {
                'name': 'Contact Information',
                'hint': 'Full Name\nEmail Address\nPhone Number\nCity, Country\nLinkedIn / Portfolio / Website (optional)',
            },
            {
                'name': 'Professional Summary / Objective',
                'hint': '[Your profession or target role] with [X years / fresh graduate] experience in [your field].\n'
                        'Skilled in [top 3-5 skills relevant to the job].\n'
                        'Seeking a [target role] position to [what you want to contribute].\n\n'
                        'Examples:\n'
                        '• "Detail-oriented Accountant with 3 years of experience in financial reporting and tax preparation."\n'
                        '• "Motivated Computer Science graduate seeking an entry-level Software Developer role."\n'
                        '• "Experienced Nurse with 5 years in emergency care and patient management."',
            },
            {
                'name': 'Skills',
                'hint': 'List your key skills relevant to the job you are applying for.\n'
                        'Group them into categories if possible:\n\n'
                        'Technical Skills: [e.g., Python, Excel, AutoCAD, QuickBooks, Adobe Photoshop]\n'
                        'Soft Skills: [e.g., Communication, Leadership, Problem Solving, Teamwork]\n'
                        'Languages: [e.g., English (Fluent), Arabic (Native), French (Intermediate)]\n'
                        'Certifications: [e.g., PMP, AWS Certified, IELTS Band 7, First Aid]',
            },
            {
                'name': 'Work Experience',
                'hint': 'Job Title — Company Name | City | Start Date – End Date\n'
                        '- Describe what you did using action verbs (Managed, Developed, Designed, Coordinated, etc.)\n'
                        '- Include numbers and results when possible (e.g., "Served 50+ customers daily")\n'
                        '- Focus on achievements, not just duties\n\n'
                        'Examples:\n'
                        '• "Sales Associate — ABC Store | Dubai | Jan 2023 – Present\n'
                        '  - Assisted 40+ customers daily and achieved 110% of monthly sales targets\n'
                        '  - Trained 3 new team members on product knowledge and POS system"\n\n'
                        '• "Marketing Intern — XYZ Agency | Manila | Jun 2022 – Aug 2022\n'
                        '  - Created social media content that increased engagement by 25%"',
            },
            {
                'name': 'Education',
                'hint': 'Degree — University / School Name | Graduation Year\n'
                        'Relevant Coursework: [Course 1, Course 2, Course 3] (optional)\n'
                        'GPA: [if 3.0+ or equivalent] (optional)\n\n'
                        'Examples:\n'
                        '• "Bachelor of Science in Information Technology — AMA University | 2024"\n'
                        '• "High School Diploma — Dubai International School | 2020"',
            },
            {
                'name': 'Projects / Achievements (Optional)',
                'hint': 'Project Name | Tools/Technologies Used\n'
                        '- Brief description of the project and your role\n'
                        '- Key results or outcomes\n\n'
                        'Or list awards, honors, and achievements:\n'
                        '• "Dean\'s List — 4 consecutive semesters"\n'
                        '• "1st Place, National Business Plan Competition 2023"\n'
                        '• "Volunteer of the Year — Red Cross Dubai Chapter"',
            },
            {
                'name': 'References (Optional)',
                'hint': 'Reference Name — Position, Company\nEmail: [email]\nPhone: [phone]\n\n'
                        'Or simply write: "References available upon request"',
            },
        ],
    },
}


def highlight_matches(raw_text, skill_names):
    """HTML-escape raw resume text and wrap case-insensitive, word-boundary
    matches of each skill name in <mark> tags, so the caller can render it
    with |safe. Longest names are matched first via a single alternation
    pass so multi-word skills aren't shadowed by a shorter substring skill
    and nothing gets double-wrapped."""
    from markupsafe import escape
    if not raw_text:
        return ''
    escaped = str(escape(raw_text))
    names = sorted({s for s in skill_names if s}, key=len, reverse=True)
    if not names:
        return escaped
    pattern = re.compile(
        r'(?<!\w)(' + '|'.join(re.escape(n) for n in names) + r')(?!\w)',
        re.IGNORECASE
    )
    return pattern.sub(r'<mark>\1</mark>', escaped)
