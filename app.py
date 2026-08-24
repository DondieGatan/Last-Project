import os
import csv
import io
import json
from functools import wraps
from flask import (Flask, render_template, request, redirect, url_for,
                   flash, jsonify, Response, send_from_directory, session)
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
from config import Config
from analyzer import (analyse_resume, IMAGE_EXTENSIONS, generate_personalized_feedback,
                      match_job_description, RESUME_TEMPLATES)
from models import (save_resume, save_skills, save_education, save_experience,
                    save_analysis_results, get_resume_by_id, get_all_resumes,
                    get_dashboard_data, init_users_table, register_user,
                    authenticate_user, get_user_by_id, get_user_by_email,
                    create_reset_code, verify_reset_code, reset_user_password)

app = Flask(__name__)
app.config.from_object(Config)

# Initialize Flask-Mail
mail = Mail(app)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Create users table if it doesn't exist
try:
    init_users_table()
except Exception:
    pass  # Table may already exist or DB not yet available


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


# --------------------------------------------------------------------------
# Authentication decorator
# --------------------------------------------------------------------------

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


# --------------------------------------------------------------------------
# Authentication Routes
# --------------------------------------------------------------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter both email and password.', 'error')
            return render_template('login.html')

        user = authenticate_user(email, password)
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['full_name']
            session['user_email'] = user['email']
            flash(f'Welcome back, {user["full_name"]}!', 'success')
            next_page = request.args.get('next') or request.form.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'error')
            return render_template('login.html', email=email)

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page."""
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validation
        errors = []
        if not full_name:
            errors.append('Full name is required.')
        if not email:
            errors.append('Email is required.')
        if not password:
            errors.append('Password is required.')
        elif len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')

        if errors:
            for err in errors:
                flash(err, 'error')
            return render_template('register.html', full_name=full_name, email=email)

        success, message = register_user(full_name, email, password)
        if success:
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash(message, 'error')
            return render_template('register.html', full_name=full_name, email=email)

    return render_template('register.html')


@app.route('/logout')
def logout():
    """Log the user out."""
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password page — sends a 6-digit code to email."""
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        if not email:
            flash('Please enter your email address.', 'error')
            return render_template('forgot_password.html')

        code = create_reset_code(email)
        if code:
            # Send code via email
            try:
                msg = Message(
                    subject='Your Reset Code - Smart Resume Analyser',
                    recipients=[email],
                    html=render_template('email_reset.html',
                                         reset_code=code,
                                         user_email=email)
                )
                mail.send(msg)
                flash('A 6-digit code has been sent to your email.', 'success')
            except Exception:
                # If email fails, show the code directly (dev/demo fallback)
                flash(f'Email service unavailable. Your reset code is: {code}', 'success')
            return redirect(url_for('verify_code', email=email))
        else:
            # Don't reveal whether the email exists
            flash('If an account with that email exists, a code has been sent.', 'success')
            return redirect(url_for('forgot_password'))

    return render_template('forgot_password.html')


@app.route('/verify-code', methods=['GET', 'POST'])
def verify_code():
    """Verify the 6-digit reset code."""
    if 'user_id' in session:
        return redirect(url_for('index'))

    email = request.args.get('email', '') or request.form.get('email', '')

    if not email:
        flash('Please start the password reset process again.', 'error')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        code = request.form.get('code', '').strip()

        if not code or len(code) != 6:
            flash('Please enter the 6-digit code.', 'error')
            return render_template('verify_code.html', email=email)

        if verify_reset_code(email, code):
            # Code is valid — store email in session for reset page
            session['reset_email'] = email
            flash('Code verified! Set your new password.', 'success')
            return redirect(url_for('reset_password'))
        else:
            flash('Invalid or expired code. Please try again.', 'error')
            return render_template('verify_code.html', email=email)

    return render_template('verify_code.html', email=email)


@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Reset password after code verification."""
    if 'user_id' in session:
        return redirect(url_for('index'))

    email = session.get('reset_email')
    if not email:
        flash('Please verify your code first.', 'error')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not password or len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('reset_password.html')
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('reset_password.html')

        success, message = reset_user_password(email, password)
        if success:
            session.pop('reset_email', None)
            flash('Password reset successfully! Please log in with your new password.', 'success')
            return redirect(url_for('login'))
        else:
            flash(message, 'error')
            return redirect(url_for('forgot_password'))

    return render_template('reset_password.html')


# --------------------------------------------------------------------------
# Routes (all protected with login_required)
# --------------------------------------------------------------------------

@app.route('/')
@login_required
def index():
    """Home page with resume upload form."""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
@login_required
def upload_resume():
    """Handle resume upload and analysis."""
    if 'resume' not in request.files:
        flash('No file selected.', 'error')
        return redirect(url_for('index'))

    file = request.files['resume']
    if file.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('index'))

    if not allowed_file(file.filename):
        flash('Only PDF and image files (PNG, JPG, BMP, TIFF) are allowed.', 'error')
        return redirect(url_for('index'))

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        # Analyse the resume
        result = analyse_resume(filepath)

        if 'error' in result:
            flash(result['error'], 'error')
            return redirect(url_for('index'))

        # Save to database
        resume_id = save_resume(
            result['name'], result['email'], result['phone'],
            filename, result['raw_text']
        )

        save_skills(resume_id, result['skills'])
        save_education(resume_id, result['education'])
        save_experience(resume_id, result['experience'])

        scores = result['scores']
        # Pack all extra data into a single JSON payload
        extra_data = {
            'explanations': result.get('explanations', {}),
            'field_recommendations': [
                {'field': f, 'confidence': c, 'details': d}
                for f, c, d in result.get('field_recommendations', [])
            ],
            'recommendations': result['recommendations'],
            'ats_results': result.get('ats_results', {}),
            'career_roles': result.get('career_roles', []),
            'employer_summary': result.get('employer_summary', {}),
        }
        save_analysis_results(
            resume_id,
            scores['overall'], scores['skills'], scores['education'],
            scores['experience'], scores['formatting'],
            result['recommended_field'],
            json.dumps(extra_data)
        )

        return redirect(url_for('result', resume_id=resume_id))

    except Exception as e:
        flash(f'An error occurred during analysis: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/result/<int:resume_id>')
@login_required
def result(resume_id):
    """Display analysis results for a specific resume."""
    resume = get_resume_by_id(resume_id)
    if not resume:
        flash('Resume not found.', 'error')
        return redirect(url_for('index'))

    # Parse the stored JSON
    if resume['analysis'] and resume['analysis']['recommendations']:
        try:
            parsed = json.loads(resume['analysis']['recommendations'])
            if isinstance(parsed, dict):
                resume['analysis']['explanations'] = parsed.get('explanations', {})
                resume['analysis']['field_recommendations'] = parsed.get('field_recommendations', [])
                resume['analysis']['recommendations'] = parsed.get('recommendations', [])
                resume['analysis']['ats_results'] = parsed.get('ats_results', {})
                resume['analysis']['career_roles'] = parsed.get('career_roles', [])
                resume['analysis']['employer_summary'] = parsed.get('employer_summary', {})
            elif isinstance(parsed, list):
                resume['analysis']['recommendations'] = parsed
                resume['analysis']['explanations'] = {}
                resume['analysis']['field_recommendations'] = []
                resume['analysis']['ats_results'] = {}
                resume['analysis']['career_roles'] = []
                resume['analysis']['employer_summary'] = {}
        except (json.JSONDecodeError, TypeError):
            resume['analysis']['recommendations'] = []
            resume['analysis']['explanations'] = {}
            resume['analysis']['field_recommendations'] = []
            resume['analysis']['ats_results'] = {}
            resume['analysis']['career_roles'] = []
            resume['analysis']['employer_summary'] = {}

    return render_template('result.html', resume=resume)


# --------------------------------------------------------------------------
# Feature 1 & 7: Personalized Feedback / Resume Personalization
# --------------------------------------------------------------------------

@app.route('/personalize/<int:resume_id>', methods=['GET', 'POST'])
@login_required
def personalize(resume_id):
    """Context-aware personalized feedback page."""
    resume = get_resume_by_id(resume_id)
    if not resume:
        flash('Resume not found.', 'error')
        return redirect(url_for('index'))

    # Parse stored JSON for full analysis data
    parsed_data = {}
    if resume['analysis'] and resume['analysis']['recommendations']:
        try:
            parsed_data = json.loads(resume['analysis']['recommendations'])
            if not isinstance(parsed_data, dict):
                parsed_data = {}
        except (json.JSONDecodeError, TypeError):
            parsed_data = {}

    feedback = None
    career_goal = ''
    experience_level = ''
    target_role = ''

    if request.method == 'POST':
        career_goal = request.form.get('career_goal', '')
        experience_level = request.form.get('experience_level', '')
        target_role = request.form.get('target_role', '')

        # Build resume_data dict from DB data
        resume_data = {
            'skills': [(s['skill_name'], s.get('category', '')) for s in resume.get('skills', [])],
            'education': resume.get('education', []),
            'experience': [(e.get('title', ''), e.get('company', ''), e.get('description', ''))
                          for e in resume.get('experience', [])],
            'scores': {
                'skills': resume['analysis'].get('skills_score', 0) if resume['analysis'] else 0,
                'education': resume['analysis'].get('education_score', 0) if resume['analysis'] else 0,
                'experience': resume['analysis'].get('experience_score', 0) if resume['analysis'] else 0,
                'formatting': resume['analysis'].get('formatting_score', 0) if resume['analysis'] else 0,
            },
            'raw_text': resume.get('raw_text', ''),
        }
        feedback = generate_personalized_feedback(
            resume_data, career_goal, experience_level, target_role
        )

    return render_template('personalize.html',
                           resume=resume,
                           feedback=feedback,
                           career_goal=career_goal,
                           experience_level=experience_level,
                           target_role=target_role)


# --------------------------------------------------------------------------
# Feature 3: Smart Job-Match Analysis
# --------------------------------------------------------------------------

@app.route('/job-match/<int:resume_id>', methods=['GET', 'POST'])
@login_required
def job_match(resume_id):
    """Compare resume against a job description."""
    resume = get_resume_by_id(resume_id)
    if not resume:
        flash('Resume not found.', 'error')
        return redirect(url_for('index'))

    match_result = None
    job_description = ''

    if request.method == 'POST':
        job_description = request.form.get('job_description', '')
        if job_description.strip():
            match_result = match_job_description(
                resume.get('raw_text', ''),
                job_description
            )

    return render_template('job_match.html',
                           resume=resume,
                           match_result=match_result,
                           job_description=job_description)


# --------------------------------------------------------------------------
# Feature 4: Resume Builder
# --------------------------------------------------------------------------

@app.route('/builder')
@login_required
def builder():
    """Beginner-friendly resume builder with templates and guidance."""
    return render_template('builder.html', templates=RESUME_TEMPLATES)


@app.route('/builder/<template_id>')
@login_required
def builder_template(template_id):
    """Show a specific resume builder template."""
    template = RESUME_TEMPLATES.get(template_id)
    if not template:
        flash('Template not found.', 'error')
        return redirect(url_for('builder'))
    return render_template('builder_template.html',
                           template=template,
                           template_id=template_id)


# --------------------------------------------------------------------------
# Existing routes
# --------------------------------------------------------------------------

@app.route('/history')
@login_required
def history():
    """Show all previously analysed resumes."""
    resumes = get_all_resumes()
    return render_template('history.html', resumes=resumes)


@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard page with analytics and Power BI integration."""
    try:
        data = get_dashboard_data()
    except Exception:
        data = {
            'total_resumes': 0,
            'avg_score': 0,
            'score_distribution': [],
            'top_skills': [],
            'field_distribution': [],
            'all_data': [],
            'score_over_time': [],
            'ats_breakdown': {'skills': 0, 'education': 0, 'experience': 0, 'formatting': 0, 'overall': 0},
            'quality_categories': {'high': 0, 'medium': 0, 'low': 0}
        }
    return render_template('dashboard.html', data=data)


@app.route('/api/dashboard-data')
@login_required
def api_dashboard_data():
    """API endpoint returning dashboard data as JSON (for Power BI)."""
    try:
        data = get_dashboard_data()
        for item in data.get('all_data', []):
            if 'upload_date' in item and item['upload_date']:
                item['upload_date'] = str(item['upload_date'])
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/export/csv')
@login_required
def export_csv():
    """Export all resume data as CSV for Power BI import."""
    try:
        data = get_dashboard_data()
    except Exception:
        flash('No data available to export.', 'error')
        return redirect(url_for('dashboard'))

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        'ID', 'Candidate Name', 'Email', 'Upload Date',
        'Overall Score', 'Skills Score', 'Education Score',
        'Experience Score', 'Formatting Score',
        'Recommended Field', 'Total Skills'
    ])

    for row in data.get('all_data', []):
        writer.writerow([
            row.get('id', ''),
            row.get('candidate_name', ''),
            row.get('email', ''),
            str(row.get('upload_date', '')),
            row.get('overall_score', ''),
            row.get('skills_score', ''),
            row.get('education_score', ''),
            row.get('experience_score', ''),
            row.get('formatting_score', ''),
            row.get('recommended_field', ''),
            row.get('total_skills', '')
        ])

    response = Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=resume_analytics.csv'}
    )
    return response


@app.route('/api/resume/<int:resume_id>')
@login_required
def api_resume(resume_id):
    """API endpoint to get resume data as JSON."""
    resume = get_resume_by_id(resume_id)
    if not resume:
        return jsonify({'error': 'Resume not found'}), 404

    if resume.get('upload_date'):
        resume['upload_date'] = str(resume['upload_date'])
    if resume.get('analysis') and resume['analysis'].get('analysed_date'):
        resume['analysis']['analysed_date'] = str(resume['analysis']['analysed_date'])

    return jsonify(resume)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
