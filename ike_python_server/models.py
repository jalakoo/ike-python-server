from pydantic import BaseModel


class Node(BaseModel):
    id: str
    label: str
    properties: dict = None


class Relationship(BaseModel):
    source_id: str
    target_id: str
    type: str
    properties: dict = None
