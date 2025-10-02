from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid

class CompanyConfigRequest(BaseModel):
    """Request model for company configuration"""
    company_name: str = Field(..., min_length=1, max_length=200, description="Nome da empresa")
    custom_instructions: str = Field(default="", max_length=2000, description="Instruções personalizadas para a IA")

class CompanyConfig(BaseModel):
    """Company configuration model"""
    config_id: str
    company_name: str
    custom_instructions: str
    created_at: datetime

class CompanyConfigResponse(BaseModel):
    """Response model for company configuration"""
    config_id: str
    company_name: str
    message: str
