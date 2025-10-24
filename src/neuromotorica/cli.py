# SPDX-License-Identifier: Apache-2.0
import typer
from neuromotorica.i18n.core import activate, _
from neuromotorica.bench.__init__ import app as bench_app
from neuromotorica.validate.__init__ import app as validate_app

app = typer.Typer(no_args_is_help=True, help="Neuromotorica CLI")

@app.callback()
def main(lang: str = typer.Option(None, "--lang", help="Interface language (uk/en)")):
    activate(lang)

app.add_typer(bench_app, name="bench")
app.add_typer(validate_app, name="validate")

if __name__ == "__main__":
    app()
