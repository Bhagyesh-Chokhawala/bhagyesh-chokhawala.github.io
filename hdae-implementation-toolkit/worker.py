"""Cloudflare Python Workers entrypoint (no paid Containers required)."""
from workers import wsgi
import json
import uuid
from flask import g, request, session
from pyodide.ffi import run_sync
import app as toolkit

app = toolkit.create_app()


def persistent_wizard_state():
    """Load only this session's state; Worker isolates are not persistent storage."""
    if not hasattr(g, "wizard_state"):
        state_id = session.setdefault("hdae_state_id", uuid.uuid4().hex)
        database = request.environ["workers.env"].STATE_DB
        payload = run_sync(database.prepare(
            "SELECT payload FROM wizard_state WHERE id = ?"
        ).bind(state_id).first("payload"))
        g.wizard_state = json.loads(payload) if payload else {}
        g.wizard_original = json.dumps(g.wizard_state, sort_keys=True)
        g.wizard_state_id = state_id
    return g.wizard_state


toolkit._wizard_state = persistent_wizard_state


@app.after_request
def save_wizard_state(response):
    if hasattr(g, "wizard_state"):
        payload = json.dumps(g.wizard_state, sort_keys=True)
        if response.status_code < 400 and payload != g.wizard_original:
            database = request.environ["workers.env"].STATE_DB
            run_sync(database.prepare(
                "INSERT INTO wizard_state (id, payload) VALUES (?, ?) "
                "ON CONFLICT(id) DO UPDATE SET payload = excluded.payload"
            ).bind(g.wizard_state_id, payload).run())
    return response


Default = wsgi.entrypoint(app)
