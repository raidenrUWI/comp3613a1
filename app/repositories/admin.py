from sqlmodel import Session, select

from app.models.admin import Admin
from app.models.user import User


class AdminRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id: int) -> Admin | None:
        statement = select(Admin).where(Admin.user_id == user_id)
        return self.db.exec(statement).one_or_none()

    def get_by_id(self, admin_id: int) -> Admin | None:
        return self.db.get(Admin, admin_id)

    def get_all(self) -> list[Admin]:
        return self.db.exec(select(Admin).order_by(Admin.name)).all()

    def ensure_for_user(self, user: User) -> Admin:
        if user.id is None:
            raise ValueError("A saved user is required to create an admin profile")
        profile = self.get_by_user_id(user.id)
        if profile is not None:
            return profile

        profile = Admin(user_id=user.id, name=user.username)
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile