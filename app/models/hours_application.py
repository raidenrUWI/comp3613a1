from decimal import Decimal

from sqlmodel import Field, SQLModel


class HoursApplication(SQLModel, table=True):
    __tablename__ = "hours_application"

    hours_application_id: int | None = Field(default=None, primary_key=True)
    opportunity_application_id: int = Field(
        foreign_key="opportunity_application.opportunity_application_id", index=True
    )
    hours: Decimal = Field(gt=0)
    note: str
    status: str = Field(default="pending", index=True)