import os
from sqlalchemy import create_engine


def get_engine():
    url = (
        f"postgresql+pg8000://{os.environ.get('PGUSER', 'postgres')}:"
        f"{os.environ.get('PGPASSWORD', 'postgres')}@"
        f"{os.environ.get('PGHOST', 'localhost')}:"
        f"{os.environ.get('PGPORT', '5432')}/"
        f"{os.environ.get('PGDATABASE', 'supply_chain_case')}"
    )
    return create_engine(url)