from database.connection import SessionLocal
from database.models import CarbonProject


def create_project(
    project_id: str,
    project_name: str,
    project_type: str | None,
    project_region: str | None,
) -> CarbonProject:

    with SessionLocal() as session:

        project = CarbonProject(
            project_id=project_id,
            project_name=project_name,
            project_type=project_type,
            project_region=project_region,
        )

        session.add(project)
        session.commit()
        session.refresh(project)

        return project


def find_by_project_id(
    project_id: str,
) -> CarbonProject | None:

    with SessionLocal() as session:

        return (
            session.query(CarbonProject)
            .filter(CarbonProject.project_id == project_id)
            .first()
        )


def find_by_project_name(
    project_name: str,
) -> CarbonProject | None:

    with SessionLocal() as session:

        return (
            session.query(CarbonProject)
            .filter(CarbonProject.project_name == project_name)
            .first()
        )
