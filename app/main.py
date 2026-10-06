from fastapi import FastAPI, HTTPException

from app.answer import answer
from app.episodes import list_seasons, list_shows
from app.models import AskRequest, AskResponse, SeasonsResponse, ShowsResponse
from app.retrieval import SpoilerFilterError

app = FastAPI(title="episode-scoped-rag")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/shows", response_model=ShowsResponse)
def get_shows():
    return {"shows": list_shows()}


@app.get("/api/shows/{show}/seasons", response_model=SeasonsResponse)
def get_seasons(show: str):
    try:
        return {"show": show, "seasons": list_seasons(show)}
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))


@app.post("/api/ask", response_model=AskResponse)
def post_ask(request: AskRequest):
    try:
        return answer(
            request.question, request.show, request.season, request.episode
        )
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except SpoilerFilterError as error:
        raise HTTPException(status_code=500, detail=str(error))
    except ConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Can't reach Ollama. Start it with 'ollama serve' and try again.",
        )