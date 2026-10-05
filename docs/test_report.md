# Test Report - Student-Document-OCR

## 1. Summary

| Suite | Command | Passed | Failed | Skipped | Duration | Coverage % |
|-------|---------|--------|--------|---------|----------|------------|
| Backend | `pytest ...` | 106 | 3 | 0 | 26.70s | 45% |
| Frontend Lint | `npm run lint` | - | - | 1 | - | N/A (No eslint) |
| Frontend Type | `npm run build`| 1 | 0 | 0 | 9.57s | N/A |
| OCR Bench | `bench_ocr.py` | 0 | 0 | 1 (skipped)| - | N/A |

## 2. Test Failures

1. `test_p0_auth_security.py::test_p0_1_signup_duplicate_email_returns_409`
   - **Severity**: High
   - **Proposed Fix**: Add a database query check to verify if the email is already registered before creating a new user, and return a 409 status code if it exists.
2. `test_rbac_security.py::test_unauthenticated_file_download_rejected`
   - **Severity**: High
   - **Proposed Fix**: Ensure that the endpoint for downloading files requires a valid authentication token, potentially using `Depends(get_current_user)`.
3. `test_rbac_security.py::test_unauthenticated_search_rejected`
   - **Severity**: High
   - **Proposed Fix**: Ensure the search endpoint enforces authentication by adding `Depends(get_current_user)` to the router dependencies.

## 3. Coverage Gaps

Modules and endpoints with no tests, ranked by risk:
1. **Auth & Security**: Partially tested, gaps in some edge cases.
2. **Documents Access Control**: Some routes lack complete coverage (24% covered).
3. **OCR Pipeline**: `vietocr_engine.py` (0% covered), `trocr_engine.py` (0% covered).
4. **Postprocessing**: `text_postprocessing` module has low coverage.
5. **Worker**: `celery_app.py` has no actual task tests, `tasks.py` is at 80%.
6. **Storage**: `storage_service.py` is at 54%.

## 4. Flaky/Slow & Network-Dependent Tests

- `test_p0_document_security.py::test_p0_12_duplicate_mounts_removed` (3.72s)
- `test_documents.py::test_upload_document_success` (2.52s)
- `test_p0_auth_security.py::test_p0_1_signup_duplicate_email_returns_409` (2.39s)
- `test_p0_document_security.py::test_p0_11_single_use_file_ticket_lifecycle` (2.21s)
- `test_p1_database_reliability.py::test_p1_13_production_fails_fast_on_postgres_failure` (2.14s)

## 5. Security Findings

- **Tracked Secrets**: `backend/app/core/config.py` contains default seed passwords (`admin123`, `password123`).
- **Hygiene**: `backend/alembic.ini` contains `CHANGE_ME` credentials.

## 6. Project & Testing Configuration Findings

- **Missing Dependencies**: `requirements.txt` was missing `slowapi` and `aiosqlite`.
- **Environment Validation**: `app_env` in `config.py` only accepts `development`, `staging`, or `production`; it does not accept `test`.
- **Accidental Live DB Connections**: The original `conftest.py`'s `init_db()` runs migrations and seeding against whatever database is configured in the environment. Tests must strictly override `DATABASE_URL` via environment variables to avoid touching real Supabase projects.
- **Untracked Artifacts (for .gitignore)**: `.venv_test/`, `.agy_runs/`, `.env_test` were created during testing and should be added to `.gitignore`.

## 7. TODO List

- [P1] Remove hardcoded passwords from `backend/app/core/config.py`.
- [P2] ...

## 7. Not Verified

- **End-to-End Real DB**: Tests hit a dummy SQLite/local postgres, not a real Supabase instance.
- **GPU Inference**: OCR runs on CPU fallback for tests.
