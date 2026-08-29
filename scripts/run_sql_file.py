"""Run a .sql script (written for sqlcmd/SSMS, with 'GO' batch separators)
against the database configured in config.py, via pyodbc. Used by CI to
set up a fresh schema — not needed for local dev, where SSMS/sqlcmd or
Config.SQL_TRUSTED_CONNECTION Windows auth already covers it.

Usage: python scripts/run_sql_file.py setup_db.sql [setup_users_table.sql ...]
"""
import sys
import pyodbc
from config import Config


def run_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    batches = [b.strip() for b in content.split('\nGO\n')]
    batches = [b for b in batches if b]

    conn_str = (
        f"DRIVER={Config.SQL_DRIVER};"
        f"SERVER={Config.SQL_SERVER};"
        f"UID={Config.SQL_USERNAME};"
        f"PWD={Config.SQL_PASSWORD};"
        f"TrustServerCertificate=yes;"
    )
    conn = pyodbc.connect(conn_str, autocommit=True)
    cursor = conn.cursor()
    for batch in batches:
        try:
            cursor.execute(batch)
        except pyodbc.Error as e:
            print(f'--- batch failed in {path} ---\n{batch}\n--- error: {e}')
            raise
    cursor.close()
    conn.close()
    print(f'Ran {path} ({len(batches)} batches).')


if __name__ == '__main__':
    for sql_path in sys.argv[1:]:
        run_file(sql_path)
