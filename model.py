from typing import List, Optional
from pydantic import BaseModel

class SearchRequestFilter(BaseModel):
    legalEntity: str = "General"
    divisions: str = "General"
    employeeTypes: str = "General"
    departments: str = "General"
class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 10
    userId: str
    filters: SearchRequestFilter #Optional[List[Optional[str]]] = ["General","General","General","General","General"]


class TagRequestData(BaseModel):
    fileName: str

class TagRequestValue(BaseModel):
    recordId: str
    data: TagRequestData

class TagRequest(BaseModel):
    values: List[TagRequestValue]