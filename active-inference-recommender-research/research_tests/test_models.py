import torch
from efe_recsys.data.synthetic import load_synthetic
from efe_recsys.models import BPRMF, LightGCN, SASRec, build_normalized_adj


def test_model_score_shapes():
    b = load_synthetic(seed=2, n_users=8, n_items=20)
    bpr = BPRMF(b.n_users, b.n_items, 8)
    assert bpr.score_all(0, b.train_by_user[0]).shape == (b.n_items,)

    adj = build_normalized_adj(b.n_users, b.n_items, b.train_by_user, torch.device("cpu"))
    gcn = LightGCN(b.n_users, b.n_items, adj, 8, 1)
    assert gcn.score_all(0, b.train_by_user[0]).shape == (b.n_items,)

    sas = SASRec(b.n_items, 8, 10, 2, 1, 0.0)
    sas.eval()
    assert sas.score_all(0, b.train_by_user[0]).shape == (b.n_items,)
