from sqlmodel import Field, SQLModel


class OpportunityApplication(SQLModel, table=True):
    __tablename__ = "opportunity_application"

    opportunity_application_id: int | None = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="student.student_id", index=True)
    admin_id: int = Field(foreign_key="admin.admin_id", index=True)
    opportunity_id: int = Field(
        foreign_key="volunteer_opportunity.opportunity_id", index=True
    )
    status: str = Field(default="pending", index=True)