from models.manager import ModelManager


class ModelsCommand:
    def __init__(self, manager=None):
        self.manager = manager or ModelManager()

    def run(self):
        default = self.manager.default()
        return {
            "default": default.get("name", "") if default else "",
            "models": self.manager.list(),
            "config_file": str(self.manager.path),
            "validation_errors": self.manager.validate_all(),
        }

    def discover(self):
        return self.manager.ensure_discovered()

    def add(self, model):
        return self.manager.upsert(model)

    def remove(self, name):
        return self.manager.remove(name)

    def select(self, name):
        return self.manager.select(name)

    def validate(self):
        return self.manager.validate_all()
