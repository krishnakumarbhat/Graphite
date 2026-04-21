# Contributing to Graphite

Thanks for contributing.

## Development setup
1. Install dependencies for each app:
   - `frontend/`: `yarn install`
   - `mobile/`: `npm install`
   - `backend/`: `pip3 install --user -r requirements.txt`
2. Start services:
   - Web: `yarn --cwd frontend start`
   - Mobile web preview: `npm --prefix mobile run web`
   - Backend API: `python3 -m uvicorn --app-dir backend server:app --reload --port 8001`

## Branch and PR rules
- Use short feature branches: `feat/<topic>`, `fix/<topic>`, `docs/<topic>`.
- Keep PRs focused and small.
- Include screenshots for UI changes (web and mobile when relevant).
- Update docs when behavior or commands change.

## Coding rules
- Do not commit secrets, API keys, or private tokens.
- Keep web and mobile UX aligned (same content hierarchy, platform-appropriate controls).
- Prefer incremental changes over large rewrites.
- Add or update tests for critical logic changes.

## Commit style
Use Conventional Commits:
- `feat: ...`
- `fix: ...`
- `docs: ...`
- `refactor: ...`
- `chore: ...`

## Security reporting
Please do not open public issues for vulnerabilities.
See `SECURITY.md` for private disclosure instructions.
