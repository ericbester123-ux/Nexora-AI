import uuid

import pytest
from app.core.exceptions import NotFoundError
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.project_service import ProjectService


class FakeProjectRepository:
    def __init__(self):
        self._projects: dict[uuid.UUID, Project] = {}

    async def create(self, user_id: uuid.UUID, **fields) -> Project:
        technology_ids = fields.pop("technology_ids", None) or []
        category_ids = fields.pop("category_ids", None) or []
        fields.setdefault("status", "open")
        fields.setdefault("is_remote", True)
        fields.setdefault("is_archived", False)
        fields.setdefault("is_negotiable", False)
        fields.setdefault("is_ai_recommended", False)
        fields.setdefault("proposals_count", 0)
        fields.setdefault("currency", "USD")
        project = Project(id=uuid.uuid4(), user_id=user_id, **fields)
        project.technologies = technology_ids
        project.categories = category_ids
        self._projects[project.id] = project
        return project

    async def get_by_id(self, id: uuid.UUID) -> Project | None:
        return self._projects.get(id)

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
        items = [
            p for p in self._projects.values()
            if p.user_id == user_id and p.is_archived == is_archived
        ]
        if search:
            items = [p for p in items if search.lower() in p.title.lower()]
        if status:
            items = [p for p in items if p.status == status]
        total = len(items)
        items = items[skip:skip + limit]
        return items, total

    async def update(self, project: Project, **fields) -> Project:
        technology_ids = fields.pop("technology_ids", None)
        category_ids = fields.pop("category_ids", None)
        for key, value in fields.items():
            setattr(project, key, value)
        if technology_ids is not None:
            project.technologies = technology_ids
        if category_ids is not None:
            project.categories = category_ids
        return project

    async def delete(self, project: Project) -> None:
        self._projects.pop(project.id, None)


@pytest.fixture
def project_service() -> ProjectService:
    return ProjectService(repository=FakeProjectRepository())


@pytest.fixture
async def existing_project(project_service: ProjectService) -> Project:
    payload = ProjectCreate(title="Build a website", description="A great project")
    return await project_service.create(user_id=uuid.uuid4(), payload=payload)


class TestCreate:
    async def test_create_returns_project(self, project_service: ProjectService):
        user_id = uuid.uuid4()
        payload = ProjectCreate(title="Mobile App", description="Build an app")
        result = await project_service.create(user_id=user_id, payload=payload)
        assert result.title == "Mobile App"
        assert result.user_id == user_id

    async def test_create_with_defaults(self, project_service: ProjectService):
        payload = ProjectCreate(title="Default project")
        result = await project_service.create(user_id=uuid.uuid4(), payload=payload)
        assert result.status == "open"
        assert result.is_remote is True
        assert result.is_archived is False


class TestGetById:
    async def test_get_by_id_returns_project(self, project_service: ProjectService, existing_project: Project):
        result = await project_service.get_by_id(existing_project.id)
        assert result.id == existing_project.id
        assert result.title == existing_project.title

    async def test_get_by_id_raises_not_found(self, project_service: ProjectService):
        with pytest.raises(NotFoundError):
            await project_service.get_by_id(uuid.uuid4())


class TestGetAll:
    async def test_get_all_returns_user_projects(self, project_service: ProjectService):
        user_id = uuid.uuid4()
        await project_service.create(user_id=user_id, payload=ProjectCreate(title="Project A"))
        await project_service.create(user_id=user_id, payload=ProjectCreate(title="Project B"))
        items, total = await project_service.get_all(user_id=user_id)
        assert total == 2
        assert len(items) == 2

    async def test_get_all_excludes_other_users(self, project_service: ProjectService):
        user_a = uuid.uuid4()
        user_b = uuid.uuid4()
        await project_service.create(user_id=user_a, payload=ProjectCreate(title="A"))
        await project_service.create(user_id=user_b, payload=ProjectCreate(title="B"))
        items, total = await project_service.get_all(user_id=user_a)
        assert total == 1

    async def test_get_all_pagination(self, project_service: ProjectService):
        user_id = uuid.uuid4()
        for i in range(5):
            await project_service.create(user_id=user_id, payload=ProjectCreate(title=f"Project {i}"))
        items, total = await project_service.get_all(user_id=user_id, skip=0, limit=2)
        assert total == 5
        assert len(items) == 2

    async def test_get_all_search_by_title(self, project_service: ProjectService):
        user_id = uuid.uuid4()
        await project_service.create(user_id=user_id, payload=ProjectCreate(title="Python backend"))
        await project_service.create(user_id=user_id, payload=ProjectCreate(title="React frontend"))
        items, total = await project_service.get_all(user_id=user_id, search="python")
        assert total == 1
        assert items[0].title == "Python backend"

    async def test_get_all_filter_by_status(self, project_service: ProjectService):
        user_id = uuid.uuid4()
        await project_service.create(user_id=user_id, payload=ProjectCreate(title="Open project", status="open"))
        await project_service.create(user_id=user_id, payload=ProjectCreate(title="Closed project", status="closed"))
        items, total = await project_service.get_all(user_id=user_id, status="closed")
        assert total == 1
        assert items[0].status == "closed"

    async def test_get_all_excludes_archived(self, project_service: ProjectService):
        user_id = uuid.uuid4()
        await project_service.create(user_id=user_id, payload=ProjectCreate(title="Active"))
        items, total = await project_service.get_all(user_id=user_id, is_archived=False)
        assert total == 1


class TestUpdate:
    async def test_update_changes_fields(self, project_service: ProjectService, existing_project: Project):
        payload = ProjectUpdate(title="Updated title")
        result = await project_service.update(existing_project.id, payload)
        assert result.title == "Updated title"

    async def test_update_partial(self, project_service: ProjectService, existing_project: Project):
        payload = ProjectUpdate(description="New description")
        result = await project_service.update(existing_project.id, payload)
        assert result.description == "New description"
        assert result.title == existing_project.title

    async def test_update_raises_not_found(self, project_service: ProjectService):
        payload = ProjectUpdate(title="Ghost")
        with pytest.raises(NotFoundError):
            await project_service.update(uuid.uuid4(), payload)


class TestDelete:
    async def test_delete_removes_project(self, project_service: ProjectService, existing_project: Project):
        await project_service.delete(existing_project.id)
        with pytest.raises(NotFoundError):
            await project_service.get_by_id(existing_project.id)

    async def test_delete_raises_not_found(self, project_service: ProjectService):
        with pytest.raises(NotFoundError):
            await project_service.delete(uuid.uuid4())
