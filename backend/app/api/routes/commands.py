from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.exc import IntegrityError

from app.api.schemas.requests import CreateCommandRequest, UpdateCommandRequest
from app.api.schemas.responses import CommandResponse, CommandsResponse, DeleteCommandResponse
from app.database.dal import DAL
from app.database.repositories import CommandHistoryRepository, CommandsRepository

commands_router = APIRouter(tags=["Commands"])

CommandsRepo = Annotated[CommandsRepository, Depends(DAL.get_repo(DAL.commands))]

CommandHistoryRepo = Annotated[CommandHistoryRepository, Depends(DAL.get_repo(DAL.command_history))]


@commands_router.get("/")
async def get_commands(commands: CommandsRepo) -> CommandsResponse:
    """
    Retrieve all commands from the database.

    :param commands: injected Command repository.
    :return: All command entries.
    """
    return CommandsResponse(data=await commands.get_all())


@commands_router.get("/{command_id}")
async def get_command(command_id: UUID, commands: CommandsRepo) -> CommandResponse:
    """
    Retrieve a single command by ID.

    :param command_id: UUID of the command to retrieve.
    :param commands: injected Command repository.
    :return: The matching command entry.
    """
    try:
        command = await commands.get_by_id(command_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return CommandResponse(data=command)


@commands_router.post("/")
async def create_command(
    request: CreateCommandRequest,
    commands: CommandsRepo,
    command_history: CommandHistoryRepo,
) -> CommandResponse:
    """
    Create a new command entry with status set to pending.

    :param request: Typed fields identifying the command type, session, and optional parameters.
    :param commands: injected Command repository.
    :return: The newly created command.
    """
    created_command = await commands.create(
        {
            "type_": request.type_,
            "params": request.params,
        }
    )
    await command_history.create(
        {
            "command_id": created_command.id,
            "status": created_command.status,
            "params": created_command.params,
        }
    )

    return CommandResponse(data=created_command)


@commands_router.patch("/{command_id}")
async def update_command(
    command_id: UUID,
    request: UpdateCommandRequest,
    commands: CommandsRepo,
    command_history: CommandHistoryRepo,
) -> CommandResponse:
    """
    Partially update a command's status, type, or parameters.

    :param command_id: UUID of the command to update.
    :param request: Fields to overwrite; omitted fields are left unchanged.
    :param commands: injected Command repository.
    :return: The updated command entry.
    :raises HTTPException: 404 if the command does not exist.
    :raises HTTPException: 422 if the repository rejects the update, e.g. a value of the wrong type or a
        ``type_`` that is not an existing main command. A rejected update leaves the command unchanged.
    """
    data = request.model_dump(exclude_unset=True)

    try:
        updated_command = await commands.update(command_id, data)
    except ValueError as e:
        # The requested command ID not in database
        raise HTTPException(status_code=404, detail=str(e)) from e
    except (TypeError, IntegrityError) as e:
        # The update is invalid or broke a database rule
        raise HTTPException(status_code=422, detail=str(e)) from e

    await command_history.create(
        {
            "command_id": updated_command.id,
            "status": updated_command.status,
            "params": updated_command.params,
        }
    )

    return CommandResponse(data=updated_command)


@commands_router.delete("/{command_id}")
async def delete_command(
    command_id: UUID,
    commands: CommandsRepo,
    command_history: CommandHistoryRepo,
) -> DeleteCommandResponse:
    """
    Delete a command by ID.

    :param command_id: UUID of the command to delete.
    :param commands: injected Command repository.
    :return: Confirmation message with the deleted command ID.
    """
    try:
        command_to_delete = await commands.get_by_id(command_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    await command_history.create(
        {
            "command_id": command_to_delete.id,
            "status": command_to_delete.status,
            "params": command_to_delete.params,
        }
    )
    await commands.delete_by_id(command_id)
    return DeleteCommandResponse(message=f"Command {command_id} deleted successfully")
