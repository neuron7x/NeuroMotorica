import os
import pytest


def test_sample_data_exists(sample_data_dir):
    # Якщо fixture sample_data_dir не пройшла — тест автоматично пропущений
    assert os.path.isdir(sample_data_dir), "sample_data directory should exist for this test"

    # Перевіримо хоча б один файл у sample_data
    entries = [p for p in os.listdir(sample_data_dir) if not p.startswith('.')]
    assert len(entries) > 0, "sample_data should contain example files"
