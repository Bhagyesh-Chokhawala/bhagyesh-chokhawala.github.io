from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

try:
    import asgi
    from workers import WorkerEntrypoint

    CLOUDFLARE_WORKER = True
except ImportError:
    CLOUDFLARE_WORKER = False

try:
    from .engine import engine
    from .models import FeedbackRequest, FeedbackResponse, RecommendationResponse
    from .store import store
except ImportError:
    from engine import engine
    from models import FeedbackRequest, FeedbackResponse, RecommendationResponse
    from store import store

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="Active Inference EFE Recommender POC",
    version="1.0.0",
    description=(
        "End-to-end proof of concept for a modular recommender that retrieves candidates, "
        "re-ranks them with decomposed Expected Free Energy, records explanation traces, "
        "and updates user belief state from feedback."
    ),
)
if not CLOUDFLARE_WORKER:
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def root():
        return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "efe-recommender-poc"}


@app.get("/api/users")
def users():
    return list(store.users.values())


@app.get("/api/items")
def items():
    return list(store.items.values())


@app.get("/api/users/{user_id}/belief")
def belief(user_id: str):
    if user_id not in store.users:
        raise HTTPException(status_code=404, detail="Unknown user")
    return store.users[user_id]


@app.get("/api/recommendations/{user_id}", response_model=RecommendationResponse)
def recommendations(
    user_id: str,
    top_k: int = Query(default=5, ge=1, le=10),
    candidate_limit: int = Query(default=8, ge=1, le=10),
    exploration: float = Query(default=0.5, ge=0.0, le=1.0),
    risk_control: float = Query(default=1.0, ge=0.0, le=2.0),
):
    if user_id not in store.users:
        raise HTTPException(status_code=404, detail="Unknown user")
    response = engine.recommend(
        store.users[user_id],
        store.items.values(),
        top_k=min(top_k, candidate_limit),
        candidate_limit=candidate_limit,
        exploration_control=exploration,
        risk_control=risk_control,
    )
    store.add_audit(event_type="recommendation", user_id=user_id, payload=response.model_dump())
    return response


@app.post("/api/feedback", response_model=FeedbackResponse)
def feedback(request: FeedbackRequest):
    if request.user_id not in store.users:
        raise HTTPException(status_code=404, detail="Unknown user")
    if request.item_id not in store.items:
        raise HTTPException(status_code=404, detail="Unknown item")

    before = store.users[request.user_id].model_copy(deep=True)
    after = engine.update_belief(before, store.items[request.item_id], request.outcome)
    store.users[request.user_id] = after
    store.add_audit(
        event_type="feedback",
        user_id=request.user_id,
        item_id=request.item_id,
        payload={"outcome": request.outcome, "belief_before": before.model_dump(), "belief_after": after.model_dump()},
    )
    return FeedbackResponse(
        belief_before=before,
        belief_after=after,
        message="Belief state updated; request recommendations again to observe the ranking change.",
    )


@app.get("/api/audit")
def audit(limit: int = Query(default=50, ge=1, le=500)):
    return store.audit[-limit:]


@app.post("/api/reset")
def reset():
    store.reset()
    return {"status": "reset", "users": len(store.users), "items": len(store.items)}


if CLOUDFLARE_WORKER:
    @app.get("/{path:path}", include_in_schema=False)
    async def frontend(path: str, request: Request):
        env = request.scope["env"]
        asset_path = path or "index.html"
        asset_response = await env.ASSETS.fetch(f"https://assets.local/{asset_path}")
        return Response(
            content=await asset_response.bytes(),
            status_code=asset_response.status,
            headers=dict(asset_response.headers),
        )

    class Default(WorkerEntrypoint):
        async def fetch(self, request):
            return await asgi.fetch(app, request, self.env)
