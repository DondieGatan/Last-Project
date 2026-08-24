-- Run this script in SQL Server Management Studio against the smart_resume_analyser database

USE smart_resume_analyser;
GO

-- Create users table
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='users' AND xtype='U')
BEGIN
    CREATE TABLE users (
        id INT IDENTITY(1,1) PRIMARY KEY,
        full_name NVARCHAR(150) NOT NULL,
        email NVARCHAR(255) NOT NULL UNIQUE,
        password_hash NVARCHAR(255) NOT NULL,
        created_at DATETIME DEFAULT GETDATE(),
        is_active BIT DEFAULT 1,
        reset_token NVARCHAR(255) NULL,
        reset_token_expiry DATETIME NULL
    );

    CREATE UNIQUE INDEX idx_users_email ON users(email);
    PRINT 'Users table created successfully.';
END
ELSE
    PRINT 'Users table already exists.';
GO
