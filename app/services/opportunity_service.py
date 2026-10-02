from dataclasses import dataclass
from decimal import Decimal

from app.models.admin import Admin
from app.models.hours_application import HoursApplication
from app.models.opportunity_application import OpportunityApplication
from app.models.volunteer_opportunity import VolunteerOpportunity
from app.repositories.admin import AdminRepository
from app.repositories.hours_application import HoursApplicationRepository
from app.repositories.opportunity import VolunteerOpportunityRepository
from app.repositories.opportunity_application import OpportunityApplicationRepository
from app.repositories.student import StudentRepository


@dataclass
class OpportunityCard:
    opportunity: VolunteerOpportunity
    admins: list[Admin]
    application: OpportunityApplication | None
    hours_application: HoursApplication | None
    capacity_reached: bool
    places_left: int
    denied_applications: int


class VolunteerOpportunityService:
    def __init__(
        self,
        opportunity_repo: VolunteerOpportunityRepository,
        opportunity_application_repo: OpportunityApplicationRepository,
        hours_application_repo: HoursApplicationRepository,
        student_repo: StudentRepository,
        admin_repo: AdminRepository,
        user_id: int,
    ):
        self.opportunity_repo = opportunity_repo
        self.opportunity_application_repo = opportunity_application_repo
        self.hours_application_repo = hours_application_repo
        self.student_repo = student_repo
        self.admin_repo = admin_repo
        self.user_id = user_id

    def list_browsable(self) -> list[OpportunityCard]:
        student = self.student_repo.get_by_user_id(self.user_id)
        if student is None or student.student_id is None:
            raise ValueError("A student profile is required to browse opportunities")

        admins = self.admin_repo.get_all()
        cards = []
        for opportunity in self.opportunity_repo.list_browsable():
            if opportunity.opportunity_id is None:
                continue
            application = self.opportunity_application_repo.get_latest_for_student(
                student.student_id, opportunity.opportunity_id
            )
            hours_application = None
            if application is not None and application.status == "accepted":
                if application.opportunity_application_id is not None:
                    hours_application = (
                        self.hours_application_repo.get_latest_for_application(
                            application.opportunity_application_id
                        )
                    )
            denied_applications = (
                self.opportunity_application_repo.count_rejected_for_student(
                    student.student_id, opportunity.opportunity_id
                )
            )
            accepted_count = (
                self.opportunity_application_repo.count_accepted_for_opportunity(
                    opportunity.opportunity_id
                )
            )
            places_left = max(0, opportunity.max_applicants - accepted_count)
            cards.append(
                OpportunityCard(
                    opportunity=opportunity,
                    admins=admins,
                    application=application,
                    hours_application=hours_application,
                    capacity_reached=places_left == 0,
                    places_left=places_left,
                    denied_applications=denied_applications,
                )
            )
        return cards

    def apply_for_opportunity(
        self, opportunity_id: int, admin_id: int
    ) -> OpportunityApplication:
        student = self.student_repo.get_by_user_id(self.user_id)
        if student is None or student.student_id is None:
            raise ValueError("A student profile is required to apply")
        opportunity = self.opportunity_repo.get_by_id(opportunity_id)
        if opportunity is None:
            raise ValueError("Opportunity not found")
        admin = self.admin_repo.get_by_id(admin_id)
        if admin is None:
            raise ValueError("Choose a valid reviewing admin")

        latest = self.opportunity_application_repo.get_latest_for_student(
            student.student_id, opportunity_id
        )
        if latest is not None and latest.status in {"pending", "accepted"}:
            raise ValueError("You already have an active application")
        if (
            self.opportunity_application_repo.count_rejected_for_student(
                student.student_id, opportunity_id
            )
            >= 3
        ):
            raise ValueError("You have reached the application limit for this opportunity")

        return self.opportunity_application_repo.create(
            OpportunityApplication(
                student_id=student.student_id,
                admin_id=admin_id,
                opportunity_id=opportunity_id,
                status="pending",
            )
        )

    def request_hours(
        self, opportunity_application_id: int, hours: Decimal, note: str
    ) -> HoursApplication:
        student = self.student_repo.get_by_user_id(self.user_id)
        if student is None or student.student_id is None:
            raise ValueError("A student profile is required to request hours")
        application = self.opportunity_application_repo.get_by_id(
            opportunity_application_id
        )
        if application is None or application.student_id != student.student_id:
            raise ValueError("Application not found")
        if application.status != "accepted":
            raise ValueError("Hours can only be requested for an accepted application")
        if hours <= 0 or not note.strip():
            raise ValueError("Enter a positive hour amount and a note")
        if application.opportunity_application_id is None:
            raise ValueError("Application must be saved before requesting hours")

        latest = self.hours_application_repo.get_latest_for_application(
            application.opportunity_application_id
        )
        if latest is not None and latest.status in {"pending", "accepted"}:
            raise ValueError("Hours have already been requested for this application")

        return self.hours_application_repo.create(
            HoursApplication(
                opportunity_application_id=application.opportunity_application_id,
                hours=hours,
                note=note.strip(),
                status="pending",
            )
        )

    def review_opportunity_application(
        self, opportunity_application_id: int, admin_id: int, decision: str
    ) -> OpportunityApplication:
        if decision not in {"approve", "reject"}:
            raise ValueError("Choose approve or reject")

        application = self.opportunity_application_repo.get_by_id(
            opportunity_application_id
        )
        if application is None or application.admin_id != admin_id:
            raise ValueError("Opportunity application not found")
        if application.status != "pending":
            raise ValueError("This opportunity application has already been reviewed")

        if decision == "approve":
            opportunity = self.opportunity_repo.get_by_id(application.opportunity_id)
            if opportunity is None:
                raise ValueError("Opportunity not found")
            accepted_count = self.opportunity_application_repo.count_accepted_for_opportunity(
                application.opportunity_id
            )
            if accepted_count >= opportunity.max_applicants:
                raise ValueError("This opportunity is full")

        status = "accepted" if decision == "approve" else "rejected"
        return self.opportunity_application_repo.update_status(application, status)