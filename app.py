import os
import csv
import io
import json
from flask import (Flask, render_template, request, redirect, url_for,
                   flash, jsonify, Response, send_from_directory)
from werkzeug.utils import secure_filename
from config import Config
from analyzer import analyse_resume
from models import (save_resume, save_skills, save_education, save_experience,
                    save_analysis_results, get_resume_by_id, get_all_resumes,
                    get_dashboard_data)

app = Flask(__name__)
app.config.from_object(Config)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------

@app.route('/')
def index():
    """Home page with resume upload form."""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
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
        flash('Only PDF files are allowed.', 'error')
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
        save_analysis_results(
            resume_id,
            scores['overall'], scores['skills'], scores['education'],
            scores['experience'], scores['formatting'],
            result['recommended_field'],
            json.dumps(result['recommendations'])
        )

        return redirect(url_for('result', resume_id=resume_id))

    except Exception as e:
        flash(f'An error occurred during analysis: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/result/<int:resume_id>')
def result(resume_id):
    """Display analysis results for a specific resume."""
    resume = get_resume_by_id(resume_id)
    if not resume:
        flash('Resume not found.', 'error')
        return redirect(url_for('index'))

    # Parse recommendations JSON
    if resume['analysis'] and resume['analysis']['recommendations']:
        try:
            resume['analysis']['recommendations'] = json.loads(
                resume['analysis']['recommendations']
            )
        except (json.JSONDecodeError, TypeError):
            resume['analysis']['recommendations'] = []

    return render_template('result.html', resume=resume)


@app.route('/history')
def history():
    """Show all previously analysed resumes."""
    resumes = get_all_resumes()
    return render_template('history.html', resumes=resumes)


@app.route('/dashboard')
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
            'all_data': []
        }
    return render_template('dashboard.html', data=data)


@app.route('/api/dashboard-data')
def api_dashboard_data():
    """API endpoint returning dashboard data as JSON (for Power BI)."""
    try:
        data = get_dashboard_data()
        # Convert datetime objects to strings for JSON serialisation
        for item in data.get('all_data', []):
            if 'upload_date' in item and item['upload_date']:
                item['upload_date'] = str(item['upload_date'])
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/export/csv')
def export_csv():
    """Export all resume data as CSV for Power BI import."""
    try:
        data = get_dashboard_data()
    except Exception:
        flash('No data available to export.', 'error')
        return redirect(url_for('dashboard'))

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
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
def api_resume(resume_id):
    """API endpoint to get resume data as JSON."""
    resume = get_resume_by_id(resume_id)
    if not resume:
        return jsonify({'error': 'Resume not found'}), 404

    # Convert datetime for JSON
    if resume.get('upload_date'):
        resume['upload_date'] = str(resume['upload_date'])
    if resume.get('analysis') and resume['analysis'].get('analysed_date'):
        resume['analysis']['analysed_date'] = str(resume['analysis']['analysed_date'])

    return jsonify(resume)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
