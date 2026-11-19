# Contributing

## Branches (never commit to main directly)
- feature/<short-desc>   new work
- fix/<short-desc>       bug fixes
- docs/<short-desc>      documentation only
- refactor/<short-desc>  no behavior change

## Commits
type(scope): summary
Types: feat, fix, docs, test, refactor, chore
Example: feat(ui): add two-column responsive grid

## Pull requests
- One branch = one PR. Say what changed and how you tested it.
- Another teammate reviews and merges. Review within a few hours.
- Never push to main directly.

## Who owns what
| Files | Owner |
|---|---|
| db/ (schema.sql, db_init.py, crud_operations.py) | DB person |
| app.py, helpers.py, routes/ | Flask person |
| static/js/ | JS person |
| static/style.css, HTML structure in templates/ | UI (Abhiraj) |
| docs/, README.md | Product Lead (Abhiraj) |

## Frozen contracts
Field names, routes, JSON shape and element IDs are in docs/CONTRACTS.md.
Do not rename anything in it without telling the group first.
