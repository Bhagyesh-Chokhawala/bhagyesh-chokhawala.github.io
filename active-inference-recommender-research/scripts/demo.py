from pprint import pprint

from app.engine import engine
from app.store import store


def main():
    user = store.get_user('user_101')
    print('\n=== Initial belief ===')
    pprint(user.model_dump())

    print('\n=== Initial recommendations ===')
    first = engine.recommend(user, store.items.values(), top_k=5)
    for rec in first.recommendations:
        print(f"{rec.rank}. {rec.title:48} EFE={rec.trace.efe_score:.3f} | {rec.explanation}")

    chosen = first.recommendations[0]
    updated = engine.update_belief(user, store.get_item(chosen.item_id), 'like')
    store.users[user.user_id] = updated

    print(f"\n=== Feedback: LIKE {chosen.title} ===")
    pprint(updated.model_dump())

    print('\n=== Recommendations after feedback ===')
    second = engine.recommend(updated, store.items.values(), top_k=5)
    for rec in second.recommendations:
        print(f"{rec.rank}. {rec.title:48} EFE={rec.trace.efe_score:.3f} | {rec.explanation}")


if __name__ == '__main__':
    main()
