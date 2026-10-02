from decimal import Decimal

from sqlmodel import Field, SQLModel


class Student(SQLModel, table=True):

    # STUDENT SNIPPET START
    
    student_id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True, index=True)
    name: str
    class_name: str
    hours: Decimal = Field(default=Decimal("0"), ge=0)
    # STUDENT SNIPPET END