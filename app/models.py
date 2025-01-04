from datetime import date
from sqlmodel import Field, SQLModel

class Track(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    year: str = Field(index=True)
    updated: date = Field()
    current_count: int = Field()
    type: str = Field()  # 'ld' or 'rd'


