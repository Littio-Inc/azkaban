"""Firebase Admin SDK configuration."""

import firebase_admin as firebase_admin_sdk
from firebase_admin import credentials

from app.common.secrets import get_secret


# Initialize Firebase Admin SDK
if not firebase_admin_sdk._apps:
    project_id = get_secret("FIREBASE_PROJECT_ID")
    private_key = get_secret("FIREBASE_PRIVATE_KEY")
    client_email = get_secret("FIREBASE_CLIENT_EMAIL")

    if project_id and private_key and client_email:
        cred = credentials.Certificate({
            "type": "service_account",
            "project_id": project_id,
            "private_key": private_key.replace("\\n", "\n"),  # noqa: WPS342
            "client_email": client_email,
            "token_uri": "https://oauth2.googleapis.com/token",
        })
        firebase_admin_sdk.initialize_app(cred)
