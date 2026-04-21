# Security Policy

## Supported scope
- Backend API (`backend/`)
- Web app (`frontend/`)
- Mobile app (`mobile/`)

## Reporting a vulnerability
Do **not** create public issues for security findings.

Please report privately with:
- Impact summary
- Reproduction steps
- Affected files/endpoints
- Suggested fix (if available)

Maintainers will acknowledge within 72 hours and provide remediation updates.

## Secret handling
- Never commit `.env` files.
- Use `.env.example` as the template.
- Rotate keys immediately if exposed.
