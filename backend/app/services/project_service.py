import uuid

from app.core.exceptions import AuthorizationError, NotFoundError
from app.models.project import Project
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    def __init__(self, repository: ProjectRepository):
        self._repo = repository

    async def create(self, user_id: uuid.UUID, payload: ProjectCreate) -> Project:
        return await self._repo.create(user_id=user_id, **payload.model_dump(exclude_unset=True))

    async def get_by_id(self, id: uuid.UUID, user_id: uuid.UUID | None = None) -> Project:
        project = await self._repo.get_by_id(id)
        if project is None:
            raise NotFoundError("Project not found.")
        self._assert_ownership(project, user_id)
        return project

    async def get_all(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        search: str | None = None,
        status: str | None = None,
        category_id: uuid.UUID | None = None,
        technology_id: uuid.UUID | None = None,
        is_archived: bool = False,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> tuple[list[Project], int]:
        return await self._repo.get_all(
            user_id=user_id,
            skip=skip,
            limit=limit,
            search=search,
            status=status,
            category_id=category_id,
            technology_id=technology_id,
            is_archived=is_archived,
            sort_by=sort_by,
            sort_desc=sort_desc,
        )

    async def update(self, id: uuid.UUID, payload: ProjectUpdate, user_id: uuid.UUID | None = None) -> Project:
        project = await self.get_by_id(id, user_id=user_id)
        return await self._repo.update(project, **payload.model_dump(exclude_unset=True))

    async def delete(self, id: uuid.UUID, user_id: uuid.UUID | None = None) -> None:
        project = await self.get_by_id(id, user_id=user_id)
        await self._repo.delete(project)

    @staticmethod
    def _assert_ownership(project: Project, user_id: uuid.UUID | None) -> None:
        if user_id is not None and project.user_id != user_id:
            raise AuthorizationError("You do not have permission to access this project.")
