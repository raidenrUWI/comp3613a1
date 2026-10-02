from decimal import Decimal

from fastapi import Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.repositories.admin import AdminRepository
from app.repositories.hours_application import HoursApplicationRepository
from app.repositories.opportunity import VolunteerOpportunityRepository
from app.repositories.opportunity_application import OpportunityApplicationRepository
from app.repositories.student import StudentRepository
from app.services.opportunity_service import VolunteerOpportunityService
from app.services.student_progress_service import StudentProgressService
from app.utilities.flash import flash
from . import router, templates


def _opportunity_service(db: SessionDep, user_id: int) -> VolunteerOpportunityService:
    return VolunteerOpportunityService(
        opportunity_repo=VolunteerOpportunityRepository(db),
        opportunity_application_repo=OpportunityApplicationRepository(db),
        hours_application_repo=HoursApplicationRepository(db),
        student_repo=StudentRepository(db),
        admin_repo=AdminRepository(db),
        user_id=user_id,
    )


@router.get("/app", response_class=HTMLResponse)
async def user_home_view(
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    if user.id is None:
        return RedirectResponse(url=request.url_for("login_view"), status_code=303)
    if user.role == "admin":
        return RedirectResponse(url=request.url_for("admin_home_view"), status_code=303)
    opportunity_service = _opportunity_service(db, user.id)

    return templates.TemplateResponse(
        request=request,
        name="app.html",
        context={
            "user": user,
            "opportunities": opportunity_service.list_browsable(),
        }
    )


@router.get("/app/leaderboard", response_class=HTMLResponse, name="leaderboard_view")
async def leaderboard_view(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    class_name: str | None = None,
    search: str | None = None,
):
    if user.id is None:
        return RedirectResponse(url=request.url_for("login_view"), status_code=303)

    student_repo = StudentRepository(db)
    selected_class = class_name.strip() if class_name and class_name.strip() else None
    search_term = search.strip() if search and search.strip() else None
    viewer_student_id = None
    if user.role == "admin":
        visible_classes = student_repo.list_class_names()
    else:
        student = student_repo.get_by_user_id(user.id)
        if student is None:
            flash(request, "Student profile not found.", "danger")
            return RedirectResponse(url=request.url_for("user_home_view"), status_code=303)
        if selected_class is not None and selected_class != student.class_name:
            raise HTTPException(
                status_code=403,
                detail="Students can only view the overall or their own class leaderboard.",
            )
        viewer_student_id = student.student_id
        visible_classes = [student.class_name]
        search_term = None

    return templates.TemplateResponse(
        request=request,
        name="leaderboard.html",
        context={
            "user": user,
            "students": student_repo.list_ranked(
                selected_class, search_term if user.role == "admin" else None
            ),
            "classes": visible_classes,
            "class_name": selected_class,
            "search_term": search_term,
            "viewer_student_id": viewer_student_id,
        },
    )


@router.get("/app/progress", response_class=HTMLResponse, name="student_progress_view")
async def student_progress_view(
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    if user.id is None:
        return RedirectResponse(url=request.url_for("login_view"), status_code=303)
    if user.role == "admin":
        return RedirectResponse(url=request.url_for("admin_home_view"), status_code=303)

    student_repo = StudentRepository(db)
    student = student_repo.get_by_user_id(user.id)
    if student is None or student.student_id is None:
        flash(request, "Student profile not found.", "danger")
        return RedirectResponse(url=request.url_for("user_home_view"), status_code=303)

    progress = StudentProgressService().build_roadmap(student.hours or Decimal("0"))
    return templates.TemplateResponse(
        request=request,
        name="progress.html",
        context={
            "user": user,
            "student": student,
            "progress": progress,
            "participated_opportunities": student_repo.list_participated_opportunities(
                student.student_id
            ),
        },
    )


@router.get("/app/profile", response_class=HTMLResponse, name="student_profile_view")
async def student_profile_view(
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    if user.id is None:
        return RedirectResponse(url=request.url_for("login_view"), status_code=303)
    if user.role == "admin":
        return RedirectResponse(url=request.url_for("admin_profile_view"), status_code=303)

    student_repo = StudentRepository(db)
    student = student_repo.get_by_user_id(user.id)
    if student is None or student.student_id is None:
        flash(request, "Student profile not found.", "danger")
        return RedirectResponse(url=request.url_for("user_home_view"), status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "user": user,
            "student": student,
            "admin": None,
        },
    )


@router.post("/app/profile/class", name="update_student_class")
async def update_student_class(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    class_name: str = Form(),
):
    if user.id is None:
        return RedirectResponse(url=request.url_for("login_view"), status_code=303)
    if user.role == "admin":
        return RedirectResponse(url=request.url_for("admin_profile_view"), status_code=303)

    student_repo = StudentRepository(db)
    student = student_repo.get_by_user_id(user.id)
    normalized_class = class_name.strip()
    if student is None:
        flash(request, "Student profile not found.", "danger")
    elif not normalized_class:
        flash(request, "Enter a class name.", "danger")
    else:
        student_repo.update_class_name(student, normalized_class)
        flash(request, "Class updated.")
    return RedirectResponse(url=request.url_for("student_profile_view"), status_code=303)


@router.post("/app/opportunities/{opportunity_id}/apply", name="apply_opportunity")
async def apply_opportunity(
    request: Request,
    opportunity_id: int,
    user: AuthDep,
    db: SessionDep,
    admin_id: int = Form(),
):
    if user.id is None:
        return RedirectResponse(url=request.url_for("login_view"), status_code=303)
    service = _opportunity_service(db, user.id)
    try:
        service.apply_for_opportunity(opportunity_id, admin_id)
        flash(request, "Application submitted.")
    except ValueError as exc:
        flash(request, str(exc), "danger")
    return RedirectResponse(url=request.url_for("user_home_view"), status_code=303)


@router.post(
    "/app/applications/{opportunity_application_id}/hours",
    name="request_hours",
)
async def request_hours(
    request: Request,
    opportunity_application_id: int,
    user: AuthDep,
    db: SessionDep,
    hours: int = Form(),
    minutes: int = Form(default=0),
    note: str = Form(),
):
    if user.id is None:
        return RedirectResponse(url=request.url_for("login_view"), status_code=303)
    total_hours = Decimal(hours) + (Decimal(minutes) / Decimal("60"))
    service = _opportunity_service(db, user.id)
    try:
        service.request_hours(opportunity_application_id, total_hours, note)
        flash(request, "Hours request submitted for verification.")
    except ValueError as exc:
        flash(request, str(exc), "danger")
    return RedirectResponse(url=request.url_for("user_home_view"), status_code=303)

    
