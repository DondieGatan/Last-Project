"""Poll the configured SQL Server until it accepts connections, or give up
after ~60 seconds. Used by CI to wait for the mssql service container to
finish starting before the schema-setup steps try to connect."""
import os
import sys
import time

import pyodbc
from config import Config


def main():
    conn_str = (
        f"DRIVER={Config.SQL_DRIVER};"
        f"SERVER={Config.SQL_SERVER};"
        f"UID={Config.SQL_USERNAME};"
        f"PWD={Config.SQL_PASSWORD};"
        f"TrustServerCertificate=yes;"
    )
    for attempt in range(30):
        try:
            conn = pyodbc.connect(conn_str, timeout=3)
            conn.close()
            print(f'SQL Server is up after {attempt + 1} attempt(s).')
            return 0
        except pyodbc.Error as e:
            print(f'attempt {attempt + 1}: not ready yet ({e})')
            time.sleep(2)
    print('SQL Server did not become ready in time.', file=sys.stderr)
    return 1


if __name__ == '__main__':
    sys.exit(main())
