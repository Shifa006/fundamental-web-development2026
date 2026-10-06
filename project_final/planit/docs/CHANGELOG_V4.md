# Changelog — Presentation-Ready v4

Built on Planit Pastel Quest v3 / Final Clean v2.

## Authentication

- added Django login page
- added POST-only logout
- added session-based protection middleware
- added JSON 401 response for unauthenticated APIs
- added safe `next` redirect handling
- added wrong-password feedback
- added demo-user option to `seed_demo`

## Presentation features

- added Mint Day / Night Quest theme mode using CSS variables + localStorage
- added semantic `<ul><li>` navigation
- added Top Focus card backed by Python attention sorting
- added login zoom/pulse motion and reduced-motion accessibility
- added presentation Q&A, code map, and runserver flow notes

## Tests

- updated existing API/frontend tests to authenticate
- added authentication test suite
- added Top Focus service/API regression coverage
- final automated suite: 64 tests passing
