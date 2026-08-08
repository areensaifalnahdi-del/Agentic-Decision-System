from pydantic import BaseModel

class FinalRecommendation(BaseModel):
    order_id: str
    selected_machine: str
    justification: str
    required_actions: dict
    machines_filtered_out: list[dict]
    evidence: dict
