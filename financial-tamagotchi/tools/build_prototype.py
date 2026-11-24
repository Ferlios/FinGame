"""Собирает прототип: data.js и standalone.html одним файлом.

Запуск: python tools/build_prototype.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
PROTO = ROOT / "prototype"

DATA_FILES = {
    "CONFIG": "game_config.json",
    "LEVELS": "levels.json",
    "CATEGORIES": "categories.json",
    "PETS": "pets.json",
    "SHOP_ITEMS": "shop_items.json",
    "QUESTS": "quests.json",
    "ACHIEVEMENTS": "achievements.json",
}


def load(name: str):
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


def safe_js(payload: str) -> str:
    # Не даём содержимому данных закрыть тег <script> в standalone-сборке.
    return payload.replace("</script", "<\\/script")


def build_data_js() -> str:
    entries = []
    for key, filename in DATA_FILES.items():
        value = safe_js(json.dumps(load(filename), ensure_ascii=False))
        entries.append(f"  {key}: {value}")
    return (
        "/* Сгенерировано tools/build_prototype.py — не редактировать вручную. */\n"
        "const DATA = {\n"
        + ",\n".join(entries)
        + "\n};\n"
    )


def build_standalone(index_html: str, data_js: str) -> str:
    css = (PROTO / "styles.css").read_text(encoding="utf-8")
    scripts = [
        data_js,
        (PROTO / "game.js").read_text(encoding="utf-8"),
        (PROTO / "ui.js").read_text(encoding="utf-8"),
        (PROTO / "app.js").read_text(encoding="utf-8"),
    ]

    html = index_html
    html = html.replace(
        '<link rel="stylesheet" href="styles.css">',
        "<style>\n" + css + "\n</style>",
    )
    bundle = "\n".join(f"<script>\n{safe_js(s)}\n</script>" for s in scripts)
    html = html.replace(
        '<script src="data.js"></script>\n'
        '<script src="game.js"></script>\n'
        '<script src="ui.js"></script>\n'
        '<script src="app.js"></script>',
        bundle,
    )
    return html


def main() -> None:
    data_js = build_data_js()
    (PROTO / "data.js").write_text(data_js, encoding="utf-8")
    print("wrote prototype/data.js")

    index_html = (PROTO / "index.html").read_text(encoding="utf-8")
    if '<script src="app.js"></script>' not in index_html:
        raise SystemExit(
            "prototype/index.html не подключает app.js — добавь script перед сборкой."
        )

    standalone = build_standalone(index_html, data_js)
    (PROTO / "standalone.html").write_text(standalone, encoding="utf-8")
    print("wrote prototype/standalone.html")

    missing = [f for f in DATA_FILES.values() if not (DATA_DIR / f).exists()]
    if missing:
        print("ВНИМАНИЕ: не хватает файлов данных:", ", ".join(missing))


if __name__ == "__main__":
    main()
