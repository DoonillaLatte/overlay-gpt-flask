import importlib
import pkgutil
import prompts

prompt_registry = {}

def register_prompt(name):
    def wrapper(cls):
        prompt_registry[name] = cls()
        return cls
    return wrapper

def load_prompts():
    for _, module_name, _ in pkgutil.iter_modules(prompts.__path__):
        importlib.import_module(f"{prompts.__name__}.{module_name}")
