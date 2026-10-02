from datetime import date

from sqlmodel import Session, select

from app.models.volunteer_opportunity import VolunteerOpportunity


class VolunteerOpportunityRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_browsable(self) -> list[VolunteerOpportunity]:
        # STUDENT SNIPPET START
        statement = select(VolunteerOpportunity).where(
            VolunteerOpportunity.end_date >= date.today()
        )
        results = self.db.exec(statement)
        return results.all()

    def get_by_id(self, opportunity_id: int) -> VolunteerOpportunity | None:
        return self.db.get(VolunteerOpportunity, opportunity_id)

    def list_all(self) -> list[VolunteerOpportunity]:
        statement = select(VolunteerOpportunity).order_by(
            VolunteerOpportunity.start_date
        )
        return self.db.exec(statement).all()

    def create(self, opportunity: VolunteerOpportunity) -> VolunteerOpportunity:
        self.db.add(opportunity)
        self.db.commit()
        self.db.refresh(opportunity)
        return opportunity
        # STUDENT SNIPPET END