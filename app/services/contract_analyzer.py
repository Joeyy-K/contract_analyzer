# === File: app/services/contract_analyzer.py (Complete) ===
import json
import logging
from typing import Dict, Any
import requests
import asyncio

from app.core.config import settings

logger = logging.getLogger(__name__)

async def analyze_contract_text(contract_text: str) -> Dict[str, Any]:
    """
    Analyze contract text using Hugging Face's Inference API to extract key legal clauses.
    
    Args:
        contract_text: The raw text of the contract document
        
    Returns:
        A dictionary containing extracted clauses and their content
    """
    try:
        # Check if HUGGINGFACE_API_TOKEN is available
        if not settings.HUGGINGFACE_API_TOKEN:
            # Fallback to backup analysis method
            return await analyze_contract_with_fallback(contract_text)
            
        # model that works with the free tier
        API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-large"
        
        headers = {
            "Authorization": f"Bearer {settings.HUGGINGFACE_API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # contract text to stay within limits
        shortened_text = contract_text[:3000]  # Takes first 3000 chars to stay within context window
        
        section_numbers = {
            "termination_clause": ["3", "termination", "term"],
            "confidentiality_clause": ["4", "confidential", "confid"],
            "payment_terms": ["2", "payment", "compensation", "fees"],
            "governing_law": ["5", "law", "govern"],
            "limitation_of_liability": ["6", "liab", "limit"]
        }

        # Processes each clause separately with explicit requests
        clause_names = [
            "termination_clause",
            "confidentiality_clause",
            "payment_terms",
            "governing_law",
            "limitation_of_liability"
        ]
        
        results = {}
        
        for clause in clause_names:
            # Format a specific question for each clause
            prompt = f"Extract the {clause.replace('_', ' ')} from this contract or respond with 'Not found': {shortened_text}"
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 250,  
                    "temperature": 0.1
                }
            }
            
            try:
                response = requests.post(API_URL, headers=headers, json=payload)
                
                if response.status_code == 200:
                    response_data = response.json()
                    
                    if isinstance(response_data, list) and len(response_data) > 0:
                        clause_text = response_data[0].get("generated_text", "Not found")
                    else:
                        clause_text = response_data.get("generated_text", "Not found")
                    
                    # Clean up the response 
                    if clause_text.lower().startswith("the ") and " is:" in clause_text.lower():
                        clause_text = clause_text.split(" is:", 1)[1].strip()
                        
                    results[clause] = clause_text
                else:
                    logger.warning(f"Error getting {clause}: {response.status_code} - {response.text}")
                    results[clause] = "Error extracting clause"
            except Exception as e:
                logger.error(f"Error processing {clause}: {str(e)}")
                results[clause] = "Error extracting clause"
        
        return results
            
    except Exception as e:
        logger.error(f"Error during contract analysis: {str(e)}")
        return {"error": f"Failed to analyze contract: {str(e)}"}

async def analyze_contract_with_fallback(contract_text: str) -> Dict[str, Any]:
    """
    Fallback analysis method when HuggingFace API is not available.
    This is a simple rule-based extraction based on common patterns.
    
    Args:
        contract_text: The raw text of the contract document
        
    Returns:
        A dictionary containing extracted clauses and their content
    """
    results = {}
    contract_lower = contract_text.lower()

    # 1. Keyword extraction
    results["termination_clause"] = extract_clause_by_keywords(
        contract_text, contract_lower, [
            "termination", "terminate", "term and termination", 
            "cancellation", "cancel this agreement", "early termination",
            "right to terminate", "terminating this agreement", 
            "effect of termination", "agreement shall terminate",
            "end of term", "expiration", "canceling"
        ]
    )
    
    results["confidentiality_clause"] = extract_clause_by_keywords(
        contract_text, contract_lower, [
            "confidentiality", "confidential information", "non-disclosure"
        ]
    )
    
    results["payment_terms"] = extract_clause_by_keywords(
        contract_text, contract_lower, [
            "payment terms", "payment schedule", "fees", "compensation", "invoice"
        ]
    )
    
    results["governing_law"] = extract_clause_by_keywords(
        contract_text, contract_lower, [
            "governing law", "jurisdiction", "applicable law", "laws of", "governed by"
        ]
    )
    
    results["limitation_of_liability"] = extract_clause_by_keywords(
        contract_text, contract_lower, [
            "limitation of liability", "limited liability", "limitation on liability", "not be liable"
        ]
    )

    # 2. Section number-based extraction fallback
    section_numbers = {
        "termination_clause": ["3", "termination", "term"],
        "confidentiality_clause": ["4", "confidential", "confid"],
        "payment_terms": ["2", "payment", "compensation", "fees"],
        "governing_law": ["5", "law", "govern"],
        "limitation_of_liability": ["6", "liab", "limit"]
    }

    for clause_type, identifiers in section_numbers.items():
        if results.get(clause_type, "Not found") == "Not found":
            for iden in identifiers:
                # Look for a section header like "\n3." or "\nPayment Terms"
                pattern = f"\n{iden}."
                idx = contract_lower.find(pattern)
                
                if idx == -1:
                    # Try to match by keyword
                    idx = contract_lower.find(iden)
                
                if idx != -1:
                    # Find section start
                    start_pos = contract_text[:idx].rfind("\n\n")
                    if start_pos == -1:
                        start_pos = max(0, contract_text[:idx].rfind("\n"))
                    
                    # Find section end 
                    end_pos = contract_text.find("\n\n", idx)
                    if end_pos == -1:
                        end_pos = len(contract_text)
                    
                    extracted_text = contract_text[start_pos:end_pos].strip()

                    if len(extracted_text) > 1000:
                        paragraphs = extracted_text.split("\n")
                        for i, para in enumerate(paragraphs):
                            if iden.lower() in para.lower():
                                start_para = max(0, i-1)
                                end_para = min(len(paragraphs), i+3)
                                extracted_text = "\n".join(paragraphs[start_para:end_para])
                                break

                    results[clause_type] = extracted_text
                    break 

    return results


def extract_clause_by_keywords(text: str, text_lower: str, keywords: list, context_length: int = 300) -> str:
    for keyword in keywords:
        index = text_lower.find(keyword)
        if index != -1:
            # Look for section headers (numbered sections or all caps)
            section_pattern = r"\n\s*(\d+\.|\#{1,3}|[A-Z][A-Z\s]+:)\s+"
            
            # Find section start (look backward for section headers)
            start_pos = text[:index].rfind("\n\n")
            if start_pos == -1:  # If no double newline, try single newline
                start_pos = max(0, text[:index].rfind("\n"))
            
            # Find section end (next double newline or section header)
            end_pos = text.find("\n\n", index)
            if end_pos == -1:  
                end_pos = len(text)

            extracted_text = text[start_pos:end_pos].strip()
            
            # If extracted text is too long
            if len(extracted_text) > 1000:
                # paragraph boundaries
                paragraphs = extracted_text.split("\n")
                # Find which paragraph contains keywords
                for i, para in enumerate(paragraphs):
                    if keyword in para.lower():
                        # Take this paragraph and adjacent ones
                        start_para = max(0, i-1)
                        end_para = min(len(paragraphs), i+3)
                        return "\n".join(paragraphs[start_para:end_para])
            
            return extracted_text
    
    return "Not found"