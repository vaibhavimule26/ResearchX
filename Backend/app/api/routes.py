from fastapi import APIRouter, Depends
from app.auth.schemas import UserRegister, UserLogin
from app.auth.auth import create_access_token
from app.auth.security import hash_password, verify_password
from app.auth.jwt_handler import verify_token
from app.database.mongodb import users_collection

router = APIRouter()


@router.get("/health")
def health():
    return {
        "status": "OK",
        "message": "ResearchX Backend is Healthy 🚀"
    }


@router.post("/register")
def register(user: UserRegister):

    existing_user = users_collection.find_one({"email": user.email})

    if existing_user:
        return {
            "message": "User already exists"
        }

    hashed_password = hash_password(user.password)

    users_collection.insert_one({
        "name": user.name,
        "email": user.email,
        "password": hashed_password
    })

    return {
        "message": "User Registered Successfully"
    }


@router.post("/login")
def login(user: UserLogin):

    existing_user = users_collection.find_one({"email": user.email})

    if not existing_user:
        return {
            "message": "Invalid Email"
        }

    if not verify_password(user.password, existing_user["password"]):
        return {
            "message": "Invalid Password"
        }

    token = create_access_token({"sub": user.email})

    return {
        "message": "Login Successful",
        "access_token": token,
        "token_type": "bearer"
    }


@router.get("/me")
def get_current_user(payload: dict = Depends(verify_token)):

    user = users_collection.find_one(
        {"email": payload["sub"]},
        {"_id": 0, "password": 0}
    )

    if not user:
        return {
            "message": "User not found"
        }

    return user