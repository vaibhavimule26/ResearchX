from bson import ObjectId
from fastapi import APIRouter, Depends
from app.auth.schemas import UserRegister, UserLogin
from app.auth.auth import create_access_token
from app.auth.security import hash_password, verify_password
from app.auth.jwt_handler import verify_token
from app.database.mongodb import users_collection
from app.services.activity_service import log_user_activity

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
    user_id = str(ObjectId())

    users_collection.insert_one({
        "user_id": user_id,
        "name": user.name,
        "email": user.email,
        "password": hashed_password
    })

    return {
        "message": "User Registered Successfully",
        "user_id": user_id,
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

    user_id = str(existing_user.get("user_id") or existing_user.get("_id"))
    token = create_access_token({"sub": user.email, "user_id": user_id})

    # Log user login activity
    try:
        log_user_activity(
            user_id=user_id,
            user_email=existing_user["email"],
            action_name="User Login",
            activity_type="auth",
            topic=None,
            paper_name=None,
            agent="Auth System",
            status="Completed",
            details=f"Logged in as {existing_user.get('name', existing_user['email'])}",
        )
    except Exception as e:
        print(f"[Login Activity Log Error]: {e}")

    return {
        "message": "Login Successful",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "user_id": user_id,
            "name": existing_user.get("name", ""),
            "email": existing_user.get("email", ""),
        }
    }


@router.get("/me")
def get_current_user(payload: dict = Depends(verify_token)):

    user = users_collection.find_one(
        {"email": payload["sub"]},
        {"password": 0}
    )

    if not user:
        return {
            "message": "User not found"
        }

    user_id = str(user.get("user_id") or user.get("_id"))
    return {
        "user_id": user_id,
        "name": user.get("name", ""),
        "email": user.get("email", ""),
    }