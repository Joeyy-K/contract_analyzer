# app/api/v1/contracts.py
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.crud.contract import create_contract, get_contract, get_user_contracts, update_contract_analysis
from app.models.user import User
from app.schemas.contract import Contract, ContractCreate, ContractResponse
from app.api.deps import get_current_user, get_db
from app.services.file_parser import parse_contract_text
from app.services.contract_analyzer import analyze_contract_text
from app.schemas.analysis import ContractAnalysisResponse, ContractAnalysis

router = APIRouter()

@router.post("/upload", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
async def upload_contract(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload and parse a contract file (PDF or DOCX).
    The file content will be extracted and stored in the database.
    """
    try:
        # Parse and extract text from the uploaded file
        file_type, content = await parse_contract_text(file)
        
        # Create contract in DB
        contract_in = ContractCreate(
            filename=file.filename,
            file_type=file_type,
            content=content,
            user_id=current_user.id
        )
        
        contract = create_contract(db=db, contract=contract_in)
        return contract
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log the error
        print(f"Error processing contract: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process contract. Please try again."
        )


@router.get("/", response_model=List[ContractResponse])
def list_user_contracts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all contracts uploaded by the current user."""
    contracts = get_user_contracts(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )
    return contracts


@router.get("/{contract_id}", response_model=Contract)
def get_contract_detail(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific contract including its content."""
    contract = get_contract(db=db, contract_id=contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if contract.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return contract

@router.post("/{contract_id}/analyze", response_model=ContractAnalysisResponse)
async def analyze_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Analyze contract text for specific clauses.
    This endpoint will return the analysis results including
    termination clause, confidentiality clause, payment terms,
    governing law, and limitation of liability.
    """
    contract = get_contract(db=db, contract_id=contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    if contract.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    try:
        analysis_results = await analyze_contract_text(contract.content)
        
        if "error" in analysis_results:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=analysis_results["error"]
            )

        updated_contract = update_contract_analysis(
            db=db, 
            contract_id=contract_id, 
            analysis_results=analysis_results
        )

        analysis = ContractAnalysis(
            termination_clause=analysis_results.get("termination_clause", "Not found"),
            confidentiality_clause=analysis_results.get("confidentiality_clause", "Not found"),
            payment_terms=analysis_results.get("payment_terms", "Not found"),
            governing_law=analysis_results.get("governing_law", "Not found"),
            limitation_of_liability=analysis_results.get("limitation_of_liability", "Not found")
        )
        
        return ContractAnalysisResponse(
            contract_id=contract_id,
            analysis=analysis
        )
        
    except Exception as e:
        print(f"Error analyzing contract: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze contract: {str(e)}"
        )