from typing import Optional
from pydantic import BaseModel

class ClauseResult(BaseModel):
    text: str
    confidence: float
    found: bool

class ContractAnalysis(BaseModel):
    """
    Schema for contract analysis results.
    This schema includes various clauses that are typically found in contracts.
    """
    termination: ClauseResult
    confidentiality: ClauseResult 
    payment_terms: ClauseResult
    governing_law: ClauseResult
    liability: ClauseResult

class ContractAnalysisResponse(BaseModel):
    """
    Schema for contract analysis API response.
    This schema includes the contract ID and the analysis results.
    """
    contract_id: int
    analysis: ContractAnalysis
    engine: str 
    
    class Config:
        from_attributes = True