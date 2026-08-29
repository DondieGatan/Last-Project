-- Smart Resume Analyser Database Schema for Microsoft SQL Server
-- Run this script in SSMS or via sqlcmd to set up the database

-- Create database
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'smart_resume_analyser')
BEGIN
    CREATE DATABASE smart_resume_analyser;
END
GO

USE smart_resume_analyser;
GO

-- Table to store uploaded resumes and analysis results
-- Note: user_id has no FK constraint here because this script may run
-- before the users table exists (that table is created separately by
-- setup_users_table.sql / models.init_users_table()). Ownership is
-- enforced at the application layer instead.
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'resumes')
BEGIN
    CREATE TABLE resumes (
        id INT IDENTITY(1,1) PRIMARY KEY,
        user_id INT NULL,
        candidate_name NVARCHAR(255) NOT NULL,
        email NVARCHAR(255),
        phone NVARCHAR(50),
        filename NVARCHAR(255) NOT NULL,
        raw_text NVARCHAR(MAX),
        upload_date DATETIME DEFAULT GETDATE()
    );
END
GO

-- Table to store extracted skills
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'skills')
BEGIN
    CREATE TABLE skills (
        id INT IDENTITY(1,1) PRIMARY KEY,
        resume_id INT NOT NULL,
        skill_name NVARCHAR(100) NOT NULL,
        category NVARCHAR(50),
        FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
    );
END
GO

-- Table to store education details
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'education')
BEGIN
    CREATE TABLE education (
        id INT IDENTITY(1,1) PRIMARY KEY,
        resume_id INT NOT NULL,
        degree NVARCHAR(255),
        institution NVARCHAR(255),
        FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
    );
END
GO

-- Table to store work experience
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'experience')
BEGIN
    CREATE TABLE experience (
        id INT IDENTITY(1,1) PRIMARY KEY,
        resume_id INT NOT NULL,
        title NVARCHAR(255),
        company NVARCHAR(255),
        description NVARCHAR(MAX),
        FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
    );
END
GO

-- Table to store analysis scores and recommendations
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'analysis_results')
BEGIN
    CREATE TABLE analysis_results (
        id INT IDENTITY(1,1) PRIMARY KEY,
        resume_id INT NOT NULL,
        overall_score INT DEFAULT 0,
        skills_score INT DEFAULT 0,
        education_score INT DEFAULT 0,
        experience_score INT DEFAULT 0,
        formatting_score INT DEFAULT 0,
        recommended_field NVARCHAR(100),
        recommendations NVARCHAR(MAX),
        analysed_date DATETIME DEFAULT GETDATE(),
        FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
    );
END
GO

-- View for Power BI dashboard
IF EXISTS (SELECT * FROM sys.views WHERE name = 'resume_dashboard')
    DROP VIEW resume_dashboard;
GO

CREATE VIEW resume_dashboard AS
SELECT
    r.id,
    r.user_id,
    r.candidate_name,
    r.email,
    r.upload_date,
    ar.overall_score,
    ar.skills_score,
    ar.education_score,
    ar.experience_score,
    ar.formatting_score,
    ar.recommended_field,
    (SELECT COUNT(*) FROM skills s WHERE s.resume_id = r.id) AS total_skills
FROM resumes r
LEFT JOIN analysis_results ar ON ar.resume_id = r.id;
GO
