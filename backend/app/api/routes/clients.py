"""
Client CRUD routes — GET/POST /clients, GET/PUT/DELETE /clients/{id}.

Thin per ARCHITECTURE.md: no SQLAlchemy queries or business logic here,
only request/response wiring around app/services/client.py.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientListResponse, ClientRead, ClientUpdate
from app.services import client as client_service

router = APIRouter()


def _get_client_or_404(db: Session, client_id: int) -> Client:
    client = client_service.get_client(db, client_id)
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return client


@router.get("", response_model=ClientListResponse)
def list_clients(
    search: str | None = Query(default=None, description="Matches against name or PAN/GSTIN"),
    partner_in_charge: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> ClientListResponse:
    items, total = client_service.list_clients(
        db,
        search=search,
        partner_in_charge=partner_in_charge,
        page=page,
        page_size=page_size,
    )
    return ClientListResponse(items=items, total=total)


@router.post("", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
def create_client(payload: ClientCreate, db: Session = Depends(get_db)) -> Client:
    return client_service.create_client(db, payload)


@router.get("/{client_id}", response_model=ClientRead)
def get_client(client_id: int, db: Session = Depends(get_db)) -> Client:
    return _get_client_or_404(db, client_id)


@router.put("/{client_id}", response_model=ClientRead)
def update_client(client_id: int, payload: ClientUpdate, db: Session = Depends(get_db)) -> Client:
    client = _get_client_or_404(db, client_id)
    return client_service.update_client(db, client, payload)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(client_id: int, db: Session = Depends(get_db)) -> None:
    client = _get_client_or_404(db, client_id)
    client_service.delete_client(db, client)
