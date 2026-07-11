# Security Policy for Spamlyser Pro

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| latest  | ✅                 |
| < latest| ❌                 |

We only provide security patches for the most recent release.  Please upgrade to the latest version before reporting vulnerabilities.

## Reporting a Vulnerability

Spamlyser Pro handles user-submitted SMS content and uses local machine-learning models.  While the application is designed for local or trusted-network deployment, we take security seriously.

**Do not file a public issue** for security vulnerabilities.  Instead, send a description to the repository maintainer via one of these channels:

- **GitHub Security Advisory**: Use the "Report a vulnerability" link under the repository's Security tab.
- **Email**: Contact the repository owner through their GitHub profile.

Please include:

- A clear description of the vulnerability and its impact.
- Steps to reproduce the issue.
- Your recommended fix (if known).

We will acknowledge receipt within 72 hours and aim to release a fix within 14 days.

## Scope

The following are considered in scope for this security policy:

- Remote code execution vulnerabilities
- Data leakage or unintended exposure of sensitive information
- CSV injection (CWE-1236) or similar formula injection attacks
- Stored or reflected cross-site scripting (XSS)
- SQL injection (if applicable)
- Authentication / authorization bypass

## Out of Scope

- Vulnerabilities in third-party dependencies (report those to the upstream maintainer)
- Denial-of-service attacks that require physical access or local network access
- Social engineering attacks against the project maintainers
- Theoretical attacks that require write access to the repository

## Recognition

We thank all security researchers who responsibly disclose vulnerabilities.  With your permission, we will add your name to our acknowledgements section.
