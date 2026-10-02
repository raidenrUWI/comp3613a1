from decimal import Decimal

from sqlalchemy import or_
from sqlmodel import Session, func, select

from app.models.hours_application import HoursApplication
from app.models.opportunity_application import OpportunityApplication
from app.models.volunteer_opportunity import VolunteerOpportunity
from app.models.student import Student
from app.models.user import User


class StudentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id: int) -> Student | None:
        statement = select(Student).where(Student.user_id == user_id)
        return self.db.exec(statement).one_or_none()

    def get_by_id(self, student_id: int) -> Student | None:
        return self.db.get(Student, student_id)

    def update_class_name(self, student: Student, class_name: str) -> Student:
        student.class_name = class_name
        self.db.add(student)
        self.db.commit()
        self.db.refresh(student)
        return student

    def list_participated_opportunities(
        self, student_id: int
    ) -> list[tuple[VolunteerOpportunity, Decimal]]:
        statement = (
            select(VolunteerOpportunity, func.sum(HoursApplication.hours))
            .join(
                OpportunityApplication,
                OpportunityApplication.opportunity_id
                == VolunteerOpportunity.opportunity_id,
            )
            .join(
                HoursApplication,
                HoursApplication.opportunity_application_id
                == OpportunityApplication.opportunity_application_id,
            )
            .where(
                OpportunityApplication.student_id == student_id,
                HoursApplication.status == "accepted",
            )
            .group_by(
                VolunteerOpportunity.opportunity_id,
                VolunteerOpportunity.name,
                VolunteerOpportunity.description,
                VolunteerOpportunity.start_date,
                VolunteerOpportunity.end_date,
                VolunteerOpportunity.max_applicants,
                VolunteerOpportunity.image_url,
            )
            .order_by(VolunteerOpportunity.end_date.desc())
        )
        return self.db.exec(statement).all()

    def list_class_names(self) -> list[str]:
        statement = select(Student.class_name).distinct().order_by(Student.class_name)
        rows = self.db.exec(statement).all()
        values: list[str] = []
        for row in rows:
            value = row[0] if isinstance(row, tuple) else row
            if value:
                values.append(str(value))
        return values

    def list_ranked(
        self, class_name: str | None, search_term: str | None = None
    ) -> list[Student]:
        statement = select(Student)
        if class_name is not None:
            statement = statement.where(Student.class_name == class_name)
        if search_term:
            search_conditions = [Student.name.ilike(f"%{search_term}%")]
            if search_term.isdecimal():
                search_conditions.append(Student.student_id == int(search_term))
            statement = statement.where(or_(*search_conditions))
        statement = statement.order_by(Student.hours.desc(), Student.name.asc())
        return self.db.exec(statement).all()

    def ensure_for_user(self, user: User, class_name: str = "Unassigned") -> Student:
        if user.id is None:
            raise ValueError("A saved user is required to create a student profile")
        profile = self.get_by_user_id(user.id)
        if profile is not None:
            return profile

        profile = Student(
            user_id=user.id,
            name=user.username,
            class_name=class_name.strip() or "Unassigned",
        )
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile