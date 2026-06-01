# oss-ready

`oss-ready` is a small command-line health check for repositories that are about to be published as open source. It looks for the basics maintainers and contributors expect: a useful README, a license, packaging metadata, tests, CI, contribution notes, and working local Markdown links.

It is intentionally boring in the best way: no network calls, no telemetry, no language-server setup, and no assumptions about a specific stack.

## Features

- Scores a repository from 0 to 100 using practical open-source readiness checks.
- Flags missing project basics such as `README.md`, `LICENSE`, tests, CI, and contribution docs.
- Checks Markdown files for broken local links, missing image alt text, and unlabeled fenced code blocks.
- Supports human-readable terminal output or JSON for CI.
- Uses only the Python standard library at runtime.

## Installation

Install from a local checkout:

```bash
python3 -m pip install .
```

Or run it without installing:

```bash
PYTHONPATH=src python3 -m oss_ready .
```

## Usage

Scan the current repository:

```bash
oss-ready .
```

Fail a CI job if the score falls below a threshold:

```bash
oss-ready . --fail-under 80
```

Write machine-readable output:

```bash
oss-ready . --json
```

Example output:

```text
oss-ready: /path/to/project
score: 91/100

PASS  README        README.md exists and has a title
PASS  License       License file found
WARN  Community     Add CONTRIBUTING.md or CODE_OF_CONDUCT.md

Markdown issues:
WARN  docs/guide.md:12  fenced code block has no language
FAIL  README.md:43      local link target does not exist: docs/setup.md
```

## What It Checks

| Check | Why it matters |
| --- | --- |
| README quality | Contributors need a fast explanation, install path, and usage example. |
| License | Users need permission to use and modify the project. |
| Project metadata | Package managers and tools need a reliable project definition. |
| Tests | A public project should show how behavior is verified. |
| CI | Maintainers and contributors need repeatable checks. |
| Community files | Contribution and conduct files reduce friction for new collaborators. |
| Markdown links | Broken docs make projects feel abandoned quickly. |

## Development

Run the tests:

```bash
python3 -m unittest discover -s tests
```

Run the tool against itself:

```bash
PYTHONPATH=src python3 -m oss_ready . --fail-under 80
```

## Design Notes

The scoring model is deliberately transparent and conservative. A low score is not a moral judgment; it is a checklist of chores before publishing. The Markdown checker only validates local files and anchors, because external link checking is slower, noisier, and less reliable in CI.

## License

MIT License. See [LICENSE](LICENSE).

