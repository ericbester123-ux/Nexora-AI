import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.project import Project, ProjectCategoryLink, ProjectTechnology
from app.models.project_category import ProjectCategory
from app.models.technology import Technology


class ProjectRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def _load_relations(self, project: Project) -> Project:
        result = await self._session.execute(
            select(Project)
            .where(Project.id == project.id)
            .options(selectinload(Project.technologies), selectinload(Project.categories))
        )
        return result.scalar_one()

    async def get_by_id(self, id: uuid.UUID) -> Optional[Project]:
        query = (
            select(Project)
            .where(Project.id == id)
            .options(selectinload(Project.technologies), selectinload(Project.categories))
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, user_id: uuid.UUID, **fields) -> Project:
        technology_ids = fields.pop("technology_ids", None) or []
        category_ids = fields.pop("category_ids", None) or []

        project = Project(user_id=user_id, **fields)
        self._session.add(project)
        await self._session.flush()

        if technology_ids:
            result = await self._session.execute(
                select(Technology).where(Technology.id.in_(technology_ids))
            )
            project.technologies = list(result.scalars().all())

        if category_ids:
            result = await self._session.execute(
                select(ProjectCategory).where(ProjectCategory.id.in_(category_ids))
            )
            project.categories = list(result.scalars().all())

        await self._session.refresh(project)
        return await self._load_relations(project)

    async def get_all(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
        category_id: Optional[uuid.UUID] = None,
        technology_id: Optional[uuid.UUID] = None,
        is_archived: bool = False,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> tuple[list[Project], int]:
        query = (
            select(Project)
            .where(Project.user_id == user_id, Project.is_archived == is_archived)
            .options(selectinload(Project.technologies), selectinload(Project.categories))
        )
        count_query = select(func.count(Project.id)).where(
            Project.user_id == user_id, Project.is_archived == is_archived
        )

        if search:
            pattern = f"%{search}%"
            query = query.where(Project.title.ilike(pattern))
            count_query = count_query.where(Project.title.ilike(pattern))

        if status:
            query = query.where(Project.status == status)
            count_query = count_query.where(Project.status == status)

        if category_id:
            query = query.join(ProjectCategoryLink).where(ProjectCategoryLink.category_id == category_id)
            count_query = count_query.join(ProjectCategoryLink).where(ProjectCategoryLink.category_id == category_id)

        if technology_id:
            query = query.join(ProjectTechnology).where(ProjectTechnology.technology_id == technology_id)
            count_query = count_query.join(ProjectTechnology).where(ProjectTechnology.technology_id == technology_id)

        sort_column = getattr(Project, sort_by, Project.created_at)
        if sort_desc:
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        total_result = await self._session.execute(count_query)
        total_count = total_result.scalar() or 0

        query = query.offset(skip).limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all()), total_count

    async def update(self, project: Project, **fields) -> Project:
        technology_ids = fields.pop("technology_ids", None)
        category_ids = fields.pop("category_ids", None)

        for key, value in fields.items():
            setattr(project, key, value)

        if technology_ids is not None:
            result = await self._session.execute(
                select(Technology).where(Technology.id.in_(technology_ids))
            )
            project.technologies = list(result.scalars().all())

        if category_ids is not None:
            result = await self._session.execute(
                select(ProjectCategory).where(ProjectCategory.id.in_(category_ids))
            )
            project.categories = list(result.scalars().all())

        await self._session.flush()
        return await self._load_relations(project)

    async def delete(self, project: Project) -> None:
        await self._session.delete(project)
        await self._session.flush()
