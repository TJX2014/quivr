import os

from dropbox import Dropbox, DropboxOAuth2Flow
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

DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5050")
BASE_REDIRECT_URI = f"{BACKEND_URL}/sync/dropbox/oauth2callback"
SCOPE = ["files.metadata.read", "account_info.read", "files.content.read"]

# Initialize sync service
syncs_service_dep = get_service(SyncsService)

logger = get_logger(__name__)

# Initialize API router
dropbox_sync_router = APIRouter()


@dropbox_sync_router.post(
    "/sync/dropbox/authorize",
    dependencies=[Depends(AuthBearer())],
    tags=["Sync"],
)
async def authorize_dropbox(
    request: Request,
    name: str,
    current_user: UserIdentity = Depends(get_current_user),
    syncs_service: SyncsService = Depends(syncs_service_dep),
):
    """
    Authorize DropBox sync for the current user.

    Args:
        request (Request): The request object.
        current_user (UserIdentity): The current authenticated user.

    Returns:
        dict: A dictionary containing the authorization URL.
    """
    logger.debug(
        f"Authorizing Drop Box sync for user: {current_user.id}, name : {name}"
    )
    auth_flow = DropboxOAuth2Flow(
        DROPBOX_APP_KEY,
        redirect_uri=BASE_REDIRECT_URI,
        session={},
        csrf_token_session_key="csrf-token",
        consumer_secret=DROPBOX_APP_SECRET,
        token_access_type="offline",
        scope=SCOPE,
    )
    state_struct = Oauth2State(name=name, user_id=current_user.id)
    sync_user_input = SyncCreateInput(
        name=name,
        user_id=current_user.id,
        provider="DropBox",
        credentials={},
        state={"state": state_struct.model_dump_json()},
        additional_data={},
    )
    sync = await syncs_service.create_sync_user(sync_user_input)
    state_struct.sync_id = sync.id
    state = state_struct.model_dump_json()
    authorize_url = auth_flow.start(state)
    logger.info(
        f"Generated authorization URL: {authorize_url} for user: {current_user.id}"
    )
    return {"authorization_url": authorize_url}


@dropbox_sync_router.get("/sync/dropbox/oauth2callback", tags=["Sync"])
async def oauth2callback_dropbox(
    request: Request,
    syncs_service: SyncsService = Depends(syncs_service_dep),
):
    """
    Handle OAuth2 callback from DropBox.

    Args:
        request (Request): The request object.

    Returns:
        dict: A dictionary containing a success message.
    """
    state = request.query_params.get("state")
    if not state:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    session = {}
    session["csrf-token"] = state.split("|")[0] if "|" in state else ""

    logger.debug("Keys in session : %s", session.keys())
    logger.debug("Value in session : %s", session.values())

    state = Oauth2State.model_validate_json(state)

    if state.sync_id is None:
        raise HTTPException(
            status_code=400, detail="Invalid state parameter. Unknown sync"
        )

    logger.debug(
        f"Handling OAuth2 callback for user: {state.user_id} with state: {state} "
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

    auth_flow = DropboxOAuth2Flow(
        DROPBOX_APP_KEY,
        redirect_uri=BASE_REDIRECT_URI,
        session=session,
        csrf_token_session_key="csrf-token",
        consumer_secret=DROPBOX_APP_SECRET,
        token_access_type="offline",
        scope=SCOPE,
    )
    try:
        oauth_result = auth_flow.finish(request.query_params)

        access_token = oauth_result.access_token

        dbx = Dropbox(oauth2_access_token=access_token)

        # Get account information
        account_info = dbx.users_get_current_account()
        user_email = account_info.email  # type: ignore
        account_id = account_info.account_id  # type: ignore

        credentials: dict[str, str] = {
            "access_token": oauth_result.access_token,
            "refresh_token": oauth_result.refresh_token,
            "account_id": account_id,
            "expires_in": str(oauth_result.expires_at),
        }

        sync_user_input = SyncUpdateInput(
            credentials=credentials,
            state={},
            email=user_email,
        )
        await syncs_service.update_sync(state.sync_id, sync_user_input)
        logger.info(f"DropBox sync created successfully for user: {state.user_id}")
        return HTMLResponse(successfullConnectionPage)
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=400, detail="Invalid user")
