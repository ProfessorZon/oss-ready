# Contributing

Thanks for considering a contribution to `oss-ready`.

## Local Setup

```bash
git clone https://github.com/ProfessorZon/oss-ready.git
cd oss-ready
python3 -m pip install -e .
```

## Checks

Run the test suite:

```bash
python3 -m unittest discover -s tests
```

Run the scanner against this repository:

```bash
oss-ready . --fail-under 80
```

## Pull Requests

Please keep changes focused and include tests for new checks or parsing behavior. If a new readiness rule is subjective, document the reasoning in the README so users can understand the tradeoff.
