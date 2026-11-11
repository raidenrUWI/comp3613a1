# Student Awards — Test Plan and Results

## Project information

- **Project:** Student Awards (incentive system)
- **Description:** A school volunteer-hours platform where students browse and apply for volunteer opportunities, submit accepted hours for verification, and track progress on class and overall leaderboards. Administrators review opportunity and hours applications.
- **Project report:** [Assignment 2 report, diagrams, wireframe, and tests](./report.md)

## Design references

- [Use-case diagram](./diagrams/use-case.png)
- [ERD in the assignment report](./report.md#model-diagram)
- [Student-crafted wireframe sheet](./wireframes/wireframe.png)

The UAT cases below refer to panels in the wireframe sheet: opportunities (top-left), opportunity details and actions (top-middle), admin application queues (top-right), student leaderboards (bottom-left), and admin leaderboard search (bottom-right).

## User acceptance test plan

Use the deployed application or run the local application with `python manage.py run`. Before running the opportunity scenarios, initialize a test/demo database with `python manage.py init`; this resets the configured database. Record actual results and attach screenshots only after manually completing each case.

| ID | Wireframe reference | Actor / setup | Acceptance steps | Expected result | Status / evidence |
|---|---|---|---|---|---|
| UAT-01 | Opportunities and opportunity details (top-left / top-middle) | Student; signed in as `bob` | Open Opportunities; inspect an opportunity card and its detail; choose an admin and apply. After an admin accepts it, submit a positive number of hours with a note. | The opportunity shows its application state; the accepted application permits an hours request; the request is visible for admin review. | **Passed.** Student confirmed the submitted request used positive hours and a non-empty note. Screenshots show application submission, pending status, hours form, request confirmation, and accepted status in [UAT-01 evidence](./testing/reports/uat-01/). |
| UAT-02 | Admin application queues (top-right) | Admin; a pending opportunity application and hours request exist | Open Applications; review a pending opportunity application, then approve a pending hours request. | Both decisions update their respective statuses; approving hours increases the student's verified-hours total. | **Passed from supplied screenshots.** Before/after images show both queues go from 1 open to 0 open; the app confirms hours approval and total update. See [UAT-02 evidence](./testing/reports/uat-02/). |
| UAT-03 | Student leaderboards (bottom-left) | Student with a class profile and recorded hours | Open Leaderboards; switch between overall and the student's class view. | Rows are ordered by verified hours; the selected student's position is highlighted as shown in the wireframe. | **Passed.** Supplied screenshots show the overall leaderboard ranked by hours with Bob highlighted, and the Class 1 leaderboard filtered to its two students with Bob highlighted. See [UAT-03 evidence](./testing/reports/uat-03/). |
| UAT-04 | Admin leaderboard search (bottom-right) | Admin; seeded student data exists | Open Leaderboards; search by student ID and by class; use the show-all view. | Search/filter results match the requested student or class; show-all displays the available leaderboard rows. | **Passed per student report.** Screenshot shows the admin leaderboard with class tabs and the student ID/name search control; search and show-all actions were reported working as expected. See [UAT-04 evidence](./testing/reports/uat-04/). |

### UAT execution record

Do not mark a case passed until a human has run it against the UI and checked the result against the cited wireframe. Record tester, date, actual result, and screenshot filename here:

| ID | Tester / date | Actual result | Screenshot |
|---|---|---|---|
| UAT-01 | Student screenshots and confirmation, 2026-11-07 | Application submitted and shown pending; accepted application enabled hours entry; positive hours and a non-empty note were submitted; the request was later shown accepted. | [Screenshot set](./testing/reports/uat-01/) |
| UAT-02 | Student screenshots supplied, 2026-11-07 | Admin queue screenshot shows one pending opportunity application and one 3h hours request. After review, both queues show zero open; the app confirms hours approved and student total updated. | [Screenshot set](./testing/reports/uat-02/) |
| UAT-03 | Student screenshots supplied, 2026-11-07 | Overall rows descend by hours; Bob is highlighted at rank 1. Class 1 view contains Bob and Alice in rank order, with Bob highlighted. | [Screenshot set](./testing/reports/uat-03/) |
| UAT-04 | Student report and screenshot supplied, 2026-11-07 | Student reports ID search, class filtering, and show-all worked as expected. Screenshot shows the admin leaderboard class views and search control. | [Screenshot](./testing/reports/uat-04/01-admin-leaderboard-class-and-search.png) |

## Unit test plan

Unit tests isolate service logic and use mock repositories where persistence is not the subject of the test.

| ID | Test | Input / condition | Expected result | Implemented in |
|---|---|---|---|---|
| UT-01 | Build progress roadmap | 12.5 verified hours | Correct current hours, next milestone, progress percentage, and hours remaining | `tests/test_student_progress_service.py` |
| UT-02 | Final progress milestone | 32 verified hours | All milestones achieved; no next milestone; zero hours remaining | `tests/test_student_progress_service.py` |
| UT-03 | Submit opportunity application | Valid student, opportunity, and admin; no active/denied limit | Creates a pending application associated with those records | `tests/test_opportunity_service.py` |
| UT-04 | Prevent duplicate active application | Latest application is pending or accepted | Raises a validation error and does not create another application | `tests/test_opportunity_service.py` |
| UT-05 | Validate hours request | Zero requested hours | Raises a validation error and does not create a request | `tests/test_opportunity_service.py` |
| UT-06 | Enforce opportunity capacity | Approval attempted when accepted applications reach capacity | Raises a validation error and does not update the application | `tests/test_opportunity_service.py` |

Run the unit plan:

```powershell
python -m pytest -q tests/test_student_progress_service.py tests/test_opportunity_service.py
```

## Integration test plan

Integration tests exercise connected components using an isolated in-memory SQLite database so they do not depend on or modify the configured app database.

| ID | Test | Components | Expected result | Implemented in |
|---|---|---|---|---|
| IT-01 | Health check | FastAPI app and health route | `GET /health` returns HTTP 200 and `{"ok": true}` | `tests/test_api_integration.py` |
| IT-02 | User-list API | FastAPI route, dependency override, SQLModel session, SQLite, response schema | `GET /api/users` returns HTTP 200 and user `id`, `username`, and `email`, without password or role fields | `tests/test_api_integration.py` |
| IT-03 | Ranked leaderboard repository | Student repository and SQLite | Overall/class filters, name/ID search, and descending rank return the expected rows | `tests/test_student_repository.py` |
| IT-04 | Opportunity application repository | Application repository and SQLite | Pending records are scoped to the assigned admin; accepted counts match the opportunity | `tests/test_opportunity_application_repository.py` |

Run the integration plan:

```powershell
python -m pytest -q tests/test_api_integration.py tests/test_student_repository.py tests/test_opportunity_application_repository.py
```

## API tests — Postman

Import [the Student Awards Postman collection](../postman/StudentAwards.postman_collection.json) into Postman. Start the app with `python manage.py run`, keep the collection variable `baseUrl` at `http://127.0.0.1:5000` (or set it to the target environment), and run the collection.

| Request | Assertions |
|---|---|
| `GET {{baseUrl}}/health` | HTTP 200; response body is exactly `{"ok": true}` |
| `GET {{baseUrl}}/api/users` | HTTP 200; response is a JSON array; every row contains exactly `id`, `username`, and `email` |

The collection was executed against an isolated local app with Newman, a CLI runner for the Postman collection format. Both requests and all four assertions passed. The exported execution data is [postman-run.json](./testing/reports/postman-run.json), and the rendered result screenshot is [postman-collection-report.png](./testing/reports/postman-collection-report.png).

## Automated test results

Run these commands from the repository root to reproduce the JUnit reports:

```powershell
python -m pytest -q tests/test_student_progress_service.py tests/test_opportunity_service.py --junitxml=docs/testing/reports/unit-tests.xml
python -m pytest -q tests/test_api_integration.py tests/test_student_repository.py tests/test_opportunity_application_repository.py --junitxml=docs/testing/reports/integration-tests.xml
```

Both pytest groups passed with no failures. Pytest also emitted the Starlette TestClient/httpx deprecation warning shown in its output. The result screenshots are rendered from the actual JUnit/Newman result files; those source files remain available for detailed test evidence. Do not report a passing UAT until a human has run the UI cases.

| Report | Result | Evidence |
|---|---|---|
| Unit tests | **7 passed, 0 failed** | [JUnit XML](./testing/reports/unit-tests.xml) · [result screenshot](./testing/reports/unit-tests-report.png) |
| Integration tests | **6 passed, 0 failed** | [JUnit XML](./testing/reports/integration-tests.xml) · [result screenshot](./testing/reports/integration-tests-report.png) |
| Postman API tests | **2 requests, 4 assertions passed, 0 failed** | [Newman JSON](./testing/reports/postman-run.json) · [result screenshot](./testing/reports/postman-collection-report.png) |
| User acceptance tests | **UAT-01 through UAT-04 passed** | UAT-04 search/show-all outcomes are recorded from the student's manual test report; screenshot shows the admin search UI and class views. |
