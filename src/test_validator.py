import subprocess, sys, pathlib
HERE = pathlib.Path(__file__).parent / "test_data" # means the folder containing this test file. and add sub folder
VALID = HERE / "valid_plan.json"
INVALIDS = [
    HERE / "invalid_plan_quantity.json",
    HERE / "invalid_plan_sizing.json",
    HERE / "invalid_plan_downtime.json",
    HERE / "invalid_plan_overlap.json"
]

def run_validator(path):
    proc = subprocess.run([sys.executable, str(path.parent.parent / "validator.py"), str(path)], capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr

def test_valid_plan():
    rc, out = run_validator(VALID)
    print(out)
    assert rc == 0, "Valid plan should exit 0"

import pytest
# Run the next test function multiple time on this INVALIDS List
@pytest.mark.parametrize("p", INVALIDS)
def test_invalid_plans(p):
    rc, out = run_validator(p)
    print(out)
    assert rc == 1, f"Invalid plan {p.name} should exit 1"
