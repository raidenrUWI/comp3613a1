from decimal import Decimal

from fastapi import Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies.auth import AdminDep
from app.dependencies.session import SessionDep
from app.repositories.admin import AdminRepository
from app.repositories.hours_application import HoursApplicationRepository
from app.repositories.opportunity import VolunteerOpportunityRepository
from app.repositories.opportunity_application import OpportunityApplicationRepository
from app.repositories.student import StudentRepository
from app.services.opportunity_service import VolunteerOpportunityService
from app.utilities.flash import flash
from . import router, templates


@router.get("/admin", response_class=HTMLResponse)
async def admin_home_view(
    request: Request,
    user: AdminDep,
    db: SessionDep,
):
    hours_repo = HoursApplicationRepository(db)
    application_repo = OpportunityApplicationRepository(db)
    admin_repo = AdminRepository(db)
    student_repo = StudentRepository(db)
    opportunity_repo = VolunteerOpportunityRepository(db)

    opportunity_requests = []
    admin = admin_repo.get_by_user_id(user.id) if user.id is not None else None
    if admin is not None and admin.admin_id is not None:
        for application in application_repo.list_pending_for_admin(admin.admin_id):
            student = student_repo.get_by_id(application.student_id)
            opportunity = opportunity_repo.get_by_id(application.opportunity_id)
            if student is None or opportunity is None:
                continue
            opportunity_requests.append(
                {
                    "application": application,
                    "student": student,
                    "opportunity": opportunity,
                }
            )

    requests = []
    for item in hours_repo.list_pending():
        application = application_repo.get_by_id(item.opportunity_application_id)
        if application is None:
            continue
        student = student_repo.get_by_id(application.student_id)
        opportunity = opportunity_repo.get_by_id(application.opportunity_id)
        if student is None or opportunity is None:
            continue
        requests.append(
            {
                "hours_request": item,
                "application": application,
                "student": student,
                "opportunity": opportunity,
            }
        )

    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "user": user,
            "opportunity_requests": opportunity_requests,
            "requests": requests,
        },
    )


@router.get("/admin/profile", response_class=HTMLResponse, name="admin_profile_view")
async def admin_profile_view(
    request: Request,
    user: AdminDep,
    db: SessionDep,
):
    admin = AdminRepository(db).get_by_user_id(user.id) if user.id is not None else None
    if admin is None:
        flash(request, "Admin profile not found.", "danger")
        return RedirectResponse(url=request.url_for("admin_home_view"), status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "user": user,
            "student": None,
            "admin": admin,
            "participated_opportunities": [],
        },
    )


@router.post(
    "/admin/opportunities/{opportunity_application_id}/review",
    name="review_opportunity_application",
)
async def review_opportunity_application(
    request: Request,
    opportunity_application_id: int,
    user: AdminDep,
    db: SessionDep,
    decision: str = Form(...),
):
    admin = AdminRepository(db).get_by_user_id(user.id) if user.id is not None else None
    if admin is None or admin.admin_id is None:
        flash(request, "Admin profile not found.", "danger")
        return RedirectResponse(url=request.url_for("admin_home_view"), status_code=303)

    service = VolunteerOpportunityService(
        opportunity_repo=VolunteerOpportunityRepository(db),
        opportunity_application_repo=OpportunityApplicationRepository(db),
        hours_application_repo=HoursApplicationRepository(db),
        student_repo=StudentRepository(db),
        admin_repo=AdminRepository(db),
        user_id=user.id,
    )
    try:
        service.review_opportunity_application(
            opportunity_application_id, admin.admin_id, decision
        )
        flash(request, "Opportunity application reviewed.")
    except ValueError as exc:
        flash(request, str(exc), "danger")
    return RedirectResponse(url=request.url_for("admin_home_view"), status_code=303)


@router.post("/admin/hours/{hours_application_id}/review", name="review_hours")
async def review_hours_application(
    request: Request,
    hours_application_id: int,
    user: AdminDep,
    db: SessionDep,
    decision: str = Form(...),
):
    hours_repo = HoursApplicationRepository(db)
    student_repo = StudentRepository(db)

    hours_request = hours_repo.get_by_id(hours_application_id)
    if hours_request is None:
        flash(request, "Hours request not found.", "danger")
        return RedirectResponse(url=request.url_for("admin_home_view"), status_code=303)

    if decision == "approve":
        hours_request.status = "accepted"
        application = OpportunityApplicationRepository(db).get_by_id(
            hours_request.opportunity_application_id
        )
        if application is not None:
            student = student_repo.get_by_id(application.student_id)
            if student is not None:
                student.hours = (student.hours or Decimal("0")) + hours_request.hours
                db.add(student)
        flash(request, "Hours approved and student total updated.")
    elif decision == "reject":
        hours_request.status = "rejected"
        flash(request, "Hours request rejected.")
    else:
        flash(request, "Choose approve or reject.", "danger")
        return RedirectResponse(url=request.url_for("admin_home_view"), status_code=303)

    db.add(hours_request)
    db.commit()
    return RedirectResponse(url=request.url_for("admin_home_view"), status_code=303)
