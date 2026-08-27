"""FastAPI app. Owner: Ian. Keep CORS open, this is a demo."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Corridor Credit")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True}

# TODO: GET /households  and  GET /score/{id}
