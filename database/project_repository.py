from database.connection import (
    SessionLocal,
)

from database.models import (
    CarbonProject,
)


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

        session.expunge(project)

        return project


def find_by_project_id(
    project_id: str,
) -> CarbonProject | None:

    with SessionLocal() as session:

        project = (
            session.query(CarbonProject)
            .filter(CarbonProject.project_id == project_id)
            .first()
        )

        if project is not None:
            session.expunge(project)

        return project


def find_by_project_name(
    project_name: str,
) -> CarbonProject | None:

    with SessionLocal() as session:

        project = (
            session.query(CarbonProject)
            .filter(CarbonProject.project_name == project_name)
            .first()
        )

        if project is not None:
            session.expunge(project)

        return project


def update_project_on_chain(
    project_id: str,
    token_id: int,
    contract_address: str,
    tx_hash: str,
):

    with SessionLocal() as session:

        project = (
            session.query(CarbonProject)
            .filter(CarbonProject.project_id == project_id)
            .first()
        )

        if project is None:
            raise ValueError("Project not found")

        project.on_chain_token_id = token_id

        project.contract_address = contract_address

        project.mint_tx_hash = tx_hash

        session.commit()
