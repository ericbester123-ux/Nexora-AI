# Sprint Progress Summary

## Sprint 6 — DONE
- **AI Proposal Generation & User Preferences** — complete
- **Test count:** 342 passing

## Sprint 7 — IN PROGRESS
- **Proposal Review Workflow**
- Models, schemas, endpoints, and tests implemented
- **Endpoints added:**
  - `POST /proposals/{id}/review` — move to Under Review
  - `POST /proposals/{id}/ready` — mark Ready to Submit
  - `POST /proposals/{id}/submitted` — mark Submitted
  - `POST /proposals/{id}/archive` — archive proposal
  - `GET /proposals/{id}/readiness` — readiness check
  - `POST /proposals/{id}/edit` — edit (creates new version)
  - `POST /proposals/{id}/rollback` — rollback to version
  - `GET /proposals/{id}/compare` — compare versions
  - `GET /proposals/{id}/versions` — list version history
  - `GET /proposals/{id}/versions/{version_id}` — get version
  - `GET/POST /proposals/{id}/notes` — list/create notes
  - `PUT/DELETE /proposals/notes/{note_id}` — update/delete note
  - `GET /proposals/{id}/audit-log` — audit trail
- **Test count:** 360 passing (53 new: 35 unit + 18 integration)
