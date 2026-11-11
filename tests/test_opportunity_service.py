from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.services.opportunity_service import VolunteerOpportunityService


@pytest.fixture
def opportunity_service():
    opportunity_repo = Mock()
    opportunity_application_repo = Mock()
    hours_application_repo = Mock()
    student_repo = Mock()
    admin_repo = Mock()
    student_repo.get_by_user_id.return_value = SimpleNamespace(student_id=11)

    service = VolunteerOpportunityService(
        opportunity_repo=opportunity_repo,
        opportunity_application_repo=opportunity_application_repo,
        hours_application_repo=hours_application_repo,
        student_repo=student_repo,
        admin_repo=admin_repo,
        user_id=101,
    )
    return (
        service,
        opportunity_repo,
        opportunity_application_repo,
        hours_application_repo,
        admin_repo,
    )


def test_apply_creates_pending_application_for_student_and_admin(
    opportunity_service,
):
    service, opportunity_repo, application_repo, _, admin_repo = opportunity_service
    expected_application = object()
    opportunity_repo.get_by_id.return_value = object()
    admin_repo.get_by_id.return_value = object()
    application_repo.get_latest_for_student.return_value = None
    application_repo.count_rejected_for_student.return_value = 0
    application_repo.create.return_value = expected_application

    result = service.apply_for_opportunity(opportunity_id=21, admin_id=31)

    assert result is expected_application
    created_application = application_repo.create.call_args.args[0]
    assert created_application.student_id == 11
    assert created_application.opportunity_id == 21
    assert created_application.admin_id == 31
    assert created_application.status == "pending"


@pytest.mark.parametrize("status", ["pending", "accepted"])
def test_apply_rejects_an_existing_active_application(opportunity_service, status):
    service, opportunity_repo, application_repo, _, admin_repo = opportunity_service
    opportunity_repo.get_by_id.return_value = object()
    admin_repo.get_by_id.return_value = object()
    application_repo.get_latest_for_student.return_value = SimpleNamespace(
        status=status
    )

    with pytest.raises(ValueError, match="active application"):
        service.apply_for_opportunity(opportunity_id=21, admin_id=31)

    application_repo.create.assert_not_called()


def test_request_hours_rejects_non_positive_amount(opportunity_service):
    service, _, application_repo, hours_repo, _ = opportunity_service
    application_repo.get_by_id.return_value = SimpleNamespace(
        opportunity_application_id=51,
        student_id=11,
        status="accepted",
    )

    with pytest.raises(ValueError, match="positive hour amount"):
        service.request_hours(
            opportunity_application_id=51,
            hours=Decimal(0),
            note="Completed cleanup",
        )

    hours_repo.create.assert_not_called()


def test_review_rejects_approval_when_opportunity_is_full(opportunity_service):
    service, opportunity_repo, application_repo, _, _ = opportunity_service
    application_repo.get_by_id.return_value = SimpleNamespace(
        opportunity_application_id=61,
        opportunity_id=21,
        admin_id=31,
        status="pending",
    )
    opportunity_repo.get_by_id.return_value = SimpleNamespace(max_applicants=2)
    application_repo.count_accepted_for_opportunity.return_value = 2

    with pytest.raises(ValueError, match="opportunity is full"):
        service.review_opportunity_application(
            opportunity_application_id=61,
            admin_id=31,
            decision="approve",
        )

    application_repo.update_status.assert_not_called()
