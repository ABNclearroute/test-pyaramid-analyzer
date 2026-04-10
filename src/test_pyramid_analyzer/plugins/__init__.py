"""Language plugin registry.

All built-in plugins are registered here. External plugins can be added by
calling ``register_plugin`` before running an analysis.

Built-in language support
-------------------------
Python     · Java        · JavaScript/TypeScript
Go         · Ruby        · C# (.NET)
Rust       · Kotlin      · PHP
C/C++      · Groovy      · Scala
"""
from __future__ import annotations

from typing import Dict, List, Optional

from .base import LanguagePlugin
from .cpp_plugin import CppPlugin
from .csharp_plugin import CSharpPlugin
from .go_plugin import GoPlugin
from .groovy_plugin import GroovyPlugin
from .java_plugin import JavaPlugin
from .javascript_plugin import JavaScriptPlugin
from .kotlin_plugin import KotlinPlugin
from .php_plugin import PhpPlugin
from .python_plugin import PythonPlugin
from .ruby_plugin import RubyPlugin
from .rust_plugin import RustPlugin
from .scala_plugin import ScalaPlugin

_REGISTRY: Dict[str, LanguagePlugin] = {}

_BUILTIN_PLUGINS = (
    PythonPlugin,
    JavaPlugin,
    JavaScriptPlugin,
    GoPlugin,
    RubyPlugin,
    CSharpPlugin,
    RustPlugin,
    KotlinPlugin,
    PhpPlugin,
    CppPlugin,
    GroovyPlugin,
    ScalaPlugin,
)


def _register_defaults() -> None:
    for cls in _BUILTIN_PLUGINS:
        instance = cls()
        _REGISTRY[instance.name] = instance


def register_plugin(plugin: LanguagePlugin) -> None:
    """Register a custom language plugin, overriding any existing plugin with the same name."""
    _REGISTRY[plugin.name] = plugin


def get_plugin(name: str) -> Optional[LanguagePlugin]:
    """Return the registered plugin for *name*, or None."""
    return _REGISTRY.get(name)


def all_plugins() -> List[LanguagePlugin]:
    return list(_REGISTRY.values())


_register_defaults()

__all__ = [
    "LanguagePlugin",
    "PythonPlugin",
    "JavaPlugin",
    "JavaScriptPlugin",
    "GoPlugin",
    "RubyPlugin",
    "CSharpPlugin",
    "RustPlugin",
    "KotlinPlugin",
    "PhpPlugin",
    "CppPlugin",
    "GroovyPlugin",
    "ScalaPlugin",
    "register_plugin",
    "get_plugin",
    "all_plugins",
]
