from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.schemas.responses import CommandHistoryResponse
from app.database.dal import DAL
from app.database.repositories import CommandHistoryRepository

command_history_router = APIRouter(tags=["Commands"])

CommandHistoryRepo = Annotated[CommandHistoryRepository, Depends(DAL.get_repo(DAL.command_history))]


@command_history_router.get("/{command_id}/history")
async def get_command_history(command_id: UUID, command_history: CommandHistoryRepo) -> CommandHistoryResponse:  # noqa: ANN201
    """
    Retrieve a command's history by ID using the `CommandHistoryRepo`'s concrete method.

    :param command_id: UUID of the command to retrieve.
    :param command_history: injected CommandHistory repository.
    :return: The command's history entries, latest first.
    :raises HTTPException: 404 if the command has no history entries. A deleted command still has
        history, so check the history table, not the commands table.
    """

    history = await command_history.get_history_by_id(command_id)

    if not history:
        raise HTTPException(
            status_code=404,
            detail=f"No history entries were found for the command {command_id}",
        )

    return CommandHistoryResponse(data=history)
