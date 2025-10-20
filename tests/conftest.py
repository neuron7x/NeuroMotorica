import os
import sys
import pytest

# Додаємо src/ в sys.path щоб імпортувати пакет як editable install fallback
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
if os.path.isdir(SRC):
    sys.path.insert(0, SRC)


@pytest.fixture(scope="session")
def sample_data_dir():
    """Шлях до sample_data, якщо існує — корисно для інтеграційних тестів."""
    sd = os.path.join(ROOT, "sample_data")
    if os.path.isdir(sd):
        return sd
    pytest.skip("sample_data directory not found; skipping tests that require sample data")
