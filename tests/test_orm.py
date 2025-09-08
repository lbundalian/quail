import os
import pytest
from sqlalchemy import text
from quail.orm import build_env_from_cfg


@pytest.fixture(scope="module")
def env():
    """
    Build a Quail ORM environment pointing at Redshift.
    Uses REDSHIFT_URL env var.
    """
    conn_str = "redshift+psycopg2://awsuser:Pg68h2ZHmVjml@redshift-cluster-2.clxqnyeopl7d.us-east-1.redshift.amazonaws.com:5439/db_quibble"
    if conn_str == "xyz":
        pytest.skip("No real REDSHIFT_URL provided, skipping integration test")

    cfg = {
        "kind": "sql",
        "url": conn_str,
        "schema": "raw_data",
        "reflect": ["pricing_report"],  # reflect this table into env["tables"]
    }
    env = build_env_from_cfg(cfg)
    yield env
    if "engine" in env:
        env["engine"].dispose()


# def test_redshift_connectivity(env):
#     """Check we can connect and run a trivial query"""
#     engine = env["engine"]
#     with engine.connect() as conn:
#         result = conn.execute(text("select 1")).scalar()
#         assert result == 1


# def test_pricing_report_table_reflected(env):
#     """Check that raw_data.pricing_report is available in env['tables']"""
#     assert "raw_data.pricing_report" in env["tables"]


from sqlalchemy import select, func

def test_pricing_report_count(env):
    """Check we can count rows from pricing_report"""
    Session = env["session_factory"]
    table = env["tables"]["raw_data.pricing_report"]

    with Session() as s:
        stmt = select(func.count()).select_from(table)
        count = s.execute(stmt).scalar_one()
        # Just assert it returns an integer
        assert isinstance(count, int)
        assert count >= 0
