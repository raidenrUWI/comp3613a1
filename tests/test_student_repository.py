from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlmodel import Session, SQLModel, create_engine

from app.repositories.student import StudentRepository
from app.models.admin import Admin
from app.models.hours_application import HoursApplication
from app.models.opportunity_application import OpportunityApplication
from app.models.student import Student
from app.models.volunteer_opportunity import VolunteerOpportunity
from app.routers.user_home import leaderboard_view


def test_student_repository_lists_ranked_by_hours_desc_and_class_filter():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        session.add_all(
            [
                Student(user_id=1, name="Ava", class_name="Alpha", hours=Decimal("12")),
                Student(user_id=2, name="Ben", class_name="Beta", hours=Decimal("30")),
                Student(user_id=3, name="Cara", class_name="Alpha", hours=Decimal("20")),
                Student(user_id=4, name="Drew", class_name="Beta", hours=Decimal("25")),
            ]
        )
        session.commit()

        repo = StudentRepository(session)

        overall = repo.list_ranked(None)
        assert [student.name for student in overall] == ["Ben", "Drew", "Cara", "Ava"]

        alpha = repo.list_ranked("Alpha")
        assert [student.name for student in alpha] == ["Cara", "Ava"]
        assert repo.list_class_names() == ["Alpha", "Beta"]
        assert [student.name for student in repo.list_ranked(None, "av")] == ["Ava"]
        assert [student.name for student in repo.list_ranked(None, str(overall[0].student_id))] == [
            "Ben"
        ]


@pytest.mark.asyncio
async def test_student_cannot_request_another_class_leaderboard():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(Student(user_id=1, name="Ava", class_name="Alpha"))
        session.commit()

        with pytest.raises(HTTPException) as error:
            await leaderboard_view(
                request=SimpleNamespace(),
                user=SimpleNamespace(id=1, role="regular_user"),
                db=session,
                class_name="Beta",
            )

        assert error.value.status_code == 403


def test_student_profile_updates_class_and_lists_verified_participation():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        student = Student(user_id=1, name="Ava", class_name="Alpha")
        admin = Admin(user_id=2, name="Admin")
        completed = VolunteerOpportunity(
            name="Campus Cleanup",
            description="Cleanup",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 1),
            max_applicants=10,
            image_url="https://example.com/cleanup.png",
        )
        not_completed = VolunteerOpportunity(
            name="Garden Day",
            description="Garden",
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 1),
            max_applicants=10,
            image_url="https://example.com/garden.png",
        )
        session.add_all([student, admin, completed, not_completed])
        session.commit()
        session.refresh(student)
        session.refresh(admin)
        session.refresh(completed)
        session.refresh(not_completed)

        completed_application = OpportunityApplication(
            student_id=student.student_id,
            admin_id=admin.admin_id,
            opportunity_id=completed.opportunity_id,
            status="accepted",
        )
        pending_application = OpportunityApplication(
            student_id=student.student_id,
            admin_id=admin.admin_id,
            opportunity_id=not_completed.opportunity_id,
            status="accepted",
        )
        session.add_all([completed_application, pending_application])
        session.commit()
        session.refresh(completed_application)
        session.refresh(pending_application)
        session.add_all(
            [
                HoursApplication(
                    opportunity_application_id=completed_application.opportunity_application_id,
                    hours=Decimal("2"),
                    note="Verified",
                    status="accepted",
                ),
                HoursApplication(
                    opportunity_application_id=pending_application.opportunity_application_id,
                    hours=Decimal("1"),
                    note="Awaiting review",
                    status="pending",
                ),
            ]
        )
        session.commit()

        repo = StudentRepository(session)
        updated = repo.update_class_name(student, "Beta")
        participated = repo.list_participated_opportunities(student.student_id)

        assert updated.class_name == "Beta"
        assert [(opportunity.name, hours) for opportunity, hours in participated] == [
            ("Campus Cleanup", Decimal("2.00"))
        ]
