import uuid
from datetime import datetime
from typing import Dict, Optional
from models.company_models import CompanyConfig, CompanyConfigRequest

class CompanyService:
    """Service for managing company configurations"""
    
    def __init__(self):
        
        self._configs: Dict[str, CompanyConfig] = {}
    
    def create_config(self, request: CompanyConfigRequest) -> CompanyConfig:
        """Create a new company configuration"""
        config_id = str(uuid.uuid4())[:8].upper()  
        
        config = CompanyConfig(
            config_id=config_id,
            company_name=request.company_name,
            custom_instructions=request.custom_instructions,
            created_at=datetime.now()
        )
        
        self._configs[config_id] = config
        return config
    
    def get_config(self, config_id: str) -> Optional[CompanyConfig]:
        """Get a company configuration by ID"""
        return self._configs.get(config_id)
    
    def config_exists(self, config_id: str) -> bool:
        """Check if a configuration exists"""
        return config_id in self._configs
