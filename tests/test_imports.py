import pytest


def test_package_import():
    # Безпечна перевірка: якщо пакета немає — тест буде пропущено
    pytest.importorskip(
        "neuromotorica", reason="neuromotorica package not installed; skipping import tests"
    )

    # Якщо імпорт пройшов — виконуємо базову перевірку API
    import importlib

    pkg = importlib.import_module("neuromotorica")
    # Очікуємо, що package має атрибут __version__ (багато проектів його мають)
    if hasattr(pkg, "__version__"):
        v = getattr(pkg, "__version__")
        assert isinstance(v, str)
