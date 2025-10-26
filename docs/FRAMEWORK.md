# FRAMEWORK.md

## Vision
A continuous test harness for the ManuOptima optimisation engine that validates every generated plan before it's consumed by downstream systems.

## Components
- **Validator Service**: The Python validator (validator.py) as a CLI and library. Containerised and runnable in CI.
- **Test Data Generator**: A data factory to produce thousands of permutations, using property-based testing (Hypothesis) + domain-aware rules.
- **CI Integration**: Run validation on every PR and on nightly full-suite runs. Fail the build if critical regressions appear.
- **Orchestration**: Use GitHub Actions / GitLab CI to run pytest, collect artifacts, run mutation tests and report coverage.
- **Reporting**: Build HTML reports + Slack alerts for failures, with attached offending plan JSON and validator trace.
- **Monitoring**: Track trends of validator failures across time; auto-label recurring failures for triage.

## Tools & Practices
- Pytest for assertions and parametrised negative tests.
- Docker for consistent runtime; publish image to registry. Helm charts to deploy validator as readiness gate.

## Data Strategy
- Seeded test corpus of known-good and known-bad plans.
- Generative tests to create realistic high-volume scenarios.
- Use synthetic timezones and holiday calendars for robust schedule checks.

## Developer Experience
- Validator CLI returns machine-readable JSON output in addition to human logs.
- Git hook to run a quick smoke validator locally before pushing.