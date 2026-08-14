from models.manager import ModelManager


class ModelsCommand:
    def __init__(self, manager=None):
        self.manager = manager or ModelManager()

    def run(self):
        return {
            "default": self.manager.data.get("default", ""),
            "models": self.manager.list(),
            "config_file": str(self.manager.path),
        }

    def discover(self):
        return self.manager.ensure_discovered()

    def add(self, model):
        return self.manager.upsert(model)

    def remove(self, name):
        return self.manager.remove(name)

    def select(self, name):
        return self.manager.select(name)
