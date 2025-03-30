from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime

@dataclass
class Source:
    """Modelo de dados para uma fonte de ebooks."""
    id: str
    name: str
    type: str
    path: str
    config: Dict[str, Any] = field(default_factory=dict)
    last_scan: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o objeto para um dicionário."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "path": self.path,
            "config": self.config,
            "last_scan": self.last_scan.isoformat() if self.last_scan else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Source':
        """Cria um objeto a partir de um dicionário."""
        source_data = dict(data)
        
        # Converter string de data para objeto datetime se existir
        if source_data.get("last_scan"):
            try:
                source_data["last_scan"] = datetime.fromisoformat(source_data["last_scan"])
            except:
                source_data["last_scan"] = None
                
        return cls(**source_data)