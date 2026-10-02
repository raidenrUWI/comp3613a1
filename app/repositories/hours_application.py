from sqlmodel import Session, select

from app.models.hours_application import HoursApplication


class HoursApplicationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, hours_application_id: int) -> HoursApplication | None:
        return self.db.get(HoursApplication, hours_application_id)

    def list_pending(self) -> list[HoursApplication]:
        statement = (
            select(HoursApplication)
            .where(HoursApplication.status == "pending")
            .order_by(HoursApplication.hours_application_id.desc())
        )
        return self.db.exec(statement).all()

    def get_latest_for_application(
        self, opportunity_application_id: int
    ) -> HoursApplication | None:
        statement = (
            select(HoursApplication)
            .where(
                HoursApplication.opportunity_application_id
                == opportunity_application_id
            )
            .order_by(HoursApplication.hours_application_id.desc())
        )
        return self.db.exec(statement).first()

    def create(self, application: HoursApplication) -> HoursApplication:
        self.db.add(application)
        self.db.commit()
        self.db.refresh(application)
        return application