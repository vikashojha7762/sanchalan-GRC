from pydantic import BaseModel
from typing import Optional, Dict, Any


class DashboardSummary(BaseModel):
    total_frameworks: int
    total_controls: int
    total_policies: int
    total_gaps: int
    gaps_by_severity: Dict[str, int]
    gaps_by_status: Dict[str, int]
    total_remediations: int
    remediations_by_status: Dict[str, int]
    compliance_score: Optional[float] = None
    recent_gaps: Optional[list] = None
    recent_policies: Optional[list] = None
