from sqlmodel import Field, SQLModel


class Admin(SQLModel, table=True):
    admin_id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True, index=True)
    name: str