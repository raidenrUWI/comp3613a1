from sqlmodel import Session, SQLModel, create_engine

from app.models.opportunity_application import OpportunityApplication
from app.repositories.opportunity_application import OpportunityApplicationRepository


def test_list_pending_for_admin_returns_only_assigned_pending_applications():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        session.add_all(
            [
                OpportunityApplication(
                    student_id=1,
                    admin_id=1,
                    opportunity_id=1,
                    status="pending",
                ),
                OpportunityApplication(
                    student_id=2,
                    admin_id=2,
                    opportunity_id=1,
                    status="pending",
                ),
                OpportunityApplication(
                    student_id=3,
                    admin_id=1,
                    opportunity_id=2,
                    status="accepted",
                ),
            ]
        )
        session.commit()

        repo = OpportunityApplicationRepository(session)
        applications = repo.list_pending_for_admin(1)

        assert len(applications) == 1
        assert applications[0].student_id == 1
        assert repo.count_accepted_for_opportunity(1) == 0
        assert repo.count_accepted_for_opportunity(2) == 1