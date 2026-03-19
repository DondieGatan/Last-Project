import pyodbc
from config import Config


def get_db_connection():
    """Create and return a SQL Server database connection."""
    if Config.SQL_TRUSTED_CONNECTION.lower() == 'yes':
        conn_str = (
            f"DRIVER={Config.SQL_DRIVER};"
            f"SERVER={Config.SQL_SERVER};"
            f"DATABASE={Config.SQL_DATABASE};"
            f"Trusted_Connection=yes;"
        )
    else:
        conn_str = (
            f"DRIVER={Config.SQL_DRIVER};"
            f"SERVER={Config.SQL_SERVER};"
            f"DATABASE={Config.SQL_DATABASE};"
            f"UID={Config.SQL_USERNAME};"
            f"PWD={Config.SQL_PASSWORD};"
        )
    connection = pyodbc.connect(conn_str)
    return connection


def save_resume(candidate_name, email, phone, filename, raw_text):
    """Save resume metadata and return the inserted ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO resumes (candidate_name, email, phone, filename, raw_text) "
        "OUTPUT INSERTED.id "
        "VALUES (?, ?, ?, ?, ?)",
        (candidate_name, email, phone, filename, raw_text)
    )
    resume_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return resume_id


def save_skills(resume_id, skills):
    """Save extracted skills for a resume."""
    conn = get_db_connection()
    cursor = conn.cursor()
    for skill_name, category in skills:
        cursor.execute(
            "INSERT INTO skills (resume_id, skill_name, category) VALUES (?, ?, ?)",
            (resume_id, skill_name, category)
        )
    conn.commit()
    cursor.close()
    conn.close()


def save_education(resume_id, education_list):
    """Save education details for a resume."""
    conn = get_db_connection()
    cursor = conn.cursor()
    for degree, institution in education_list:
        cursor.execute(
            "INSERT INTO education (resume_id, degree, institution) VALUES (?, ?, ?)",
            (resume_id, degree, institution)
        )
    conn.commit()
    cursor.close()
    conn.close()


def save_experience(resume_id, experience_list):
    """Save work experience for a resume."""
    conn = get_db_connection()
    cursor = conn.cursor()
    for title, company, description in experience_list:
        cursor.execute(
            "INSERT INTO experience (resume_id, title, company, description) VALUES (?, ?, ?, ?)",
            (resume_id, title, company, description)
        )
    conn.commit()
    cursor.close()
    conn.close()


def save_analysis_results(resume_id, overall_score, skills_score, education_score,
                          experience_score, formatting_score, recommended_field, recommendations):
    """Save the analysis results for a resume."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO analysis_results "
        "(resume_id, overall_score, skills_score, education_score, experience_score, "
        "formatting_score, recommended_field, recommendations) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (resume_id, overall_score, skills_score, education_score,
         experience_score, formatting_score, recommended_field, recommendations)
    )
    conn.commit()
    cursor.close()
    conn.close()


def _row_to_dict(cursor, row):
    """Convert a pyodbc Row to a dictionary."""
    if row is None:
        return None
    columns = [column[0] for column in cursor.description]
    return dict(zip(columns, row))


def _rows_to_dicts(cursor, rows):
    """Convert multiple pyodbc Rows to a list of dictionaries."""
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


def get_resume_by_id(resume_id):
    """Retrieve a resume and its analysis results by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM resumes WHERE id = ?", (resume_id,))
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        return None
    resume = _row_to_dict(cursor, row)

    cursor.execute("SELECT * FROM skills WHERE resume_id = ?", (resume_id,))
    resume['skills'] = _rows_to_dicts(cursor, cursor.fetchall())

    cursor.execute("SELECT * FROM education WHERE resume_id = ?", (resume_id,))
    resume['education'] = _rows_to_dicts(cursor, cursor.fetchall())

    cursor.execute("SELECT * FROM experience WHERE resume_id = ?", (resume_id,))
    resume['experience'] = _rows_to_dicts(cursor, cursor.fetchall())

    cursor.execute("SELECT * FROM analysis_results WHERE resume_id = ?", (resume_id,))
    resume['analysis'] = _row_to_dict(cursor, cursor.fetchone())

    cursor.close()
    conn.close()
    return resume


def get_all_resumes():
    """Retrieve all resumes with their scores."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.id, r.candidate_name, r.email, r.upload_date,
               ar.overall_score, ar.recommended_field
        FROM resumes r
        LEFT JOIN analysis_results ar ON ar.resume_id = r.id
        ORDER BY r.upload_date DESC
    """)
    resumes = _rows_to_dicts(cursor, cursor.fetchall())
    cursor.close()
    conn.close()
    return resumes


def get_dashboard_data():
    """Get aggregated data for the dashboard / Power BI export."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Overall statistics
    cursor.execute("SELECT COUNT(*) AS total_resumes FROM resumes")
    stats = _row_to_dict(cursor, cursor.fetchone())

    cursor.execute("SELECT AVG(CAST(overall_score AS FLOAT)) AS avg_score FROM analysis_results")
    avg_row = _row_to_dict(cursor, cursor.fetchone())
    stats['avg_score'] = round(avg_row['avg_score'], 1) if avg_row['avg_score'] else 0

    # Score distribution
    cursor.execute("""
        SELECT
            CASE
                WHEN overall_score >= 80 THEN 'Excellent'
                WHEN overall_score >= 60 THEN 'Good'
                WHEN overall_score >= 40 THEN 'Average'
                ELSE 'Needs Improvement'
            END AS rating,
            COUNT(*) AS count
        FROM analysis_results
        GROUP BY
            CASE
                WHEN overall_score >= 80 THEN 'Excellent'
                WHEN overall_score >= 60 THEN 'Good'
                WHEN overall_score >= 40 THEN 'Average'
                ELSE 'Needs Improvement'
            END
    """)
    stats['score_distribution'] = _rows_to_dicts(cursor, cursor.fetchall())

    # Top skills
    cursor.execute("""
        SELECT TOP 20 skill_name, category, COUNT(*) AS frequency
        FROM skills
        GROUP BY skill_name, category
        ORDER BY frequency DESC
    """)
    stats['top_skills'] = _rows_to_dicts(cursor, cursor.fetchall())

    # Recommended fields distribution
    cursor.execute("""
        SELECT recommended_field, COUNT(*) AS count
        FROM analysis_results
        WHERE recommended_field IS NOT NULL
        GROUP BY recommended_field
        ORDER BY count DESC
    """)
    stats['field_distribution'] = _rows_to_dicts(cursor, cursor.fetchall())

    # All resume data for Power BI export
    cursor.execute("SELECT * FROM resume_dashboard")
    stats['all_data'] = _rows_to_dicts(cursor, cursor.fetchall())

    cursor.close()
    conn.close()
    return stats
