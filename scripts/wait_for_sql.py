"""Poll the configured SQL Server until it accepts connections, or give up
after ~3 minutes. Used by CI to wait for the mssql service container to
finish starting before the schema-setup steps try to connect — the
mcr.microsoft.com/mssql/server image commonly takes well over a minute to
become ready even after its port is reachable, since --health-cmd is set
to a no-op (see tests.yml) so Actions doesn't block service startup on it."""
import sys
import time

import pyodbc
from config import Config

MAX_ATTEMPTS = 60
DELAY_SECONDS = 3


def main():
    conn_str = (
        f"DRIVER={Config.SQL_DRIVER};"
        f"SERVER={Config.SQL_SERVER};"
        f"UID={Config.SQL_USERNAME};"
        f"PWD={Config.SQL_PASSWORD};"
        f"TrustServerCertificate=yes;"
    )
    print(f'Connecting with: DRIVER={Config.SQL_DRIVER};SERVER={Config.SQL_SERVER};UID={Config.SQL_USERNAME};PWD=***;TrustServerCertificate=yes;')
    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            conn = pyodbc.connect(conn_str, timeout=5)
            conn.close()
            print(f'SQL Server is up after {attempt} attempt(s) (~{attempt * DELAY_SECONDS}s).')
            return 0
        except pyodbc.Error as e:
            last_error = e
            if attempt == 1 or attempt % 5 == 0:
                print(f'attempt {attempt}/{MAX_ATTEMPTS}: not ready yet ({e})')
            time.sleep(DELAY_SECONDS)
    print(f'SQL Server did not become ready within {MAX_ATTEMPTS * DELAY_SECONDS}s. Last error: {last_error}', file=sys.stderr)
    return 1


if __name__ == '__main__':
    sys.exit(main())
