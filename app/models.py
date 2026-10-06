from pydantic import BaseModel, Field


class Source(BaseModel):
    season: int
    episode: int
    title: str


class AskRequest(BaseModel):
    show: str = Field(min_length=1)
    season: int = Field(ge=1)
    episode: int = Field(ge=1)
    question: str = Field(min_length=1, max_length=1000)


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]


class Season(BaseModel):
    season: int
    episodes: list[int]


class ShowsResponse(BaseModel):
    shows: list[str]


class SeasonsResponse(BaseModel):
    show: str
    seasons: list[Season]