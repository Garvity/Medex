from functools import lru_cache

import firebase_admin
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth, credentials

from core.config import get_settings

bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache
def get_firebase_app():
    settings = get_settings()
    if not settings.firebase_project_id:
        raise RuntimeError("FIREBASE_PROJECT_ID must be configured before Firebase authentication can run.")
    try:
        return firebase_admin.get_app()
    except ValueError:
        options = {"projectId": settings.firebase_project_id}
        if settings.google_application_credentials:
            return firebase_admin.initialize_app(credentials.Certificate(settings.google_application_credentials), options)
        return firebase_admin.initialize_app(options=options)


async def get_current_user(
    credentials_value: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    if not credentials_value or not credentials_value.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="A Firebase ID token is required.")
    try:
        get_firebase_app()
        return auth.verify_id_token(credentials_value.credentials, check_revoked=True)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired Firebase ID token.") from exc
