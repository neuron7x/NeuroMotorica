import json

from neuromotorica.analysis import viz_cli


def test_viz_cli_main_outputs_expected_json(monkeypatch, tmp_path, capsys):
    recorded_kwargs = {}
    expected_files = ["plot-a.png", "plot-b.png"]

    def fake_plot_scenarios(**kwargs):
        recorded_kwargs.update(kwargs)
        return expected_files

    monkeypatch.setattr(viz_cli, "plot_scenarios", fake_plot_scenarios)

    viz_cli.main(
        outdir=str(tmp_path),
        seconds=2.5,
        units=128,
        rate=20.0,
    )

    output = capsys.readouterr().out.strip()
    assert json.loads(output) == {"saved": expected_files}

    assert recorded_kwargs == {
        "outdir": str(tmp_path),
        "seconds": 2.5,
        "units": 128,
        "rate_hz": 20.0,
    }
