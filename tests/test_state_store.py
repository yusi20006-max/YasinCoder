import json

from core.state_store import StateStore


def test_projects_sessions_tasks_memory_and_backup(tmp_path):
    store = StateStore(tmp_path / "data")
    project = store.create_project("p1", "Demo", tmp_path / "workspace")
    assert project["id"] == "p1"
    store.create_session("s1", "p1", "Session", {"messages": ["hello"]})
    store.create_task("t1", "p1", "Build", metadata={"priority": "high"})
    store.add_memory("p1", "important architecture decision")
    assert len(store.list_projects()) == 1
    assert store.get_session("s1")["state"]["messages"] == ["hello"]
    assert store.list_tasks("p1")[0]["title"] == "Build"
    assert store.search_memory("p1", "architecture")[0]["content"].startswith("important")
    assert list((tmp_path / "data" / "backups").glob("*.sqlite3"))
    store.close()


def test_restart_and_export_import(tmp_path):
    data = tmp_path / "data"
    store = StateStore(data)
    store.create_project("p1", "Demo", tmp_path / "workspace")
    store.create_task("t1", "p1", "Persist")
    export_path = tmp_path / "export.json"
    store.export_project("p1", export_path)
    store.close()

    reopened = StateStore(data)
    assert reopened.get_project("p1")["name"] == "Demo"
    assert reopened.list_tasks("p1")[0]["title"] == "Persist"
    imported = reopened.import_project(export_path, "p2")
    assert imported == "p2"
    assert reopened.get_project("p2")["root"] == str((tmp_path / "workspace").resolve())
    reopened.close()


def test_runtime_state_is_outside_repository(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.chdir(repo)
    store = StateStore(tmp_path / "user-data")
    store.create_project("p1", "Demo", repo)
    assert not (repo / "state.sqlite3").exists()
    assert not (repo / "history.json").exists()
    assert (tmp_path / "user-data" / "state.sqlite3").exists()
    store.close()
