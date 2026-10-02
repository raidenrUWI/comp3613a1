from sqlmodel import Session, func, select

from app.models.opportunity_application import OpportunityApplication


class OpportunityApplicationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_latest_for_student(
        self, student_id: int, opportunity_id: int
    ) -> OpportunityApplication | None:
        statement = (
            select(OpportunityApplication)
            .where(
                OpportunityApplication.student_id == student_id,
                OpportunityApplication.opportunity_id == opportunity_id,
            )
            .order_by(OpportunityApplication.opportunity_application_id.desc())
        )
        return self.db.exec(statement).first()

    def get_by_id(self, application_id: int) -> OpportunityApplication | None:
        return self.db.get(OpportunityApplication, application_id)

    def list_pending_for_admin(self, admin_id: int) -> list[OpportunityApplication]:
        statement = (
            select(OpportunityApplication)
            .where(
                OpportunityApplication.admin_id == admin_id,
                OpportunityApplication.status == "pending",
            )
            .order_by(OpportunityApplication.opportunity_application_id.desc())
        )
        return self.db.exec(statement).all()

    def count_accepted_for_opportunity(self, opportunity_id: int) -> int:
        statement = select(func.count()).where(
            OpportunityApplication.opportunity_id == opportunity_id,
            OpportunityApplication.status == "accepted",
        )
        return self.db.exec(statement).one()

    def count_rejected_for_student(
        self, student_id: int, opportunity_id: int
    ) -> int:
        statement = select(func.count()).where(
            OpportunityApplication.student_id == student_id,
            OpportunityApplication.opportunity_id == opportunity_id,
            OpportunityApplication.status == "rejected",
        )
        return self.db.exec(statement).one()

    def create(self, application: OpportunityApplication) -> OpportunityApplication:
        self.db.add(application)
        self.db.commit()
        self.db.refresh(application)
        return application

    def update_status(
        self, application: OpportunityApplication, status: str
    ) -> OpportunityApplication:
        application.status = status
        self.db.add(application)
        self.db.commit()
        self.db.refresh(application)
        return application