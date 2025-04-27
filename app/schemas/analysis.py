from typing import Optional
from pydantic import BaseModel

class ContractAnalysis(BaseModel):
    """
    Schema for contract analysis results.
    This schema includes various clauses that are typically found in contracts.
    """
    termination_clause: str
    confidentiality_clause: str
    payment_terms: str 
    governing_law: str
    limitation_of_liability: str

class ContractAnalysisResponse(BaseModel):
    """
    Schema for contract analysis API response.
    This schema includes the contract ID and the analysis results.
    """
    contract_id: int
    analysis: ContractAnalysis
    
    class Config:
        from_attributes = True