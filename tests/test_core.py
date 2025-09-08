import pytest
from quail.core import qtask, qcheck, Runner, CheckResult

@qtask(id="hello")
def hello(ctx):
    return "hi"

@qcheck(id="check_hello", requires=["hello"])
def check_hello(ctx):
    return CheckResult(id="check_hello", status="pass")

def test_runner_executes_tasks_and_checks():
    runner = Runner(env={}, params={})
    results = runner.run(["check_hello"])
    assert "hello" in results
    assert "check_hello" in results
    kind, result = results["check_hello"]
    assert kind == "check"
    assert result.status == "pass"


## REDSHIFT_URI=redshift+psycopg2://awsuser:Pg68h2ZHmVjml@redshift-cluster-2.clxqnyeopl7d.us-east-1.redshift.amazonaws.com:5439/db_quibble