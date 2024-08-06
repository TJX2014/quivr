from typing import List, Sequence

from quivr_api.logger import get_logger
from quivr_api.modules.dependencies import BaseService
from quivr_api.modules.sync.dto.inputs import (SyncsActiveInput,
                                               SyncsActiveUpdateInput,
                                               SyncsUserInput,
                                               SyncUserUpdateInput)
from quivr_api.modules.sync.entity.sync import (NotionSyncFile, SyncsActive,
                                                SyncsUser)
from quivr_api.modules.sync.repository.sync import NotionRepository, Sync
from quivr_api.modules.sync.repository.sync_interfaces import (
    SyncInterface, SyncUserInterface)
from quivr_api.modules.sync.repository.sync_user import SyncUser
from quivr_api.modules.user.service.user_service import UserService

logger = get_logger(__name__)


user_service = UserService()


class SyncUserService:
    repository: SyncUserInterface

    def __init__(self):
        self.repository = SyncUser()

    def get_syncs_user(self, user_id: str, sync_user_id: int | None = None):
        return self.repository.get_syncs_user(user_id, sync_user_id)

    def create_sync_user(self, sync_user_input: SyncsUserInput):
        return self.repository.create_sync_user(sync_user_input)

    def delete_sync_user(self, sync_id: int, user_id: str):
        return self.repository.delete_sync_user(sync_id, user_id)

    def get_sync_user_by_state(self, state: dict) -> SyncsUser | None:
        return self.repository.get_sync_user_by_state(state)

    def get_sync_user_by_id(self, sync_id: int):
        return self.repository.get_sync_user_by_id(sync_id)

    def update_sync_user(
        self, sync_user_id: int, state: dict, sync_user_input: SyncUserUpdateInput
    ):
        return self.repository.update_sync_user(sync_user_id, state, sync_user_input)

    def get_all_notion_user_syncs(self):
        return self.repository.get_all_notion_user_syncs()

    async def get_files_folder_user_sync(
        self,
        sync_active_id: int,
        user_id: str,
        folder_id: str | None = None,
        recursive: bool = False,
        notion_service=None,
    ):
        return await self.repository.get_files_folder_user_sync(
            sync_active_id=sync_active_id,
            user_id=user_id,
            folder_id=folder_id,
            recursive=recursive,
            notion_service=notion_service,
        )


class SyncService:
    repository: SyncInterface

    def __init__(self):
        self.repository = Sync()

    def create_sync_active(
        self, sync_active_input: SyncsActiveInput, user_id: str
    ) -> SyncsActive | None:
        return self.repository.create_sync_active(sync_active_input, user_id)

    def get_syncs_active(self, user_id: str) -> List[SyncsActive]:
        return self.repository.get_syncs_active(user_id)

    def update_sync_active(
        self, sync_id: int, sync_active_input: SyncsActiveUpdateInput
    ):
        return self.repository.update_sync_active(sync_id, sync_active_input)

    def delete_sync_active(self, sync_active_id: int, user_id: str):
        return self.repository.delete_sync_active(int(sync_active_id), user_id)

    async def get_syncs_active_in_interval(self) -> List[SyncsActive]:
        return await self.repository.get_syncs_active_in_interval()

    def get_details_sync_active(self, sync_active_id: int):
        return self.repository.get_details_sync_active(sync_active_id)
