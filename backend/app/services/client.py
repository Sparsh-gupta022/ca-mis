"""
Service layer for the Client resource.

Routes call these functions; all SQLAlchemy queries and business logic
for clients live here, per ARCHITECTURE.md.
"""
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.client import Client
from app.schemas.client import ClientCreate, ClientUpdate


def list_clients(
    db: Session,
    *,
    search: str | None = None,
    partner_in_charge: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[Client], int]:
    """
    List clients with optional search / filter / pagination.

    `search` matches against name OR pan_gstin (case-insensitive,
    substring match). Returns (items, total_count).
    """
    stmt = select(Client)
    count_stmt = select(func.count()).select_from(Client)

    if search:
        pattern = f"%{search}%"
        search_clause = or_(Client.name.ilike(pattern), Client.pan_gstin.ilike(pattern))
        stmt = stmt.where(search_clause)
        count_stmt = count_stmt.where(search_clause)

    if partner_in_charge:
        stmt = stmt.where(Client.partner_in_charge == partner_in_charge)
        count_stmt = count_stmt.where(Client.partner_in_charge == partner_in_charge)

    total = db.execute(count_stmt).scalar_one()

    stmt = stmt.order_by(Client.name).offset((page - 1) * page_size).limit(page_size)
    items = list(db.execute(stmt).scalars().all())

    return items, total


def get_client(db: Session, client_id: int) -> Client | None:
    """Fetch a single client by ID, or None if it doesn't exist."""
    return db.get(Client, client_id)


def create_client(db: Session, payload: ClientCreate) -> Client:
    """Create and persist a new client."""
    client = Client(**payload.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


def update_client(db: Session, client: Client, payload: ClientUpdate) -> Client:
    """
    Apply a partial update to an existing client.

    Only fields explicitly present in the payload are changed —
    fields the caller omitted are left untouched.
    """
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(client, field, value)

    db.add(client)
    db.commit()
    db.refresh(client)
    return client


def delete_client(db: Session, client: Client) -> None:
    """
    Delete a client.

    Relies on the existing ON DELETE CASCADE relationship from Client to
    ComplianceSchedule/Task (see DATABASE_SPEC.md) — the database itself
    removes the client's schedules and tasks.
    """
    db.delete(client)
    db.commit()
