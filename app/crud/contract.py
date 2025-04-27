from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

from app.models.contract import Contract
from app.schemas.contract import ContractCreate

def create_contract(db: Session, contract: ContractCreate) -> Contract:
    db_contract = Contract(
        user_id=contract.user_id,
        filename=contract.filename,
        file_type=contract.file_type,
        content=contract.content
    )
    db.add(db_contract)
    db.commit()
    db.refresh(db_contract)
    return db_contract


def get_contract(db: Session, contract_id: int) -> Optional[Contract]:
    return db.query(Contract).filter(Contract.id == contract_id).first()


def get_user_contracts(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Contract]:
    return db.query(Contract).filter(Contract.user_id == user_id).offset(skip).limit(limit).all()


def delete_contract(db: Session, contract_id: int) -> bool:
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if contract:
        db.delete(contract)
        db.commit()
        return True
    return False


def update_contract_analysis(db: Session, contract_id: int, analysis_results: Dict[str, Any]) -> Optional[Contract]:
    """Update a contract with analysis results."""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if contract:
        contract.analysis_results = analysis_results
        db.commit()
        db.refresh(contract)
        return contract
    return None