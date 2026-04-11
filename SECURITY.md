# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.2.x (latest) | ✅ |
| < 0.2.0 | ❌ |

Only the latest minor release receives security fixes. We recommend always using the latest version.

## Reporting a Vulnerability

**Please do not report security vulnerabilities via public GitHub Issues.**

To report a vulnerability, email the maintainers at:

**security@vstorm.co**

Include in your report:
- Description of the vulnerability
- Steps to reproduce (CLI invocation or generated project behavior)
- Affected versions
- Potential impact
- Any suggested fix (optional)

## Response Timeline

| Stage | Target |
|-------|--------|
| Acknowledgement | Within 48 hours |
| Initial assessment | Within 5 business days |
| Fix or mitigation | Within 30 days for critical/high |
| Public disclosure | After fix is released |

We follow coordinated disclosure — we ask that you give us time to release a fix before public disclosure.

## Scope

In scope:
- Vulnerabilities in the CLI generator itself (`fastapi-fullstack` package)
- Security issues in the generated project template code (auth, JWT handling, SSRF, etc.)
- Unsafe defaults in generated project configuration
- Path traversal or template injection via cookiecutter inputs

Out of scope:
- Vulnerabilities in third-party dependencies (report to the respective project)
- Security issues introduced by users after project generation
- Issues requiring physical access to the machine

## Security in Generated Projects

**CLI generator:**
- `pip-audit` in CI — scans for known CVEs on every build
- `ty` type checking — prevents type-related vulnerabilities
- Ruff linting — enforces safe coding patterns

**Generated projects include:**
- **SSRF protection (CWE-918)** — `validate_webhook_url()` blocks private/reserved/loopback IPs and validates DNS resolution
- **JWT + API Key authentication** — Secure defaults with bcrypt password hashing and refresh token rotation
- **RBAC** — Role-based access control out of the box
- **CORS** — Explicit origin allowlists
- **SQL injection prevention** — SQLAlchemy parameterized queries
- **Input validation** — All API inputs validated via Pydantic v2 strict schemas
- **Secret management** — `.env`-based configuration, secrets never committed
- **HTTP-only cookies** — For token storage on the frontend
- **Secret key validation** — Minimum 32-character key enforcement

## Acknowledgements

We thank all security researchers who responsibly disclose vulnerabilities to us. Confirmed reporters will be credited in the release notes unless they prefer to remain anonymous.
