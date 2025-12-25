# Claude Working Rules for VAS-MS

You are modifying a **frozen reference implementation** of VAS.

## Absolute Rules
- Do NOT use emojis in the code
- Do NOT refactor existing architecture
- Do NOT rename services
- Do NOT introduce new frameworks or tools
- Do NOT split frontend into multiple codebases
- Do NOT change MediaSoup behavior
- Do NOT change backend APIs unless explicitly instructed

## Allowed Changes
- Small, explicit configuration changes
- Docker Compose adjustments when clearly requested
- Environment-variable–based behavior only
- Additive changes that do not break existing flows

## Frontend Rules
- There is ONE frontend codebase
- Docker frontend = production-style
- Local `npm run dev` = development
- No port numbers hardcoded in frontend code

## Goal Orientation
Optimize for:
- developer iteration speed
- minimal diff
- reversibility