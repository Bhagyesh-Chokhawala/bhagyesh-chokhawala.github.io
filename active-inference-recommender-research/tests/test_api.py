from fastapi.testclient import TestClient
from app.main import app
from app.store import store

client = TestClient(app)


def setup_function():
    store.reset()


def test_health():
    r = client.get('/api/health')
    assert r.status_code == 200
    assert r.json()['status'] == 'ok'


def test_recommendations_have_component_trace():
    r = client.get('/api/recommendations/user_101?top_k=3')
    assert r.status_code == 200
    body = r.json()
    assert len(body['recommendations']) == 3
    trace = body['recommendations'][0]['trace']
    for key in ['pragmatic_mismatch', 'epistemic_value', 'exposure_risk', 'ambiguity', 'efe_score']:
        assert key in trace


def test_feedback_updates_belief_and_audit_log():
    before = client.get('/api/users/user_101/belief').json()
    r = client.post('/api/feedback', json={'user_id':'user_101', 'item_id':'I002', 'outcome':'like'})
    assert r.status_code == 200
    after = r.json()['belief_after']
    assert after['uncertainty'] < before['uncertainty']
    audit = client.get('/api/audit').json()
    assert len(audit) == 1
    assert audit[0]['event_type'] == 'feedback'
