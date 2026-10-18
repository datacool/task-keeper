from sqlalchemy import event

from app.services import task_service


def _count_selects(db, fn):
    statements = []

    def on_execute(conn, cursor, statement, *args):
        if statement.lstrip().upper().startswith("SELECT"):
            statements.append(statement)

    engine = db.get_bind()
    event.listen(engine, "before_cursor_execute", on_execute)
    try:
        tasks = fn()
        for t in tasks:
            _ = [tag.name for tag in t.tags]  # 직렬화 시 접근을 재현
    finally:
        event.remove(engine, "before_cursor_execute", on_execute)
    return len(statements)


def test_list_tasks_query_count_is_constant(db_session):
    for i in range(3):
        task_service.create_task(db_session, f"할일{i}", ["개인", "긴급"])
    db_session.expire_all()
    few = _count_selects(db_session, lambda: task_service.list_tasks(db_session))

    for i in range(3, 30):
        task_service.create_task(db_session, f"할일{i}", ["개인", "긴급"])
    db_session.expire_all()
    many = _count_selects(db_session, lambda: task_service.list_tasks(db_session))

    assert few == many == 2  # tasks 1회 + tags 1회
