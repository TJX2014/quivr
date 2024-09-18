import os

import requests
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse

from quivr_api.logger import get_logger
from quivr_api.middlewares.auth import AuthBearer, get_current_user
from quivr_api.modules.dependencies import get_service
from quivr_api.modules.sync.dto.inputs import SyncCreateInput, SyncUpdateInput
from quivr_api.modules.sync.service.sync_service import SyncsService
from quivr_api.modules.sync.utils.oauth2 import Oauth2State
from quivr_api.modules.sync.utils.sync_exceptions import SyncNotFoundException
from quivr_api.modules.user.entity.user_identity import UserIdentity

from .successfull_connection import successfullConnectionPage

# Initialize logger
logger = get_logger(__name__)

# Initialize sync service
syncs_service_dep = get_service(SyncsService)

# Initialize API router
github_sync_router = APIRouter()

# Constants
CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5050")
REDIRECT_URI = f"{BACKEND_URL}/sync/github/oauth2callback"
SCOPE = "repo user"


@github_sync_router.post(
    "/sync/github/authorize",
    dependencies=[Depends(AuthBearer())],
    tags=["Sync"],
)
async def authorize_github(
    request: Request,
    name: str,
    syncs_service: SyncsService = Depends(syncs_service_dep),
    current_user: UserIdentity = Depends(get_current_user),
):
    """
    Authorize GitHub sync for the current user.

    Args:
        request (Request): The request object.
        current_user (UserIdentity): The current authenticated user.

    Returns:
        dict: A dictionary containing the authorization URL.
    """
    logger.debug(f"Authorizing GitHub sync for user: {current_user.id}")

    state_struct = Oauth2State(name=name, user_id=current_user.id)
    state = state_struct.model_dump_json()

    sync_user_input = SyncCreateInput(
        user_id=current_user.id,
        name=name,
        provider="GitHub",
        credentials={},
        state={"state": state},
    )
    sync = await syncs_service.create_sync_user(sync_user_input)
    state_struct.sync_id = sync.id
    state = state_struct.model_dump_json()

    authorization_url = (
        f"https://github.com/login/oauth/authorize?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}&scope={SCOPE}&state={state}"
    )
    return {"authorization_url": authorization_url}


@github_sync_router.get("/sync/github/oauth2callback", tags=["Sync"])
async def oauth2callback_github(
    request: Request, syncs_service: SyncsService = Depends(syncs_service_dep)
):
    """
    Handle OAuth2 callback from GitHub.

    Args:
        request (Request): The request object.

    Returns:
        dict: A dictionary containing a success message.
    """
    state = request.query_params.get("state")

    if not state:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    state = Oauth2State.model_validate_json(state)

    if state.sync_id is None:
        raise HTTPException(
            status_code=400, detail="Invalid state parameter. Unknown sync"
        )

    logger.debug(
        f"Handling OAuth2 callback for user: {state.user_id} with state: {state}"
    )

    try:
        sync = await syncs_service.get_sync_by_id(state.sync_id)
    except SyncNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"{e.message}"
        )
    if (
        not sync
        or not sync.state
        or state.model_dump(exclude={"sync_id"}) != sync.state["state"]
    ):
        logger.error("Invalid state parameter")
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    if sync.user_id != state.user_id:
        raise HTTPException(status_code=400, detail="Invalid user")

    token_url = "https://github.com/login/oauth/access_token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": request.query_params.get("code"),
        "redirect_uri": REDIRECT_URI,
        "state": state,
    }
    headers = {"Accept": "application/json"}
    response = requests.post(token_url, data=data, headers=headers)
    if response.status_code != 200:
        logger.error(f"Failed to acquire token: {response.json()}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to acquire token: {response.json()}",
        )

    result = response.json()
    access_token = result.get("access_token")
    if not access_token:
        logger.error(f"Failed to acquire token: {result}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to acquire token: {result}",
        )

    creds = result
    logger.info(f"Fetched OAuth2 token for user: {state.user_id}")

    # Fetch user email from GitHub API
    github_api_url = "https://api.github.com/user"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(github_api_url, headers=headers)
    if response.status_code != 200:
        logger.error("Failed to fetch user profile from GitHub API")
        raise HTTPException(status_code=400, detail="Failed to fetch user profile")

    user_info = response.json()
    user_email = user_info.get("email")
    if not user_email:
        # If the email is not public, make a separate API call to get emails
        emails_url = "https://api.github.com/user/emails"
        response = requests.get(emails_url, headers=headers)
        if response.status_code == 200:
            emails = response.json()
            user_email = next(email["email"] for email in emails if email["primary"])
        else:
            logger.error("Failed to fetch user email from GitHub API")
            raise HTTPException(status_code=400, detail="Failed to fetch user email")

    logger.info(f"Retrieved email for user: {state.user_id} - {user_email}")

    sync_user_input = SyncUpdateInput(credentials=result, state={}, email=user_email)

    await syncs_service.update_sync(state.sync_id, sync_user_input)
    logger.info(f"GitHub sync created successfully for user: {state.user_id}")
    return HTMLResponse(successfullConnectionPage)
