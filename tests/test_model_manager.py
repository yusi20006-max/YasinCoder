import json

from models.manager import ModelManager


def test_registry_lifecycle(tmp_path):
    path = tmp_path / "models.json"
    manager = ModelManager(path)
    assert manager.list() == []

    manager.upsert({"name": "my-local", "type": "openai_compatible", "base_url": "http://127.0.0.1:9999", "model": "my-model"})
    assert manager.get("my-local")["model"] == "my-model"

    manager.select("my-local")
    assert manager.default()["name"] == "my-local"

    reloaded = ModelManager(path)
    assert reloaded.default()["name"] == "my-local"
    assert json.loads(path.read_text())["default"] == "my-local"

    assert reloaded.remove("my-local") is True
    assert reloaded.default() is None
