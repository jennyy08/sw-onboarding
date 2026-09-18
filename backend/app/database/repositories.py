from uuid import UUID

from sqlmodel import desc, select

from app.database.abstract_repository import AbstractRepository
from app.database.engine import get_db_session
from app.database.models import Command, CommandHistory, MainCommand


class MainCommandRepository(AbstractRepository[MainCommand, int]):
    """
    Repository for MainCommand table.
    """

    model = MainCommand


class CommandsRepository(AbstractRepository[Command, UUID]):
    """
    Repository for Command table.
    """

    model = Command


class CommandHistoryRepository(AbstractRepository[CommandHistory, UUID]):
    """
    Repository for Command table.
    """

    model = CommandHistory

    async def get_history_by_id(self, command_id: UUID) -> list[CommandHistory]:
        """
        Get the entire history of a command by its UUID, sorted by latest first.
        """
        statement = (
            select(CommandHistory)
            .where(CommandHistory.command_id == command_id)
            .order_by(desc(CommandHistory.created_at))
        )

        async with get_db_session() as session:
            result = await session.exec(statement)
            return list(result.all())

        return []
