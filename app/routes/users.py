from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict
from app import UserCreateResponse, UserWithRelations, UserResponse, Other, BaseUser, UserFull, \
    UserListResponse, User, logger, get_db, exception_handler, user_by_api_key, user_by_id, check_unique_user, get_users

users_router = APIRouter(prefix="/api/users", tags=["Users"])
app_logger = logger.bind(name="app")


@users_router.post("/", status_code=201, response_model=UserCreateResponse)
@exception_handler()
async def create_user(
        user_data: BaseUser,
        db: AsyncSession = Depends(get_db),
        api_key: str = Header(..., convert_underscores=False)):
    """Function of the registration of a new user"""
    app_logger.info(f"POST/api/users")

    if not await check_unique_user(db, user_data.username, user_data.email, api_key):
        raise HTTPException(status_code=400, detail={"result": False,
                                                     "error_type": 400,
                                                     "error_message": f"Already registered"})
    new_user = User(**user_data.model_dump())
    await new_user.set_api_key(api_key=api_key)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    app_logger.info(f"User created successfully (user_id={new_user.id})")
    return {"result": True, "id": new_user.id}


@users_router.get("/me", status_code=200, response_model=UserResponse)
@exception_handler()
async def get_authorized_user(db: AsyncSession = Depends(get_db),
                              api_key: str = Header(..., convert_underscores=False)):
    """The function of obtaining an authorized user"""
    app_logger.info(f"GET/api/users/me")

    user = await user_by_api_key(api_key=api_key, db=db, _with="all")
    user_response = UserWithRelations(
        id=user.id,
        username=user.username,
        followers=[Other(id=f.id, username=f.username) for f in user.followers],
        following=[Other(id=f.id, username=f.username) for f in user.following]
    )
    return UserResponse(result=True, user=user_response)


@users_router.get("/{user_id}", status_code=200, response_model=UserResponse)
@exception_handler()
async def get_user_by_id(user_id: int, db: AsyncSession = Depends(get_db)):
    """The function of obtaining a user by ID"""
    app_logger.info(f"GET/api/users/{user_id}")

    user = await user_by_id(user_id=user_id, db=db, _with="all")
    user_response = UserWithRelations(
        id=user.id,
        username=user.username,
        followers=[Other(id=f.id, username=f.username) for f in user.followers],
        following=[Other(id=f.id, username=f.username) for f in user.following]
    )
    return UserResponse(result=True, user=user_response)


@users_router.get("/", status_code=200, response_model=UserListResponse)
@exception_handler()
async def get_all_users(
        db: AsyncSession = Depends(get_db),
        api_key: str = Header(..., convert_underscores=False),
        limit: int = Query(10, ge=1, le=30),
        offset: int = Query(0, ge=0)):
    """The function of obtaining all users"""
    app_logger.info(f"GET/api/users")

    await user_by_api_key(api_key=api_key, db=db)
    users = await get_users(db=db, limit=limit, offset=offset)
    users_data = []
    for u in users:
        users_data.append(
            UserFull(
                id=u.id,
                username=u.username,
                about_me=u.about_me,
                email=u.email
            )
        )

    return UserListResponse(result=True, users=users_data)


@users_router.post("/{user_id}/follow", status_code=201)
@exception_handler()
async def follow(
        user_id: int,
        db: AsyncSession = Depends(get_db),
        api_key: str = Header(..., convert_underscores=False)):
    """Follow func"""
    app_logger.info(f"POST/api/users/{user_id}/follow")

    existing_user = await user_by_api_key(api_key=api_key, db=db)

    if existing_user.id == user_id:
        raise HTTPException(status_code=400, detail={"result": False,
                                                     "error_type": 400,
                                                     "error_message": "Invalid user_id"})
    user = await user_by_id(user_id=user_id, db=db)
    await existing_user.follow(db, user)
    app_logger.info(f"User id={existing_user.id} follow successfully id={user_id}")
    return {"result": True}


@users_router.delete("/{user_id}/unfollow", status_code=200)
@exception_handler()
async def unfollow(
        user_id: int,
        db: AsyncSession = Depends(get_db),
        api_key: str = Header(..., convert_underscores=False)) -> Dict[str, bool]:
    """Unfollow func"""
    app_logger.info(f"DELETE/api/users/{user_id}/unfollow")

    existing_user = await user_by_api_key(api_key=api_key, db=db)

    if existing_user.id == user_id:
        raise HTTPException(status_code=400, detail={"result": False,
                                                     "error_type": 400,
                                                     "error_message": "Invalid user_id"})
    user = await user_by_id(user_id=user_id, db=db)
    await existing_user.unfollow(db, user)
    app_logger.info(f"User id={existing_user.id} unfollow successfully id={user_id}")
    return {"result": True}
