import uuid


def generate_project_id() -> str:

    return "PRJ-" + uuid.uuid4().hex[:12].upper()


from database.project_repository import (
    create_project,
    find_by_project_name,
    find_by_project_id
)


def get_or_create_project(
    project_name: str,
    project_type: str | None,
    project_region: str | None,
):

    existing = find_by_project_name(project_name)

    if existing is not None:
        return existing

    project_id = generate_project_id()

    return create_project(
        project_id=project_id,
        project_name=project_name,
        project_type=project_type,
        project_region=project_region,
    )

def get_project(
    project_id: str
):
    return find_by_project_id(project_id)