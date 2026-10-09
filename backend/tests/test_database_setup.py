import os
import sys


def test_create_tables_import_works():
    os.environ["DATABASE_URL"] = "sqlite://"
    sys.modules.pop("bc_ferry_data_platform.database.create_tables", None)

    from bc_ferry_data_platform.database import create_tables

    assert create_tables.Base is not None
    assert create_tables.engine is not None
