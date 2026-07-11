## How to Contribute

- Firstly, Star the Repository.
- Take a look at the Existing [Issues](https://github.com/theeccentriccoder01/Spamlyser/issues) or create your own.
- Fork the Repo and create a Branch for any Issue that you are working upon.
- Create a Pull Request which will be promptly reviewed and suggestions would be added to improve it.
- Add Screenshots to help us know what this is all about.

## Setting Up Your Development Environment

### 1. Quick Setup (Recommended)

```bash
make setup
```

This installs dependencies, sets up pre-commit hooks, and runs them once.

### 2. Manual Setup

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
pre-commit install
```

### 3. Configure Your Editor

Install the [EditorConfig](https://editorconfig.org) plugin for your IDE
to automatically pick up the settings in `.editorconfig`.

## How to Make a Pull Request

**1.** Fork the repository by clicking on the Fork symbol at the top right corner.

**2.** Clone the forked repository.
```bash
git clone https://github.com/YOUR_USERNAME/Spamlyser.git
cd Spamlyser
```

**3.** Create a new branch:
```bash
git checkout -b YourBranchName
```

**4.** Make changes in source code.

**5.** Run tests to verify your changes:
```bash
PYTHONPATH=. pytest
```

**6.** Run the linter:
```bash
ruff check .
ruff format --check .
```

**7.** Stage your changes and commit:
```bash
git add .
git commit -m "<your_commit_message>"
```

**8.** Push your local commits to the remote repo:
```bash
git push origin YourBranchName
```

**9.** Create a [Pull Request](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request)

### Keeping Your Fork in Sync

```bash
git remote add upstream https://github.com/theeccentriccoder01/Spamlyser.git
git fetch upstream
git checkout main
git merge upstream/main
```

## Guidelines

- Follow the existing code style. Ruff formatting is enforced in CI.
- Write and update tests for any new functionality.
- Keep changes focused. Submit separate PRs for unrelated changes.
- Write clear [commit messages](http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html).
- Ensure CI passes (lint + tests) before requesting review.

## Resources

- [How to Contribute to Open Source](https://opensource.guide/how-to-contribute/)
- [Using Pull Requests](https://help.github.com/articles/about-pull-requests/)
- [GitHub Help](https://help.github.com)

## Reporting Security Vulnerabilities

We take security seriously and appreciate responsible disclosure.

**For non-sensitive issues** (e.g. a missing header, an informational finding
from a static analyser), open a public issue using the
[Security vulnerability report](.github/ISSUE_TEMPLATE/security_report.yml)
template.

**For sensitive vulnerabilities** that could be exploited in production (stored
XSS, injection, authentication bypass, data exposure), please **do not** open
a public issue. Email the maintainers directly instead so the issue can be
patched before it is publicly disclosed.

The project's CI pipeline runs automated security checks on every PR:

- **`pip-audit`** — scans all runtime dependencies for known CVEs.
- **`bandit`** — performs static analysis to catch common Python security
  anti-patterns (e.g. `eval()`, hard-coded passwords, unsafe `subprocess`
  calls).

You can run the same checks locally:

```bash
pip install pip-audit bandit
pip-audit -r requirements.txt
bandit -r . --exclude ./tests,./docs -l -i
```
