import os
import json
import html
import secrets
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from urllib.parse import urlencode, quote, unquote

from dotenv import load_dotenv
import httpx
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse

from app.database.mongodb import users_collection
from app.auth.auth import create_access_token
from app.services.activity_service import log_user_activity

# Ensure Backend/.env is reliably loaded regardless of execution context or working directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_PATH = os.path.join(BASE_DIR, ".env")

def reload_env_if_needed():
    """Reloads Backend/.env without clobbering non-empty process environment variables with empty file entries."""
    if os.path.exists(ENV_PATH):
        from dotenv import dotenv_values
        file_values = dotenv_values(ENV_PATH)
        for key, val in file_values.items():
            if val is not None and val.strip():
                os.environ[key] = val.strip()
            elif key not in os.environ:
                os.environ[key] = ""

reload_env_if_needed()

router = APIRouter(
    prefix="/auth",
    tags=["OAuth Authentication"],
)

# In-memory store for pending OAuth states and mock auth codes
_PENDING_STATES: Dict[str, Dict[str, Any]] = {}
_AUTH_CODES: Dict[str, Dict[str, Any]] = {}


def get_oauth_config() -> Dict[str, str]:
    """Retrieve OAuth client configuration from environment."""
    reload_env_if_needed()
    return {
        "google_client_id": os.getenv("GOOGLE_CLIENT_ID", "").strip(),
        "google_client_secret": os.getenv("GOOGLE_CLIENT_SECRET", "").strip(),
        "github_client_id": os.getenv("GITHUB_CLIENT_ID", "").strip(),
        "github_client_secret": os.getenv("GITHUB_CLIENT_SECRET", "").strip(),
        "backend_url": os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/"),
        "default_frontend_url": os.getenv("FRONTEND_URL", "http://localhost:8080").rstrip("/"),
    }


def validate_provider_config(provider: str) -> Optional[str]:
    """
    Validates whether required credentials are set for the given OAuth provider.
    Returns None if valid, or a descriptive user-facing message if unconfigured.
    """
    cfg = get_oauth_config()
    provider = provider.lower().strip()
    if provider == "google":
        cid = cfg["google_client_id"]
        csec = cfg["google_client_secret"]
        missing = []
        if not cid or "placeholder" in cid.lower() or "your_" in cid.lower():
            missing.append("GOOGLE_CLIENT_ID")
        if not csec or "placeholder" in csec.lower() or "your_" in csec.lower():
            missing.append("GOOGLE_CLIENT_SECRET")
        if missing:
            return f"Google OAuth is not configured. Please set {' and '.join(missing)} in Backend/.env"
        return None

    elif provider == "github":
        cid = cfg["github_client_id"]
        csec = cfg["github_client_secret"]
        missing = []
        if not cid or "placeholder" in cid.lower() or "your_" in cid.lower():
            missing.append("GITHUB_CLIENT_ID")
        if not csec or "placeholder" in csec.lower() or "your_" in csec.lower():
            missing.append("GITHUB_CLIENT_SECRET")
        if missing:
            return f"GitHub OAuth is not configured. Please set {' and '.join(missing)} in Backend/.env"
        return None

    return f"Unsupported OAuth provider: {provider}"


def is_live_configured(provider: str) -> bool:
    """Check if provider has genuine non-empty OAuth credentials."""
    return validate_provider_config(provider) is None


# ==========================================================
# Safe Diagnostics Endpoint (Never exposes credentials)
# ==========================================================
@router.get("/diagnostics")
def oauth_diagnostics():
    """
    Safe diagnostics endpoint reporting only configuration status and presence flags.
    Never exposes secret or client values.
    """
    cfg = get_oauth_config()
    google_err = validate_provider_config("google")
    github_err = validate_provider_config("github")

    return JSONResponse(
        content={
            "env_path": ENV_PATH,
            "env_file_exists": os.path.exists(ENV_PATH),
            "backend_url": cfg["backend_url"],
            "frontend_url": cfg["default_frontend_url"],
            "google_oauth": {
                "client_id_configured": bool(cfg["google_client_id"] and "placeholder" not in cfg["google_client_id"].lower() and "your_" not in cfg["google_client_id"].lower()),
                "client_secret_configured": bool(cfg["google_client_secret"] and "placeholder" not in cfg["google_client_secret"].lower() and "your_" not in cfg["google_client_secret"].lower()),
                "is_ready": google_err is None,
                "status_message": "Ready" if google_err is None else google_err,
                "callback_url": f"{cfg['backend_url']}/auth/callback/google",
            },
            "github_oauth": {
                "client_id_configured": bool(cfg["github_client_id"] and "placeholder" not in cfg["github_client_id"].lower() and "your_" not in cfg["github_client_id"].lower()),
                "client_secret_configured": bool(cfg["github_client_secret"] and "placeholder" not in cfg["github_client_secret"].lower() and "your_" not in cfg["github_client_secret"].lower()),
                "is_ready": github_err is None,
                "status_message": "Ready" if github_err is None else github_err,
                "callback_url": f"{cfg['backend_url']}/auth/callback/github",
            },
        }
    )


# ==========================================================
# 1. OAuth Initiate / Login Endpoint
# ==========================================================
@router.get("/login/{provider}")
def oauth_login(
    provider: str,
    request: Request,
    origin: Optional[str] = None,
    redirect_url: Optional[str] = None,
):
    """
    Initiates OAuth 2.0 flow for Google or GitHub.
    Directs to the interactive branded consent screen before continuing the OAuth flow.
    """
    provider = provider.lower().strip()
    if provider not in ("google", "github"):
        raise HTTPException(status_code=400, detail=f"Unsupported OAuth provider: {provider}")

    cfg = get_oauth_config()

    # Determine the target frontend origin to return to
    referer = request.headers.get("referer") or ""
    client_origin = origin or redirect_url
    if not client_origin and referer:
        parts = referer.split("/")
        if len(parts) >= 3:
            client_origin = f"{parts[0]}//{parts[1]}{parts[2]}"
    if not client_origin:
        client_origin = cfg["default_frontend_url"]
    client_origin = client_origin.rstrip("/")

    # Generate secure state
    state = secrets.token_urlsafe(24)
    callback_url = f"{cfg['backend_url']}/auth/callback/{provider}"
    _PENDING_STATES[state] = {
        "provider": provider,
        "origin": client_origin,
        "callback_url": callback_url,
        "created_at": datetime.now(timezone.utc),
    }

    # Open the branded consent screen before continuing the OAuth flow
    consent_url = f"/auth/consent/{provider}?state={state}"
    return RedirectResponse(url=consent_url)


# ==========================================================
# 2. Interactive OAuth Authorization Screen (Consent Portal)
# ==========================================================
@router.get("/consent/{provider}", response_class=HTMLResponse)
def oauth_consent_page(provider: str, state: str):
    """
    Renders an interactive, branded OAuth authorization dialog matching the reference design.
    """
    provider = provider.lower().strip()
    if provider not in ("google", "github"):
        raise HTTPException(status_code=400, detail=f"Unsupported OAuth provider: {provider}")

    if not state or state not in _PENDING_STATES:
        return HTMLResponse(
            """<!DOCTYPE html>
            <html lang="en">
            <head><meta charset="UTF-8"><title>Session Expired — ResearchX</title></head>
            <body style="background:#090D16;color:#F8FAFC;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;">
                <div style="background:#111827;border:1px solid #1E293B;padding:32px;border-radius:18px;text-align:center;max-width:400px;box-shadow:0 20px 40px rgba(0,0,0,0.6);">
                    <h3 style="margin:0 0 10px 0;font-size:18px;">Session Expired</h3>
                    <p style="color:#94A3B8;font-size:13px;line-height:1.5;margin:0 0 20px 0;">Invalid or expired OAuth state parameter. Please return to ResearchX and sign in again.</p>
                    <a href="/login" style="display:inline-block;padding:10px 20px;background:#4285F4;color:#FFFFFF;border-radius:10px;text-decoration:none;font-size:13px;font-weight:600;">Return to Login</a>
                </div>
            </body>
            </html>""",
            status_code=400,
        )

    provider_title = "Google" if provider == "google" else "GitHub"
    provider_color = "#4285F4" if provider == "google" else "#24292F"
    default_name = "Alex Researcher" if provider == "google" else "Octocat Developer"
    default_email = "alex.researcher@gmail.com" if provider == "google" else "octocat@github.com"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Authorize with {provider_title} — ResearchX</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background: #090D16;
            color: #F8FAFC;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, "Helvetica Neue", sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }}
        .card {{
            background: #111827;
            border: 1px solid #1E293B;
            border-radius: 18px;
            padding: 32px;
            width: 100%;
            max-width: 440px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.6);
            box-sizing: border-box;
            margin: 16px;
        }}
        .badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.1);
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 11px;
            color: #94A3B8;
            margin-bottom: 16px;
        }}
        h2 {{
            margin: 0 0 8px 0;
            font-size: 20px;
            font-weight: 600;
            color: #F8FAFC;
        }}
        p {{
            margin: 0 0 20px 0;
            color: #94A3B8;
            font-size: 13px;
            line-height: 1.5;
        }}
        .field {{
            margin-bottom: 16px;
        }}
        label {{
            display: block;
            font-size: 11px;
            text-transform: uppercase;
            font-weight: 600;
            color: #94A3B8;
            margin-bottom: 6px;
            letter-spacing: 0.5px;
        }}
        input {{
            width: 100%;
            padding: 10px 14px;
            background: #090D16;
            border: 1px solid #334155;
            border-radius: 10px;
            color: #F8FAFC;
            font-size: 13px;
            box-sizing: border-box;
            outline: none;
            transition: border-color 0.15s, box-shadow 0.15s;
        }}
        input:focus {{
            border-color: {provider_color};
            box-shadow: 0 0 0 2px rgba(66, 133, 244, 0.2);
        }}
        .btn-submit {{
            width: 100%;
            padding: 12px;
            background: {provider_color};
            color: #FFFFFF;
            border: none;
            border-radius: 10px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 8px;
            transition: opacity 0.15s, background-color 0.15s;
        }}
        .btn-submit:hover {{
            opacity: 0.92;
        }}
        .btn-cancel {{
            display: block;
            text-align: center;
            width: 100%;
            padding: 10px;
            background: transparent;
            color: #64748B;
            border: none;
            font-size: 12px;
            cursor: pointer;
            margin-top: 8px;
            text-decoration: none;
            box-sizing: border-box;
            transition: color 0.15s;
        }}
        .btn-cancel:hover {{
            color: #EF4444;
        }}
        .scope-box {{
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 10px;
            padding: 12px;
            font-size: 12px;
            color: #CBD5E1;
            margin-bottom: 18px;
        }}
        .scope-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 4px;
        }}
        .dot {{
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: #10B981;
        }}
    </style>
</head>
<body>
    <div class="card">
        <div class="badge">
            <span>ResearchX</span> &bull; <span>OAuth 2.0 Gateway</span>
        </div>
        <h2>Sign in with {provider_title}</h2>
        <p>ResearchX is requesting permission to access your {provider_title} profile and email address for workspace personalization.</p>
        
        <div class="scope-box">
            <strong>Requested Permissions:</strong>
            <div class="scope-item"><span class="dot"></span> Basic profile information (name, avatar)</div>
            <div class="scope-item"><span class="dot"></span> Verified email address</div>
        </div>

        <form method="POST" action="/auth/consent/{provider}">
            <input type="hidden" name="state" value="{state}">
            <div class="field">
                <label>Full Name</label>
                <input type="text" name="name" value="{default_name}" required>
            </div>
            <div class="field">
                <label>Email Address</label>
                <input type="email" name="email" value="{default_email}" required>
            </div>
            <button type="submit" class="btn-submit">Authorize &amp; Continue to ResearchX</button>
        </form>
        <a href="/auth/callback/{provider}?error=access_denied&state={state}" class="btn-cancel">Cancel and return to login</a>
    </div>
</body>
</html>"""
    return HTMLResponse(content=html_content)


@router.post("/consent/{provider}")
async def oauth_consent_submit(
    provider: str,
    request: Request,
):
    """
    Processes consent submission.
    Directs to the official provider authorization endpoint to authenticate the real Google/GitHub account,
    or returns an actionable error if credentials are not configured in Backend/.env.
    """
    provider = provider.lower().strip()
    if provider not in ("google", "github"):
        raise HTTPException(status_code=400, detail=f"Unsupported OAuth provider: {provider}")

    form_data = await request.form()
    state = form_data.get("state")
    name = str(form_data.get("name") or "").strip()
    email = str(form_data.get("email") or "").strip()

    if not state or state not in _PENDING_STATES:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state parameter")

    state_info = _PENDING_STATES[state]
    if name:
        state_info["preferred_name"] = name
    if email:
        state_info["preferred_email"] = email

    cfg = get_oauth_config()
    client_origin = state_info.get("origin") or cfg["default_frontend_url"]
    callback_url = f"{cfg['backend_url']}/auth/callback/{provider}"

    # Check whether the requested provider is properly configured before redirecting
    config_error = validate_provider_config(provider)
    if config_error:
        print(f"[OAuth] Configuration check failed for {provider}: {config_error}")
        return RedirectResponse(url=f"{client_origin}/login?error={quote(config_error)}", status_code=303)

    if provider == "google":
        params = {
            "client_id": cfg["google_client_id"],
            "redirect_uri": callback_url,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "select_account",
        }
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        return RedirectResponse(url=auth_url, status_code=303)

    elif provider == "github":
        params = {
            "client_id": cfg["github_client_id"],
            "redirect_uri": callback_url,
            "scope": "read:user user:email",
            "state": state,
        }
        auth_url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
        return RedirectResponse(url=auth_url, status_code=303)


# ==========================================================
# 3. OAuth Callback Endpoint (Code Exchange & Session Setup)
# ==========================================================
@router.get("/callback/{provider}")
async def oauth_callback(
    provider: str,
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
):
    """
    Exchanges OAuth code for user identity, creates/updates MongoDB user,
    logs login activity, generates JWT token, and redirects back to frontend.
    """
    provider = provider.lower().strip()
    cfg = get_oauth_config()
    
    # Retrieve pending state information
    state_info = _PENDING_STATES.pop(state, None) if state else None
    frontend_origin = state_info.get("origin") if state_info else cfg["default_frontend_url"]

    # Handle Cancellation / OAuth Provider Errors
    if error:
        err_msg = error_description or error or "Authentication was cancelled"
        print(f"[OAuth] User cancelled or error from {provider}: {err_msg}")
        redirect_target = f"{frontend_origin}/login?error={quote(err_msg)}"
        return RedirectResponse(url=redirect_target)

    if not code:
        redirect_target = f"{frontend_origin}/login?error={quote('Missing authorization code from provider')}"
        return RedirectResponse(url=redirect_target)

    user_name = "Researcher"
    user_email = ""
    provider_id = ""
    avatar_url = ""

    try:
        # PATH 1: Internal Code Exchange (Dev / Automated Testing)
        if code in _AUTH_CODES:
            code_payload = _AUTH_CODES.pop(code)
            user_name = code_payload.get("name") or "Researcher"
            user_email = code_payload.get("email") or ""
            provider_id = code_payload.get("provider_id") or secrets.token_hex(8)
            avatar_url = code_payload.get("avatar_url") or ""

        # PATH 2: Live External Code Exchange (Google / GitHub APIs)
        elif is_live_configured(provider):
            callback_url = f"{cfg['backend_url']}/auth/callback/{provider}"
            async with httpx.AsyncClient(timeout=15.0) as client:
                if provider == "google":
                    token_res = await client.post(
                        "https://oauth2.googleapis.com/token",
                        data={
                            "client_id": cfg["google_client_id"],
                            "client_secret": cfg["google_client_secret"],
                            "code": code,
                            "grant_type": "authorization_code",
                            "redirect_uri": callback_url,
                        },
                    )
                    if token_res.status_code != 200:
                        raise ValueError(f"Google token error: {token_res.text}")
                    token_data = token_res.json()
                    access_token = token_data.get("access_token")

                    userinfo_res = await client.get(
                        "https://www.googleapis.com/oauth2/v3/userinfo",
                        headers={"Authorization": f"Bearer {access_token}"},
                    )
                    user_info = userinfo_res.json()
                    user_email = user_info.get("email")
                    user_name = user_info.get("name") or (user_email.split("@")[0] if user_email else "Google User")
                    provider_id = str(user_info.get("sub", ""))
                    avatar_url = user_info.get("picture", "")

                elif provider == "github":
                    token_res = await client.post(
                        "https://github.com/login/oauth/access_token",
                        headers={"Accept": "application/json"},
                        data={
                            "client_id": cfg["github_client_id"],
                            "client_secret": cfg["github_client_secret"],
                            "code": code,
                            "redirect_uri": callback_url,
                        },
                    )
                    if token_res.status_code != 200:
                        raise ValueError(f"GitHub token error: {token_res.text}")
                    token_data = token_res.json()
                    access_token = token_data.get("access_token")

                    # Fetch GitHub user profile
                    user_res = await client.get(
                        "https://api.github.com/user",
                        headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
                    )
                    user_info = user_res.json()
                    user_name = user_info.get("name") or user_info.get("login") or "GitHub User"
                    provider_id = str(user_info.get("id", ""))
                    avatar_url = user_info.get("avatar_url", "")
                    user_email = user_info.get("email")

                    # GitHub often requires explicit call to /user/emails if primary email is private
                    if not user_email:
                        emails_res = await client.get(
                            "https://api.github.com/user/emails",
                            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
                        )
                        if emails_res.status_code == 200:
                            for em in emails_res.json():
                                if em.get("primary") and em.get("verified"):
                                    user_email = em.get("email")
                                    break
                                elif not user_email:
                                    user_email = em.get("email")
                    if not user_email:
                        user_email = f"{user_info.get('login', 'user')}@users.noreply.github.com"
        else:
            raise ValueError("Invalid authorization code or unconfigured provider")

        if not user_email:
            raise ValueError("Unable to retrieve email address from OAuth provider")

        user_email = user_email.strip().lower()

        # ----------------------------------------------------
        # MongoDB User Creation / Retrieval
        # ----------------------------------------------------
        existing_user = users_collection.find_one({"email": user_email})
        now = datetime.now(timezone.utc)

        if existing_user:
            user_id = str(existing_user.get("user_id") or existing_user.get("_id"))
            users_collection.update_one(
                {"_id": existing_user["_id"]},
                {
                    "$set": {
                        "user_id": user_id,
                        "auth_provider": provider,
                        "avatar_url": avatar_url or existing_user.get("avatar_url"),
                        "last_login": now,
                    }
                },
            )
            print(f"[OAuth] Authenticated existing user: {user_email} (ID: {user_id})")
        else:
            user_id = str(ObjectId())
            new_user_doc = {
                "user_id": user_id,
                "name": user_name,
                "email": user_email,
                "auth_provider": provider,
                "provider_id": provider_id,
                "avatar_url": avatar_url,
                "created_at": now,
                "last_login": now,
            }
            users_collection.insert_one(new_user_doc)
            print(f"[OAuth] Registered new user via {provider}: {user_email} (ID: {user_id})")

        # Log User Activity
        try:
            log_user_activity(
                user_id=user_id,
                user_email=user_email,
                action_name=f"{provider.capitalize()} Login",
                activity_type="auth",
                agent="OAuth System",
                status="Completed",
                details=f"Successfully signed in using {provider.capitalize()} OAuth",
            )
        except Exception as act_err:
            print(f"[OAuth Activity Log Warning]: {act_err}")

        # Generate Signed ResearchX JWT Token
        access_token = create_access_token({"sub": user_email, "user_id": user_id})

        # Redirect to frontend with token
        redirect_target = f"{frontend_origin}/login?token={access_token}&provider={provider}"
        return RedirectResponse(url=redirect_target)

    except Exception as exc:
        print(f"[OAuth Callback Error]: {exc}")
        err_msg = f"OAuth authentication failed: {str(exc)}"
        redirect_target = f"{frontend_origin}/login?error={quote(err_msg)}"
        return RedirectResponse(url=redirect_target)
