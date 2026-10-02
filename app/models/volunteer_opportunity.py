from datetime import date

from sqlmodel import Field, SQLModel


class VolunteerOpportunity(SQLModel, table=True):
    __tablename__ = "volunteer_opportunity"

    opportunity_id: int | None = Field(default=None, primary_key=True)

    # STUDENT SNIPPET START
    name: str
    description: str
    start_date: date
    end_date: date
    max_applicants: int
    image_url: str
    
    # STUDENT SNIPPET END