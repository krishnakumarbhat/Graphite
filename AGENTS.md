---
name: Graphite AGENTS
description: >
  Use when: how to run Graphite backend; how to run mobile/web preview; setup dev; run frontend builds; run tests.
applyTo:
  - "Graphite/**"
exclude:
  - "**/node_modules/**"
  - "**/build/**"
---

Purpose
- Project-scoped instructions and quickstart for Graphite developers and AI agents.

Primary docs
- Graphite/README.md
- Graphite/docs/ARCHITECTURE.md

Common tasks
- Backend quickstart
  - `cd Graphite/backend`
  - `cp .env.example .env`
  - `pip3 install --user -r requirements.txt`
  - `python3 -m uvicorn --app-dir . server:app --reload --port 8001`
- Mobile / Web preview
  - `cd Graphite/mobile`
  - `npm install && npm run web`

Notes
- Separate Node and Python environments per subfolder. Use per-subfolder commands rather than global workspace commands.
- Link to docs rather than embedding long instructions.
