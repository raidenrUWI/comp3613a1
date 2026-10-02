from app.repositories.user import UserRepository
from app.repositories.student import StudentRepository
from app.utilities.security import encrypt_password, verify_password, create_access_token
from app.schemas.user import RegularUserCreate
from typing import Optional

class AuthService:
    def __init__(
        self,
        user_repo: UserRepository,
        student_repo: StudentRepository | None = None,
    ):
        self.user_repo = user_repo
        self.student_repo = student_repo

    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        user = self.user_repo.get_by_username(username)
        if not user or not verify_password(plaintext_password=password, encrypted_password=user.password):
            return None
        access_token = create_access_token(data={"sub": f"{user.id}", "role": user.role})
        return access_token

    def register_user(
        self, username: str, email: str, password: str, class_name: str
    ):
        new_user = RegularUserCreate(
            username=username, 
            email=email, 
            password=encrypt_password(password)
        )
        user = self.user_repo.create(new_user)
        if self.student_repo is not None:
            self.student_repo.ensure_for_user(user, class_name)
        return user
