from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def create_user(user_data: UserCreate):
    with SessionLocal() as session:
        user = User(**user_data.model_dump())
        session.add(user)
        try:
            session.commit()
        except IntegrityError as exc:
            raise HTTPException(
                status_code=409,
                detail="A user with this mobile or email already exists",
            ) from exc
        session.refresh(user)
        return user


@router.get("", response_model=list[UserRead])
def list_users(
    user_type: str | None = Query(default=None, pattern=r"^(staff|customer|admin)$"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    with SessionLocal() as session:
        statement = select(User).order_by(User.id).limit(limit).offset(offset)

        if user_type is not None:
            statement = statement.where(User.user_type == user_type)

        return session.scalars(statement).all()


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int):
    with SessionLocal() as session:
        user = session.get(User, user_id)

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        return user


@router.patch("/{user_id}", response_model=UserRead)
def update_user(user_id: int, user_data: UserUpdate):
    with SessionLocal() as session:
        user = session.get(User, user_id)

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        changes = user_data.model_dump(exclude_unset=True)
        for field, value in changes.items():
            setattr(user, field, value)

        try:
            session.commit()
        except IntegrityError as exc:
            raise HTTPException(
                status_code=409,
                detail="A user with this mobile or email already exists",
            ) from exc
        session.refresh(user)
        return user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_user(user_id: int):
    with SessionLocal() as session:
        user = session.get(User, user_id)

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        session.delete(user)
        session.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
