import json


def test_main_prints_expected_json(monkeypatch, capsys, tmp_path):
    """CLI should forward arguments and print JSON with saved files metadata."""

    from neuromotorica.analysis import viz_cli

    expected_response = {"plots": ["figure-1.png", "figure-2.png"]}
    captured_kwargs = {}

    def fake_plot_scenarios(*, outdir, seconds, units, rate_hz):
        captured_kwargs.update(
            {
                "outdir": outdir,
                "seconds": seconds,
                "units": units,
                "rate_hz": rate_hz,
            }
        )
        return expected_response

    monkeypatch.setattr(viz_cli, "plot_scenarios", fake_plot_scenarios)

    custom_kwargs = {
        "outdir": str(tmp_path),
        "seconds": 2.5,
        "units": 128,
        "rate": 42.0,
    }

    viz_cli.main(**custom_kwargs)

    captured = json.loads(capsys.readouterr().out)
    assert captured == {"saved": expected_response}

    assert captured_kwargs == {
        "outdir": custom_kwargs["outdir"],
        "seconds": custom_kwargs["seconds"],
        "units": custom_kwargs["units"],
        "rate_hz": custom_kwargs["rate"],
    }
