# Backend Review Log

## 2026-05-17

### Checked

- Championship schedule generation still exists as one backend action:
  `POST /api/v1/schedule/championships/{tournament_id}/generate`.
- Match schedule can still be manually edited through match update,
  reschedule, referee assignment, and ticket price endpoints while the match is
  not finished.
- One-match protocol generation now exists through:
  `POST /api/v1/matches/{match_id}/generate-protocol`.
- Full-season simulation now exists through:
  `POST /api/v1/seasons/{season_id}/generate-protocols`.
- The compatible random-result endpoint remains available:
  `POST /api/v1/matches/{match_id}/generate-random-result`.

### Problems Found And Fixed

- Protocol generation previously filled score and events, but did not guarantee
  referee assignment or match lineups. It now auto-assigns an available referee,
  generates missing starting lineups for both teams, and uses lineup players for
  generated protocol events.
- Full-season simulation could not exist as a single backend workflow. It now
  prevalidates season matches and rolls back the whole operation if a match is
  finished, cancelled, already has events, lacks a referee option, or cannot
  form valid lineups.
- Teams did not have an emblem field. Added optional `emblem_url` with
  HTTP/HTTPS validation and an Alembic migration.

### Validation Notes

- Generated starting lineups must have 11 starters and exactly one goalkeeper.
- Existing manual lineups are respected, but protocol generation rejects them if
  they are incomplete or have zero/multiple starting goalkeepers.
- Protocol generation requires at least one referee in the user's scope, or an
  already assigned available referee on the match.
- Generated protocol events match the generated final score.
- Full-season simulation updates championship standings and player statistics
  after generation.

### Verification

- `.venv\Scripts\python.exe -m pytest` passed: 146 tests.
- Remaining local warning: pytest cannot write `.pytest_cache` because of local
  filesystem permissions. This does not affect backend behavior.
