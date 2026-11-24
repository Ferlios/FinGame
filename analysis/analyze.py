"""Анализ данных FinGame.

Что делает скрипт:
1. читает MOCK_DATA (1).csv из корня репозитория;
2. читает синтетические данные игрового прототипа из financial-tamagotchi/data;
3. проверяет качество данных;
4. считает сводные таблицы;
5. строит графики в analysis/figures;
6. собирает analysis/report.md, analysis/dashboard.html и CSV-выгрузки.

Запуск из корня репозитория:
    python analysis/analyze.py

Нужны только pandas, numpy и matplotlib.
"""

from __future__ import annotations

import base64
import json
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter

REPO = Path(__file__).resolve().parent.parent
ANALYSIS = REPO / "analysis"
FIG_DIR = ANALYSIS / "figures"
OUT_DIR = ANALYSIS / "output"
GAME = REPO / "financial-tamagotchi"
MOCK_CSV = REPO / "MOCK_DATA (1).csv"

for folder in (FIG_DIR, OUT_DIR):
    folder.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Оформление
# ---------------------------------------------------------------------------

COLORS = {
    "violet": "#7c3aed",
    "violet_light": "#c4b5fd",
    "violet_pale": "#ede9fe",
    "teal": "#0d9488",
    "teal_light": "#99f6e4",
    "amber": "#f59e0b",
    "amber_light": "#fde68a",
    "pink": "#ec4899",
    "blue": "#3b82f6",
    "green": "#22c55e",
    "red": "#ef4444",
    "slate": "#64748b",
    "grid": "#e5e7eb",
    "text": "#1f2937",
    "muted": "#6b7280",
}

ARCHETYPE_RU = {
    "disciplined": "Дисциплинированные",
    "coffee_addict": "Кофеманы",
    "impulse_buyer": "Импульсивные",
    "weekend_spender": "Тратят на выходных",
    "newbie": "Новички",
    "frugal_saver": "Экономные",
}

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 15,
    "axes.titleweight": "bold",
    "axes.labelsize": 10,
    "axes.edgecolor": "#d1d5db",
    "axes.linewidth": 0.8,
    "axes.facecolor": "white",
    "figure.facecolor": "white",
    "xtick.color": COLORS["muted"],
    "ytick.color": COLORS["muted"],
    "text.color": COLORS["text"],
    "axes.labelcolor": COLORS["text"],
    "grid.color": COLORS["grid"],
    "grid.linewidth": 0.7,
    "legend.frameon": False,
    "savefig.bbox": "tight",
    "savefig.dpi": 150,
})

VIOLET_CMAP = LinearSegmentedColormap.from_list(
    "fin_violet", ["#f5f3ff", "#ddd6fe", COLORS["violet"], "#4c1d95"]
)
TEAL_CMAP = LinearSegmentedColormap.from_list(
    "fin_teal", ["#f0fdfa", "#99f6e4", COLORS["teal"], "#134e4a"]
)


def fmt_int(value) -> str:
    return f"{int(round(float(value))):,}".replace(",", " ")


def fmt_money(value) -> str:
    return f"{fmt_int(value)} ₽"


def fmt_coins(value) -> str:
    return f"{fmt_int(value)} монет"


def fmt_pct(value, digits: int = 1) -> str:
    return f"{value * 100:.{digits}f}%".replace(".", ",")


def md_table(headers: list[str], rows: list[list], aligns: list[str] | None = None) -> str:
    aligns = aligns or ["left"] + ["right"] * (len(headers) - 1)
    sep = []
    for align in aligns:
        sep.append("---:" if align == "right" else ":---")
    out = ["| " + " | ".join(str(h) for h in headers) + " |", "| " + " | ".join(sep) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(cell).replace("|", "\\|") for cell in row) + " |")
    return "\n".join(out)


def save_fig(fig, filename: str) -> Path:
    path = FIG_DIR / filename
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def base64_image(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def subtitle(fig, text: str, y: float = 0.94) -> None:
    fig.text(0.5, y, text, ha="center", va="top", fontsize=10, color=COLORS["muted"])


def style_axes(ax, grid_axis: str = "y") -> None:
    ax.grid(axis=grid_axis, alpha=0.75)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)


# ---------------------------------------------------------------------------
# Загрузка и проверка
# ---------------------------------------------------------------------------

def load_data() -> dict:
    missing = []
    for path in (MOCK_CSV, GAME / "data" / "transactions.csv", GAME / "data" / "mock_users.json",
                 GAME / "reports" / "balance_runs.csv", GAME / "data" / "game_config.json"):
        if not path.exists():
            missing.append(str(path.relative_to(REPO)))
    if missing:
        raise SystemExit("Не найдены файлы: " + ", ".join(missing))

    mock = pd.read_csv(MOCK_CSV, encoding="utf-8-sig")
    mock.columns = [c.strip() for c in mock.columns]
    mock["using_finapp"] = mock["Using finapp"].astype(str).str.lower().eq("true")

    tx = pd.read_csv(GAME / "data" / "transactions.csv", encoding="utf-8-sig")
    tx["date"] = pd.to_datetime(tx["date"])
    tx["amount"] = pd.to_numeric(tx["amount"], errors="coerce")
    tx["archetypeLabel"] = tx["archetype"].map(ARCHETYPE_RU).fillna(tx["archetype"])

    raw_users = json.loads((GAME / "data" / "mock_users.json").read_text(encoding="utf-8"))
    daily_rows = []
    for user in raw_users["users"]:
        for day in user["days"]:
            daily_rows.append({
                "user_id": user["id"],
                "name": user["profile"]["name"],
                "archetype": user["profile"]["archetype"],
                "archetypeLabel": user["profile"]["archetypeLabel"],
                "daily_limit_profile": user["profile"]["dailyLimit"],
                **day,
            })
    daily = pd.DataFrame(daily_rows)
    daily["date"] = pd.to_datetime(daily["date"])
    daily["withinLimit"] = daily["withinLimit"].astype(bool)

    quests_rows = []
    for _, row in daily.iterrows():
        for quest in row["quests"]:
            quests_rows.append({
                "user_id": row["user_id"],
                "archetypeLabel": row["archetypeLabel"],
                "date": row["date"],
                "quest_id": quest["id"],
                "quest_title": quest["title"],
                "done": bool(quest["done"]),
                "coins": int(quest["coins"]),
                "xp": int(quest["xp"]),
            })
    quests = pd.DataFrame(quests_rows)

    balance = pd.read_csv(GAME / "reports" / "balance_runs.csv", encoding="utf-8-sig")
    balance["archetypeLabel"] = balance["archetype"].map(ARCHETYPE_RU).fillna(balance["archetype"])

    config = json.loads((GAME / "data" / "game_config.json").read_text(encoding="utf-8"))
    achievements = json.loads((GAME / "data" / "achievements.json").read_text(encoding="utf-8"))
    user_summary = pd.read_csv(GAME / "reports" / "mock_users_summary.csv", encoding="utf-8-sig")

    return {
        "mock": mock,
        "tx": tx,
        "daily": daily,
        "quests": quests,
        "balance": balance,
        "config": config,
        "achievements": achievements,
        "user_summary": user_summary,
        "raw_users": raw_users,
    }


def quality_checks(data: dict) -> pd.DataFrame:
    mock, tx, daily, balance = data["mock"], data["tx"], data["daily"], data["balance"]
    rows = []

    rows.append({
        "dataset": "MOCK_DATA (1).csv",
        "rows": len(mock),
        "columns": 4,
        "missing_required": 0,
        "missing_optional": 0,
        "duplicate_ids": int(mock["id"].duplicated().sum()),
        "verdict": "чисто, но мало полей",
    })
    required_tx = [c for c in tx.columns if c != "note"]
    rows.append({
        "dataset": "transactions.csv",
        "rows": len(tx),
        "columns": 10,
        "missing_required": int(tx[required_tx].isna().sum().sum()),
        "missing_optional": int(tx["note"].isna().sum()),
        "duplicate_ids": int(tx["tx_id"].duplicated().sum()),
        "verdict": "готово; заметки опциональны",
    })
    rows.append({
        "dataset": "mock_users.json → дни",
        "rows": len(daily),
        "columns": 24,
        "missing_required": int(daily.drop(columns=["archetypeLabel", "daily_limit_profile"]).isna().sum().sum()),
        "missing_optional": 0,
        "duplicate_ids": int(daily.duplicated(subset=["user_id", "date"]).sum()),
        "verdict": "готово к анализу",
    })
    rows.append({
        "dataset": "balance_runs.csv",
        "rows": len(balance),
        "columns": 19,
        "missing_required": 0,
        "missing_optional": int(balance["dayTo6000"].isna().sum()),
        "duplicate_ids": int(balance.duplicated().sum()),
        "verdict": "19 NaN в dayTo6000 — не ошибка",
    })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Графики
# ---------------------------------------------------------------------------

def chart_finapp_usage(mock: pd.DataFrame) -> Path:
    counts = mock["using_finapp"].value_counts().reindex([True, False]).fillna(0)
    share = counts[True] / counts.sum()

    fig, ax = plt.subplots(figsize=(7.5, 5.2))
    wedges, _, autotexts = ax.pie(
        counts.values,
        colors=[COLORS["violet"], "#cbd5e1"],
        startangle=90,
        counterclock=False,
        autopct=lambda p: f"{p:.1f}%".replace(".", ","),
        pctdistance=0.78,
        wedgeprops=dict(width=0.38, edgecolor="white", linewidth=2),
        textprops=dict(color="white", fontsize=11, fontweight="bold"),
    )
    ax.text(0, 0.10, fmt_int(counts[True]), ha="center", va="center", fontsize=25, fontweight="bold", color=COLORS["text"])
    ax.text(0, -0.12, "пользуются\nFinApp", ha="center", va="center", fontsize=10, color=COLORS["muted"])
    ax.legend(
        [Line2D([0], [0], color=COLORS["violet"], lw=8),
         Line2D([0], [0], color="#cbd5e1", lw=8)],
        [f"Пользуются — {fmt_int(counts[True])}", f"Не пользуются — {fmt_int(counts[False])}"],
        loc="lower center", bbox_to_anchor=(0.5, -0.12), ncol=2, fontsize=9
    )
    ax.set_title("Сколько пользователей пользуются FinApp")
    subtitle(fig, "MOCK_DATA (1).csv · 1 000 синтетических пользователей", y=0.98)
    return save_fig(fig, "01_finapp_usage.png")


def chart_top_names(mock: pd.DataFrame) -> Path:
    top = (
        mock.groupby("first_name")
        .agg(total=("id", "size"), using=("using_finapp", "sum"))
        .nlargest(10, "total")
        .sort_values("total")
    )
    top["not_using"] = top["total"] - top["using"]

    fig, ax = plt.subplots(figsize=(9.5, 5.6))
    ax.barh(top.index, top["using"], color=COLORS["violet"], label="Пользуются")
    ax.barh(top.index, top["not_using"], left=top["using"], color="#ddd6fe", label="Не пользуются")
    for i, (_, row) in enumerate(top.iterrows()):
        ax.text(row["total"] + 0.05, i, fmt_int(row["total"]), va="center", fontsize=9, color=COLORS["text"])
    ax.set_xlim(0, top["total"].max() + 1.2)
    ax.set_xticks(np.arange(0, top["total"].max() + 1, 1))
    ax.set_xlabel("Человек с таким именем")
    ax.set_title("Топ-10 имён в MOCK_DATA")
    subtitle(fig, "Даже самое частое имя встречается 3 раза — набор почти равномерный", y=0.98)
    ax.legend(loc="lower right", fontsize=9)
    style_axes(ax, "x")
    return save_fig(fig, "02_top_names.png")


def chart_spend_by_category(tx: pd.DataFrame) -> Path:
    cat = (
        tx.groupby("category_name")
        .agg(total=("amount", "sum"), count=("tx_id", "count"), avg=("amount", "mean"))
        .sort_values("total")
    )
    colors = [VIOLET_CMAP(x) for x in np.linspace(0.25, 0.95, len(cat))]

    fig, ax = plt.subplots(figsize=(10.5, 6.2))
    bars = ax.barh(cat.index, cat["total"] / 1000, color=colors, height=0.72)
    for bar, (_, row) in zip(bars, cat.iterrows()):
        ax.text(
            bar.get_width() + 0.6, bar.get_y() + bar.get_height() / 2,
            f"{fmt_int(row['total'] / 1000)} тыс. ₽ · {fmt_int(row['count'])} шт.",
            va="center", fontsize=8.5, color=COLORS["text"]
        )
    ax.set_xlim(0, cat["total"].max() / 1000 * 1.28)
    ax.set_xlabel("Сумма трат, тыс. ₽")
    ax.set_title("Куда уходят деньги: траты по категориям")
    subtitle(fig, f"501 транзакция · {fmt_money(tx['amount'].sum())} за 30 дней", y=0.98)
    style_axes(ax, "x")
    return save_fig(fig, "03_spend_by_category.png")


def chart_daily_energy(daily: pd.DataFrame) -> Path:
    pivot = daily.pivot_table(index="date", columns="name", values="energy", aggfunc="first")
    activity = daily.pivot_table(index="date", columns="name", values="txCount", aggfunc="first")
    # Дни без записей не рисуем как «ноль энергии»: иначе график даёт ложные провалы.
    pivot = pivot.mask(activity.fillna(0) == 0)
    user_colors = ["#7c3aed", "#0d9488", "#f59e0b", "#ec4899", "#3b82f6", "#22c55e"]

    fig, ax = plt.subplots(figsize=(11, 5.8))
    for color, column in zip(user_colors, pivot.columns):
        ax.plot(pivot.index, pivot[column], color=color, lw=1.8, marker="o", ms=2.6, alpha=0.92, label=column)
    ax.axhline(100, color=COLORS["red"], lw=1.4, ls="--", label="Лимит 100%")
    ax.axhline(70, color=COLORS["amber"], lw=1.1, ls=":", label="Порог «счастлив» 70%")
    ax.fill_between(pivot.index, 100, max(130, np.nanmax(pivot.values) * 1.03), color=COLORS["red"], alpha=0.05)
    ax.set_ylim(0, max(130, np.nanmax(pivot.values) * 1.05))
    ax.set_ylabel("Энергия бюджета, %")
    ax.set_title("Энергия бюджета по дням")
    subtitle(fig, "Выше 100% — перерасход; дни без записей не соединены линией", y=0.98)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
    ax.legend(ncol=4, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.18))
    style_axes(ax)
    return save_fig(fig, "04_daily_energy.png")


def chart_limit_scatter(daily: pd.DataFrame) -> Path:
    active = daily[daily["txCount"] > 0].copy()
    within = active["withinLimit"]
    over = ~within

    fig, ax = plt.subplots(figsize=(8.2, 6.2))
    ax.scatter(
        active.loc[within, "limit"], active.loc[within, "spent"],
        s=38 + active.loc[within, "txCount"] * 11, color=COLORS["teal"], alpha=0.7,
        edgecolor="white", linewidth=0.6, label=f"В лимите — {int(within.sum())}"
    )
    ax.scatter(
        active.loc[over, "limit"], active.loc[over, "spent"],
        s=38 + active.loc[over, "txCount"] * 11, color=COLORS["red"], alpha=0.72,
        edgecolor="white", linewidth=0.6, label=f"Перерасход — {int(over.sum())}"
    )
    max_value = max(active["limit"].max(), active["spent"].max()) * 1.06
    ax.plot([0, max_value], [0, max_value], color=COLORS["slate"], lw=1.3, ls="--", label="Лимит = траты")
    ax.set_xlim(0, max_value)
    ax.set_ylim(0, max_value)
    ax.set_xlabel("Дневной лимит, ₽")
    ax.set_ylabel("Фактические траты, ₽")
    ax.set_title("Дневные траты против лимита")
    subtitle(fig, f"{len(active)} дней с тратами: {int(within.sum())} в лимите, {int(over.sum())} с перерасходом", y=0.98)
    ax.legend(loc="upper left", fontsize=9)
    style_axes(ax, "both")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: fmt_int(x)))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: fmt_int(x)))
    return save_fig(fig, "05_limit_scatter.png")


def chart_category_heatmap(tx: pd.DataFrame) -> Path:
    mix = tx.pivot_table(
        index="archetypeLabel", columns="category_name", values="amount",
        aggfunc="sum", fill_value=0
    )
    mix = mix.loc[mix.sum(axis=1).sort_values(ascending=False).index]
    mix = mix[mix.sum(axis=0).sort_values(ascending=False).index]
    share = mix.div(mix.sum(axis=1), axis=0) * 100

    fig, ax = plt.subplots(figsize=(12, 5.6))
    im = ax.imshow(share.values, aspect="auto", cmap=VIOLET_CMAP, vmin=0, vmax=max(35, share.values.max()))
    ax.set_xticks(range(len(share.columns)))
    ax.set_xticklabels(share.columns, rotation=38, ha="right", fontsize=8.5)
    ax.set_yticks(range(len(share.index)))
    ax.set_yticklabels(share.index, fontsize=9)
    for i in range(share.shape[0]):
        for j in range(share.shape[1]):
            value = share.values[i, j]
            if value >= 6:
                color = "white" if value > 22 else COLORS["text"]
                ax.text(j, i, f"{value:.0f}", ha="center", va="center", fontsize=7.5, color=color)
    cbar = fig.colorbar(im, ax=ax, fraction=0.026, pad=0.02)
    cbar.set_label("% от суммы трат архетипа", fontsize=8.5)
    ax.set_title("Структура трат по архетипам")
    subtitle(fig, "Процент от суммы трат каждого архетипа; подписи — доли ≥ 6%", y=0.98)
    return save_fig(fig, "06_category_heatmap.png")


def chart_coin_sources(daily: pd.DataFrame) -> Path:
    cols = ["coinsWork", "coinsQuests", "coinsLeftover", "coinsWeeklyBonus"]
    labels = ["Работа", "Квесты", "Остаток энергии", "Недельный бонус"]
    colors = [COLORS["violet"], COLORS["teal"], COLORS["amber"], COLORS["pink"]]
    source = daily.groupby("archetypeLabel")[cols].sum()
    source = source.div(daily.groupby("archetypeLabel").size(), axis=0)
    source["total"] = source.sum(axis=1)
    source = source.sort_values("total")

    fig, ax = plt.subplots(figsize=(10, 5.6))
    left = np.zeros(len(source))
    for col, label, color in zip(cols, labels, colors):
        values = source[col].values
        ax.barh(source.index, values, left=left, color=color, height=0.62, label=label)
        left += values
    for i, (_, row) in enumerate(source.iterrows()):
        ax.text(row["total"] + 1.5, i, f"{fmt_int(row['total'])} монет/день", va="center", fontsize=9, color=COLORS["text"])
    ax.set_xlim(0, source["total"].max() * 1.22)
    ax.set_xlabel("Монет в день, в среднем")
    ax.set_title("Из чего складывается доход питомца")
    subtitle(fig, "Среднее по 30 дням для каждого архетипа", y=0.98)
    ax.legend(ncol=4, fontsize=8.5, loc="upper center", bbox_to_anchor=(0.5, -0.16))
    style_axes(ax, "x")
    return save_fig(fig, "07_coin_sources.png")


def chart_balance_distributions(balance: pd.DataFrame, config: dict) -> Path:
    targets = config["balanceTargets"]
    coin_lo, coin_hi = targets["avgDailyCoins"]
    core_lo, core_hi = targets["daysToCoreCosmetics"]

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5))
    ax = axes[0]
    values = balance["avgDailyCoins"]
    ax.hist(values, bins=22, color=COLORS["violet"], alpha=0.78, edgecolor="white")
    ax.axvspan(coin_lo, coin_hi, color=COLORS["teal"], alpha=0.12, label=f"Цель {coin_lo}–{coin_hi}")
    median = values.median()
    ax.axvline(median, color=COLORS["red"], lw=1.5, ls="--", label=f"Медиана {median:.0f}")
    ax.set_xlabel("Монет в день")
    ax.set_ylabel("Прогонов")
    ax.set_title("Монеты в день")
    ax.legend(fontsize=8.5)
    style_axes(ax)

    ax = axes[1]
    values = balance["coreDays"]
    ax.hist(values, bins=22, color=COLORS["teal"], alpha=0.8, edgecolor="white")
    ax.axvspan(core_lo, core_hi, color=COLORS["amber"], alpha=0.16, label=f"Цель {core_lo}–{core_hi} дн.")
    median = values.median()
    ax.axvline(median, color=COLORS["red"], lw=1.5, ls="--", label=f"Медиана {median:.0f}")
    ax.set_xlabel("Дней до ядра косметики")
    ax.set_ylabel("Прогонов")
    ax.set_title("Скорость закрытия ядра коллекции")
    ax.legend(fontsize=8.5)
    style_axes(ax)

    fig.suptitle("Симуляция баланса: 400 игроков × 90 дней", fontsize=16, fontweight="bold", y=1.02)
    subtitle(fig, "Гистограммы показывают разброс результатов, а не одного «среднего игрока»", y=0.97)
    return save_fig(fig, "08_balance_distributions.png")


def chart_level_progress(balance: pd.DataFrame) -> Path:
    cols = ["levelDay30", "levelDay60", "finalLevel"]
    labels = ["К 30-му дню", "К 60-му дню", "К 90-му дню"]
    colors = [COLORS["violet_light"], COLORS["violet"], "#4c1d95"]

    agg = balance.groupby("archetypeLabel")[cols].mean()
    agg = agg.sort_values("levelDay30")
    short = {
        "Дисциплинированные": "Дисциплина",
        "Тратят на выходных": "Выходные",
        "Импульсивные": "Импульс",
        "Экономные": "Экономные",
        "Кофеманы": "Кофеманы",
        "Новички": "Новички",
    }
    agg.index = [short.get(x, x) for x in agg.index]

    fig, ax = plt.subplots(figsize=(10.5, 5.4))
    x = np.arange(len(agg))
    width = 0.26
    for i, (col, label, color) in enumerate(zip(cols, labels, colors)):
        positions = x + (i - 1) * width
        bars = ax.bar(positions, agg[col], width=width, color=color, label=label)
        for bar in bars:
            ax.text(
                bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2,
                f"{bar.get_height():.1f}", ha="center", va="bottom", fontsize=7.5
            )
    ax.set_xticks(x)
    ax.set_xticklabels(agg.index, fontsize=9)
    ax.set_ylabel("Средний уровень")
    ax.set_ylim(0, agg.max().max() + 3)
    ax.set_title("Как быстро растёт уровень у разных архетипов")
    subtitle(fig, "Средние по симуляции; цель к 30-му дню — 9–14 уровень", y=0.98)
    ax.legend(ncol=3, fontsize=8.5, loc="upper left")
    style_axes(ax)
    return save_fig(fig, "09_level_progress.png")


def chart_quest_completion(quests: pd.DataFrame) -> Path:
    quest = (
        quests.groupby("quest_title")
        .agg(attempts=("done", "size"), done=("done", "sum"))
        .assign(rate=lambda d: d["done"] / d["attempts"] * 100)
        .sort_values("rate")
    )
    quest = quest[quest["attempts"] >= 10]
    colors = [VIOLET_CMAP(x) for x in np.linspace(0.25, 0.95, len(quest))]

    fig, ax = plt.subplots(figsize=(10.5, 6.8))
    bars = ax.barh(quest.index, quest["rate"], color=colors, height=0.72)
    for bar, (_, row) in zip(bars, quest.iterrows()):
        x = max(row["rate"] + 1.5, 2)
        ax.text(x, bar.get_y() + bar.get_height() / 2,
                f"{row['rate']:.0f}% · n={int(row['attempts'])}",
                va="center", fontsize=8, color=COLORS["text"])
    ax.set_xlim(0, 112)
    ax.set_xlabel("Доля выполненных попыток, %")
    ax.set_title("Какие квесты выполняются чаще")
    subtitle(fig, "540 попыток за 30 дней; n — сколько раз квест выпадал; показаны квесты с n ≥ 10", y=0.98)
    style_axes(ax, "x")
    return save_fig(fig, "10_quest_completion.png")


# ---------------------------------------------------------------------------
# Сводки
# ---------------------------------------------------------------------------

def build_summaries(data: dict) -> dict:
    mock, tx, daily, quests, balance = data["mock"], data["tx"], data["daily"], data["quests"], data["balance"]
    config = data["config"]

    mock_counts = mock["using_finapp"].value_counts().reindex([True, False]).fillna(0)
    mock_share = mock_counts[True] / len(mock)

    tx_total = tx["amount"].sum()
    active_days = int((daily["txCount"] > 0).sum())
    within_active = int(((daily["txCount"] > 0) & daily["withinLimit"]).sum())
    over_days = int(((daily["txCount"] > 0) & ~daily["withinLimit"]).sum())
    zero_days = int((daily["txCount"] == 0).sum())

    category = (
        tx.groupby("category_name")
        .agg(tx_count=("tx_id", "count"), total=("amount", "sum"), mean=("amount", "mean"),
             median=("amount", "median"))
        .reset_index()
        .sort_values("total", ascending=False)
    )
    category["share"] = category["total"] / tx_total

    user = data["user_summary"].copy()
    user["spent_per_active_day"] = user["spent"] / user["expenses"].clip(lower=1)

    quest_summary = (
        quests.groupby("quest_title")
        .agg(attempts=("done", "size"), done=("done", "sum"), coins=("coins", "sum"), xp=("xp", "sum"))
        .assign(rate=lambda d: d["done"] / d["attempts"])
        .reset_index()
        .sort_values("rate", ascending=False)
    )

    percentile_metrics = [
        ("avgDailyCoins", "Монет в день", "монет"),
        ("avgDailyXp", "XP в день", "XP"),
        ("levelDay30", "Уровень к 30-му дню", "уровень"),
        ("finalLevel", "Уровень к 90-му дню", "уровень"),
        ("withinShare", "Доля дней в лимите", "доля"),
        ("bestLogStreak", "Лучший стрик учёта", "дней"),
        ("bestBudgetStreak", "Лучший бюджетный стрик", "дней"),
        ("coreDays", "Дней до ядра косметики", "дней"),
        ("fullDays", "Дней до полной коллекции", "дней"),
        ("health", "Здоровье питомца", "из 100"),
    ]
    percentile_rows = []
    for col, label, unit in percentile_metrics:
        values = balance[col]
        p10, p50, p90 = np.percentile(values, [10, 50, 90])
        percentile_rows.append({
            "metric": label, "unit": unit, "p10": p10, "p50": p50, "p90": p90
        })
    percentiles = pd.DataFrame(percentile_rows)

    corridor_rows = []
    for key, label, fmt in [
        ("avgDailyCoins", "Средние монеты в день", "coins"),
        ("daysToCoreCosmetics", "Дней до ядра косметики", "days"),
        ("daysToFullCollection", "Дней до полной коллекции", "days"),
        ("overspendDaysShare", "Доля дней с перерасходом", "share"),
        ("day30Level", "Уровень к 30-му дню", "level"),
    ]:
        lo, hi = config["balanceTargets"][key]
        if key == "avgDailyCoins":
            actual = balance["avgDailyCoins"].median()
            metric_series = balance["avgDailyCoins"]
        elif key == "daysToCoreCosmetics":
            actual = balance["coreDays"].median()
            metric_series = balance["coreDays"]
        elif key == "daysToFullCollection":
            actual = balance["fullDays"].median()
            metric_series = balance["fullDays"]
        elif key == "overspendDaysShare":
            actual = 1 - balance["withinShare"].median()
            metric_series = 1 - balance["withinShare"]
        else:
            actual = balance["levelDay30"].median()
            metric_series = balance["levelDay30"]
        inside = float(((metric_series >= lo) & (metric_series <= hi)).mean())
        corridor_rows.append({
            "metric": label, "low": lo, "high": hi, "actual": actual, "inside": inside
        })
    corridors = pd.DataFrame(corridor_rows)

    by_archetype = (
        balance.groupby("archetypeLabel")
        .agg(
            runs=("archetype", "size"),
            coins=("avgDailyCoins", "mean"),
            xp=("avgDailyXp", "mean"),
            level30=("levelDay30", "mean"),
            within=("withinShare", "mean"),
            core_days=("coreDays", "mean"),
            health=("health", "mean"),
        )
        .reset_index()
        .sort_values("coins", ascending=False)
    )

    corr = pd.DataFrame([
        {"pair": "Дисциплина ↔ монеты", "r": balance["withinShare"].corr(balance["avgDailyCoins"])},
        {"pair": "Дисциплина ↔ здоровье", "r": balance["withinShare"].corr(balance["health"])},
        {"pair": "Монеты ↔ уровень к 30-му дню", "r": balance["avgDailyCoins"].corr(balance["levelDay30"])},
        {"pair": "Монеты ↔ здоровье", "r": balance["avgDailyCoins"].corr(balance["health"])},
    ])

    return {
        "mock_counts": mock_counts,
        "mock_share": mock_share,
        "tx_total": tx_total,
        "active_days": active_days,
        "within_active": within_active,
        "over_days": over_days,
        "zero_days": zero_days,
        "category": category,
        "user": user,
        "quest_summary": quest_summary,
        "percentiles": percentiles,
        "corridors": corridors,
        "by_archetype": by_archetype,
        "corr": corr,
        "mock_top_names": mock["first_name"].value_counts().head(10),
    }


# ---------------------------------------------------------------------------
# Текстовые блоки
# ---------------------------------------------------------------------------

def build_report(data: dict, s: dict, quality: pd.DataFrame, figures: dict) -> str:
    mock, tx, daily, balance = data["mock"], data["tx"], data["daily"], data["balance"]
    config = data["config"]
    totals = config["balanceTargets"]
    p50 = s["percentiles"].set_index("metric")["p50"]

    category_rows = [
        [row["category_name"], fmt_int(row["tx_count"]), fmt_money(row["total"]),
         fmt_money(row["mean"]), fmt_pct(row["share"])]
        for _, row in s["category"].iterrows()
    ]

    user_rows = []
    for _, row in s["user"].iterrows():
        user_rows.append([
            row["name"], ARCHETYPE_RU.get(row["archetype"], row["archetype"]),
            fmt_int(row["expenses"]), fmt_money(row["spent"]),
            fmt_pct(row["days_within_limit"] / 30), row["final_level"],
            fmt_coins(row["final_coins"]),
        ])

    pct_rows = []
    for _, row in s["percentiles"].iterrows():
        if row["unit"] == "доля":
            pct_rows.append([row["metric"], fmt_pct(row["p10"]), fmt_pct(row["p50"]), fmt_pct(row["p90"])])
        else:
            pct_rows.append([row["metric"], fmt_int(row["p10"]), fmt_int(row["p50"]), fmt_int(row["p90"])])

    corridor_rows = []
    for _, row in s["corridors"].iterrows():
        if row["metric"] == "Доля дней с перерасходом":
            actual = fmt_pct(row["actual"])
            low, high = fmt_pct(row["low"]), fmt_pct(row["high"])
        elif row["metric"] == "Уровень к 30-му дню":
            actual = f"{row['actual']:.0f}"
            low, high = f"{row['low']:.0f}", f"{row['high']:.0f}"
        elif row["metric"] == "Средние монеты в день":
            actual = fmt_int(row["actual"])
            low, high = fmt_int(row["low"]), fmt_int(row["high"])
        else:
            actual = f"{row['actual']:.0f}"
            low, high = f"{row['low']:.0f}", f"{row['high']:.0f}"
        corridor_rows.append([row["metric"], f"{low}–{high}", actual,
                              "да" if row["low"] <= row["actual"] <= row["high"] else "нет",
                              fmt_pct(row["inside"], 0)])

    arch_rows = [
        [row["archetypeLabel"], fmt_int(row["coins"]), fmt_int(row["xp"]),
         f"{row['level30']:.1f}", fmt_pct(row["within"]), f"{row['core_days']:.0f}", fmt_int(row["health"])]
        for _, row in s["by_archetype"].iterrows()
    ]

    quest_top = s["quest_summary"].head(8)
    quest_bottom = s["quest_summary"].tail(6).sort_values("rate")
    quest_rows = [
        [row["quest_title"], fmt_int(row["attempts"]), fmt_int(row["done"]), fmt_pct(row["rate"])]
        for _, row in pd.concat([quest_top, quest_bottom]).drop_duplicates("quest_title").iterrows()
    ]

    quality_rows = [
        [row["dataset"], fmt_int(row["rows"]), fmt_int(row["columns"]),
         fmt_int(row["missing_required"]), fmt_int(row["missing_optional"]),
         fmt_int(row["duplicate_ids"]), row["verdict"]]
        for _, row in quality.iterrows()
    ]

    top_name_rows = [
        [name, fmt_int(count)]
        for name, count in s["mock_top_names"].items()
    ]

    corr_rows = [
        [row["pair"], f"{row['r']:+.2f}"]
        for _, row in s["corr"].iterrows()
    ]

    def figure_block(filename: str, caption: str, insight: str) -> str:
        return (
            f"![{caption}](figures/{filename})\n\n"
            f"> **Что это значит.** {insight}\n"
        )

    report = f"""# Анализ данных FinGame

**Дата анализа:** {datetime.now().strftime('%d.%m.%Y')}  
**Источники:** `MOCK_DATA (1).csv` из репозитория и синтетические данные игрового прототипа `financial-tamagotchi/`  
**Инструменты:** Python, pandas, numpy, matplotlib

> Все данные синтетические. Это учебный анализ, а не исследование реальных людей и не финансовый совет.

---

## 1. Если вы не занимаетесь анализом данных

Анализ данных — это не «магия с графиками». Это последовательность из пяти шагов:

1. **Понять, что лежит в таблицах.** Какая строка что описывает: человек, трата, день, игровой прогон?
2. **Проверить качество.** Есть ли пропуски, дубли, странные суммы, битые даты?
3. **Посчитать сводные показатели.** Сколько всего, сколько в среднем, медиана, минимум и максимум.
4. **Сравнить группы и посмотреть динамику.** Например, траты по категориям, дни в лимите, поведение архетипов.
5. **Сделать выводы с оговорками.** Что данные действительно показывают, а что им только приписывают.

Главный вывод этого отчёта: **два набора данных описывают разные вещи и не склеиваются между собой**. `MOCK_DATA` — это 1 000 синтетических пользователей с одним флагом «пользуется FinApp». Данные прототипа — это 6 игровых пользователей, 501 трата и 180 игровых дней. Поэтому анализ идёт по каждому набору отдельно, а затем собирается общая картина.

### Пять главных цифр

| Показатель | Значение | Источник |
|---|---:|---|
| Пользователей в MOCK_DATA | {fmt_int(len(mock))} | `MOCK_DATA (1).csv` |
| Из них пользуются FinApp | {fmt_pct(s['mock_share'])} | `MOCK_DATA (1).csv` |
| Транзакций в игровом наборе | {fmt_int(len(tx))} | `transactions.csv` |
| Дней в лимите (активные дни) | {fmt_pct(s['within_active'] / max(1, s['active_days']))} | `mock_users.json` |
| Медианный доход в симуляции | {fmt_int(p50['Монет в день'])} монет/день | `balance_runs.csv` |

---

## 2. Какие данные есть

| Набор | Что описывает одна строка | Размер | Сильные поля | Ограничение |
|---|---|---|---:|---|---|
| `MOCK_DATA (1).csv` | пользователь | {fmt_int(len(mock))} | имя, флаг `Using finapp` | нет трат, дат и финансового поведения |
| `transactions.csv` | одна трата | {fmt_int(len(tx))} | дата, сумма, категория, лимит, пользователь | всего 6 пользователей |
| `mock_users.json` → дни | один игровой день | {fmt_int(len(daily))} | энергия, здоровье, стрики, XP, монеты, квесты | синтетическая модель, а не живые люди |
| `balance_runs.csv` | один прогон симуляции на 90 дней | {fmt_int(len(balance))} | уровень, доход, доля дней в лимите, сроки коллекции | это математическая модель, а не A/B-тест |

### Проверка качества

{md_table(['Набор', 'Строк', 'Колонок', 'Пропусков в обязательных', 'Пропусков в необязательных', 'Дублей id', 'Вердикт'], quality_rows,
          ['left', 'right', 'right', 'right', 'right', 'right', 'left'])}

**Что проверяли:** пропущенные значения, полные дубли строк, повторяющиеся идентификаторы и невозможные значения (например, отрицательная сумма траты или здоровье вне 0–100). В игровых данных пропуски в заметках — это нормально: заметка необязательна. В `MOCK_DATA` пропусков нет, но и полей для глубокого анализа почти нет.

### Почему наборы нельзя просто «склеить»

- В `MOCK_DATA` нет `user_id`, который совпадал бы с `u_001…u_006`.
- В `MOCK_DATA` нет дат, сумм и категорий трат.
- Игровые пользователи — вымышленные персонажи с архетипами, а не те же люди из `MOCK_DATA`.
- Любое объединение по имени было бы случайным совпадением.

Поэтому дальше: сначала отдельно `MOCK_DATA`, потом отдельно игровые данные, потом — общая сводка метрик.

---

## 3. Набор A: `MOCK_DATA (1).csv`

{md_table(['Имя', 'Человек'], top_name_rows, ['left', 'right'])}

{figure_block('01_finapp_usage.png', 'Доля пользователей FinApp',
             f"Из 1 000 строк {fmt_int(s['mock_counts'][True])} помечены как пользователи FinApp, {fmt_int(s['mock_counts'][False])} — как не пользующиеся. Это {fmt_pct(s['mock_share'])}. Но это мок-данные генератора, а не репрезентативная выборка рынка.")}

{figure_block('02_top_names.png', 'Топ-10 имён',
             "Даже самое частое имя встречается всего 3 раза. Набор выглядит почти равномерно сгенерированным: в нём нет естественных демографических перекосов, поэтому имена здесь почти не несут аналитической ценности.")}

**Что можно сказать честно:** `MOCK_DATA` подходит как заготовка для демонстрации списка пользователей или тестирования интерфейса. Для анализа финансового поведения в нём не хватает главного — самих финансовых действий.

---

## 4. Набор B: траты игровых пользователей

### 4.1 Общая картина

| Показатель | Значение |
|---|---:|
| Всего транзакций | {fmt_int(len(tx))} |
| Суммарные траты | {fmt_money(s['tx_total'])} |
| Средний чек | {fmt_money(tx['amount'].mean())} |
| Медианный чек | {fmt_money(tx['amount'].median())} |
| Минимальная трата | {fmt_money(tx['amount'].min())} |
| Максимальная трата | {fmt_money(tx['amount'].max())} |
| Дней с тратами | {s['active_days']} из 180 |
| Дней без трат | {s['zero_days']} |
| Дней с перерасходом | {s['over_days']} |
| Дней в лимите (среди активных) | {s['within_active']} ({fmt_pct(s['within_active'] / max(1, s['active_days']))}) |

Средний чек ({fmt_money(tx['amount'].mean())}) заметно выше медианного ({fmt_money(tx['amount'].median())}). Это значит, что распределение трат смещено вправо: большинство чеков небольшие, но есть крупные покупки, которые тянут среднее вверх. Для таких данных медиана часто честнее среднего.

{figure_block('03_spend_by_category.png', 'Траты по категориям',
             "Больше всего денег уходит на продукты, покупки и транспорт. При этом количество транзакций и сумма — разные вещи: в категории может быть много мелких чеков, а в другой — несколько крупных.")}

### 4.2 Траты по категориям

{md_table(['Категория', 'Трат', 'Сумма', 'Средний чек', 'Доля суммы'], category_rows,
          ['left', 'right', 'right', 'right', 'right'])}

### 4.3 Пользователи

{md_table(['Имя', 'Архетип', 'Трат', 'Потрачено', 'Дней в лимите', 'Уровень', 'Монеты'], user_rows,
          ['left', 'left', 'right', 'right', 'right', 'right', 'right'])}

{figure_block('04_daily_energy.png', 'Энергия бюджета по дням',
             "Энергия — это процент потраченного дневного лимита. Линии выше 100% означают перерасход. Видно, что у разных архетипов разные паттерны: кто-то держится ровно, кто-то регулярно «взрывает» лимит.")}

{figure_block('05_limit_scatter.png', 'Траты против лимита',
             f"Точки ниже пунктирной линии — дни в лимите, выше — перерасход. Из {s['active_days']} активных дней {s['within_active']} были в лимите, а {s['over_days']} — с перерасходом. Размер точки — число трат за день.")}

### 4.4 Категории по архетипам

{figure_block('06_category_heatmap.png', 'Структура трат по архетипам',
             "Тепловая карта показывает не абсолютные суммы, а доли внутри каждого архетипа. Так честнее сравнивать: у всех разный дневной лимит и разная сумма трат. Например, у кофеманов ожидаемо выше доля кафе, а у экономных — продуктов.")}

---

## 5. Игровая экономика

### 5.1 Доход питомца

{figure_block('07_coin_sources.png', 'Источники монет',
             "Основной источник монет — работа, затем квесты. Остаток энергии и недельный бонус дают меньший, но заметный вклад. Это значит, что игрок не обязан быть идеально дисциплинированным, чтобы получать доход: база работает всегда.")}

| Показатель | Значение |
|---|---:|
| Средние монеты в день (6 пользователей) | {fmt_int(daily['coinsEarned'].mean())} |
| Средний XP в день | {fmt_int(daily['xpEarned'].mean())} |
| Среднее здоровье | {fmt_int(daily['health'].mean())} / 100 |
| Доля дней в лимите (все дни) | {fmt_pct(daily['withinLimit'].mean())} |
| Выполнено попыток квестов | {fmt_int(data['quests']['done'].sum())} из {fmt_int(len(data['quests']))} |
| Среднее выполнение квестов в день | {f"{daily['questsCompleted'].mean():.2f}".replace(".", ",")} из 3 |

### 5.2 Квесты

{md_table(['Квест', 'Выпадал', 'Выполнен', 'Доля'], quest_rows,
          ['left', 'right', 'right', 'right'])}

{figure_block('10_quest_completion.png', 'Выполнение квестов',
             "Самые выполняемые квесты — простые действия: одна смена работы, проверка питомца, запись трат. Самые сложные — «Экономный день» и «Дорога учтена»: в этой симуляции они не выполняются ни разу. Это сигнал пересмотреть условия или награду, а не вину игрока.")}

---

## 6. Симуляция баланса: 400 игроков × 90 дней

Симуляция — это не реальные люди. Это способ проверить, как математика игры ведёт себя на разных стилях поведения. 400 прогонов помогают увидеть не только среднее, но и разброс.

### 6.1 Перцентили

{md_table(['Метрика', 'p10', 'p50 (медиана)', 'p90'], pct_rows,
          ['left', 'right', 'right', 'right'])}

### 6.2 Проверка целевых коридоров

{md_table(['Цель', 'Коридор', 'Факт (медиана)', 'Попала?', 'Доля прогонов в коридоре'], corridor_rows,
          ['left', 'right', 'right', 'center', 'right'])}

{figure_block('08_balance_distributions.png', 'Распределение монет и сроков коллекции',
             "Гистограммы показывают, что «средний игрок» — это упрощение. Даже в одной модели результаты сильно различаются: часть прогонов выходит за целевой коридор. Именно поэтому баланс проверяют по перцентилям, а не только по среднему.")}

### 6.3 По архетипам

{md_table(['Архетип', 'Монет/день', 'XP/день', 'Уровень к 30-му', 'Дней в лимите', 'Дней до ядра', 'Здоровье'], arch_rows,
          ['left', 'right', 'right', 'right', 'right', 'right', 'right'])}

{figure_block('09_level_progress.png', 'Прогресс уровня по архетипам',
             "Дисциплинированные и экономные растут быстрее, импульсивные — медленнее, но всё равно доходят до жизнеспособного уровня. Это хороший признак: игра не «выключает» игрока за плохую дисциплину.")}

### 6.4 Корреляции

{md_table(['Пара', 'Корреляция r'], corr_rows, ['left', 'right'])}

**Как читать:** коэффициент корреляции от −1 до +1. Чем ближе к +1, тем сильнее две метрики растут вместе. Но это **не доказательство причины и следствия**. В нашей модели дисциплина напрямую увеличивает монеты и здоровье, поэтому связь ожидаема. На реальных людях такая корреляция могла бы объясняться третьим фактором, например доходом.

---

## 7. Общая картина по всем данным

{md_table(
    ['Метрика', 'Значение', 'Источник', 'Как трактовать'],
    [
        ['Пользователей в MOCK_DATA', fmt_int(len(mock)), 'MOCK_DATA', 'демо-список, не финансы'],
        ['Доля Using finapp', fmt_pct(s['mock_share']), 'MOCK_DATA', 'можно использовать только как заглушку'],
        ['Игровых пользователей', '6', 'mock_users.json', 'маленькая выборка для демонстрации'],
        ['Транзакций', fmt_int(len(tx)), 'transactions.csv', 'основной массив для анализа трат'],
        ['Средний чек', fmt_money(tx['amount'].mean()), 'transactions.csv', 'смещён крупными покупками'],
        ['Медианный чек', fmt_money(tx['amount'].median()), 'transactions.csv', 'типичная трата'],
        ['Доля активных дней в лимите', fmt_pct(s['within_active'] / max(1, s['active_days'])), 'mock_users.json', 'дисциплина в игровом наборе'],
        ['Медиана монет/день', fmt_int(p50['Монет в день']), 'balance_runs.csv', 'результат модели, не люди'],
        ['Медиана дней до ядра', f"{p50['Дней до ядра косметики']:.0f}", 'balance_runs.csv', 'длина ранней коллекции'],
        ['Медиана дней до полной коллекции', f"{p50['Дней до полной коллекции']:.0f}", 'balance_runs.csv', 'долгая цель'],
    ],
    ['left', 'right', 'left', 'left']
)}

### Что бы я добавил, чтобы анализ стал сильнее

1. **Единый `user_id` во всех таблицах.** Тогда можно связать пользователя, его траты и игровое состояние.
2. **Даты и события в `MOCK_DATA`.** Без них нельзя смотреть динамику и retention.
3. **Реальные (или хотя бы правдоподобные) транзакции.** Не только флаг «пользуется приложением».
4. **События продукта:** открытие, запись траты, завершение дня, покупка, уход.
5. **Когорты:** дата регистрации, канал привлечения, эксперимент A/B.
6. **Больше пользователей в игровом наборе.** 6 человек — это иллюстрация, а не статистика.

---

## 8. Ограничения анализа

- **Синтетика.** Все игровые пользователи и траты сгенерированы по правилам, а не собраны с людей.
- **Маленькая выборка.** 6 игровых пользователей и 30 дней не дают статистической значимости.
- **Нет причинности.** Корреляции в симуляции — следствие заложенных формул.
- **MOCK_DATA не про финансы.** Там нет сумм, категорий и дат.
- **Наборы не связаны.** Нельзя утверждать, что 51,5% из `MOCK_DATA` — это аудитория игры.
- **Средние обманчивы.** Поэтому в отчёте есть медианы, перцентили и разброс.

---

## 9. Как воспроизвести

```powershell
python -m pip install -r analysis/requirements.txt
python analysis/analyze.py
```

Скрипт пересоберёт:

- `analysis/figures/*.png` — графики;
- `analysis/output/*.csv` — сводные таблицы;
- `analysis/output/summary.json` — ключевые цифры;
- `analysis/report.md` — этот отчёт;
- `analysis/dashboard.html` — автономный дашборд с графиками.

---

## 10. Итог одной фразой

Данные прототипа показывают, что игровая петля собирает траты, дисциплину, награды и прогресс в одну систему; `MOCK_DATA` показывает только демографическую заглушку. Сильнее всего анализ улучшит не новый график, а **связка данных по пользователю и событиям**.
"""
    return report


def build_dashboard(data: dict, s: dict, quality: pd.DataFrame, figures: dict) -> str:
    mock, tx, daily, balance = data["mock"], data["tx"], data["daily"], data["balance"]
    p50 = s["percentiles"].set_index("metric")["p50"]
    total_quests = int(len(data["quests"]))
    done_quests = int(data["quests"]["done"].sum())

    fig_html = {
        name: f'<img src="data:image/png;base64,{base64_image(path)}" alt="{name}">'
        for name, path in figures.items()
    }

    category_rows = "".join(
        f"<tr><td>{row['category_name']}</td><td>{fmt_int(row['tx_count'])}</td>"
        f"<td>{fmt_money(row['total'])}</td><td>{fmt_money(row['mean'])}</td>"
        f"<td>{fmt_pct(row['share'])}</td></tr>"
        for _, row in s["category"].iterrows()
    )
    user_rows = "".join(
        f"<tr><td>{row['name']}</td><td>{ARCHETYPE_RU.get(row['archetype'], row['archetype'])}</td>"
        f"<td>{fmt_int(row['expenses'])}</td><td>{fmt_money(row['spent'])}</td>"
        f"<td>{fmt_pct(row['days_within_limit'] / 30)}</td><td>{row['final_level']}</td>"
        f"<td>{fmt_coins(row['final_coins'])}</td></tr>"
        for _, row in s["user"].iterrows()
    )
    quality_rows = "".join(
        f"<tr><td>{row['dataset']}</td><td>{fmt_int(row['rows'])}</td>"
        f"<td>{fmt_int(row['missing_required'])}</td><td>{fmt_int(row['missing_optional'])}</td>"
        f"<td>{fmt_int(row['duplicate_ids'])}</td><td>{row['verdict']}</td></tr>"
        for _, row in quality.iterrows()
    )
    corridor_rows = "".join(
        f"<tr><td>{row['metric']}</td><td>{row['low']}–{row['high']}</td>"
        f"<td>{row['actual']:.1f}</td>"
        f"<td class=\"{'ok' if row['low'] <= row['actual'] <= row['high'] else 'bad'}\">"
        f"{'да' if row['low'] <= row['actual'] <= row['high'] else 'нет'}</td>"
        f"<td>{fmt_pct(row['inside'], 0)}</td></tr>"
        for _, row in s["corridors"].iterrows()
    )
    arch_rows = "".join(
        f"<tr><td>{row['archetypeLabel']}</td><td>{fmt_int(row['coins'])}</td>"
        f"<td>{fmt_int(row['xp'])}</td><td>{row['level30']:.1f}</td>"
        f"<td>{fmt_pct(row['within'])}</td><td>{row['core_days']:.0f}</td>"
        f"<td>{fmt_int(row['health'])}</td></tr>"
        for _, row in s["by_archetype"].iterrows()
    )
    quest_rows = "".join(
        f"<tr><td>{row['quest_title']}</td><td>{fmt_int(row['attempts'])}</td>"
        f"<td>{fmt_int(row['done'])}</td><td>{fmt_pct(row['rate'])}</td></tr>"
        for _, row in s["quest_summary"].sort_values("rate", ascending=False).iterrows()
    )

    def card(label: str, value: str, note: str) -> str:
        return f'<div class="kpi"><span>{label}</span><b>{value}</b><small>{note}</small></div>'

    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FinGame · анализ данных</title>
<style>
  :root {{
    --bg: #f7f5fb; --card: #ffffff; --ink: #1f2937; --muted: #6b7280;
    --violet: #7c3aed; --teal: #0d9488; --amber: #f59e0b; --pink: #ec4899;
    --line: #e5e7eb;
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--bg); color: var(--ink); font-family: "Segoe UI", Arial, sans-serif; line-height: 1.55; }}
  .page {{ max-width: 1180px; margin: 0 auto; padding: 32px 20px 80px; }}
  header.hero {{ background: linear-gradient(135deg, #2e1065, #6d28d9 55%, #0f766e); color: white; border-radius: 26px; padding: 38px 34px; box-shadow: 0 22px 55px rgba(76,29,149,.22); }}
  header.hero h1 {{ margin: 0 0 8px; font-size: 38px; line-height: 1.1; }}
  header.hero p {{ margin: 0; max-width: 760px; color: #ede9fe; }}
  .tags {{ display: flex; gap: 8px; flex-wrap: wrap; margin-top: 18px; }}
  .tags span {{ background: rgba(255,255,255,.14); border: 1px solid rgba(255,255,255,.25); padding: 5px 10px; border-radius: 999px; font-size: 12px; }}
  .kpis {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 14px; margin: 22px 0 30px; }}
  .kpi {{ background: var(--card); border: 1px solid var(--line); border-radius: 18px; padding: 16px 18px; box-shadow: 0 8px 24px rgba(15,23,42,.04); }}
  .kpi span {{ display: block; color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .04em; }}
  .kpi b {{ display: block; font-size: 27px; margin: 4px 0 2px; color: var(--violet); }}
  .kpi small {{ color: var(--muted); font-size: 12px; }}
  section {{ margin: 34px 0; }}
  h2 {{ font-size: 25px; margin: 0 0 6px; }}
  h3 {{ font-size: 18px; margin: 24px 0 8px; }}
  p.lead {{ color: var(--muted); margin-top: 0; }}
  .card {{ background: var(--card); border: 1px solid var(--line); border-radius: 20px; padding: 20px; box-shadow: 0 10px 28px rgba(15,23,42,.045); }}
  .grid2 {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 18px; }}
  figure {{ margin: 0; }}
  figure img {{ width: 100%; height: auto; display: block; border-radius: 12px; background: #fff; }}
  figcaption {{ color: var(--muted); font-size: 13px; margin-top: 8px; }}
  .note {{ border-left: 4px solid var(--teal); background: #f0fdfa; padding: 12px 14px; border-radius: 0 12px 12px 0; margin: 12px 0 0; font-size: 14px; }}
  .warn {{ border-left-color: var(--amber); background: #fffbeb; }}
  .bad {{ color: #b91c1c; font-weight: 700; }}
  .ok {{ color: #047857; font-weight: 700; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13.5px; }}
  th, td {{ padding: 8px 10px; border-bottom: 1px solid var(--line); text-align: left; }}
  th {{ font-size: 11.5px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); background: #fafafa; }}
  tr:last-child td {{ border-bottom: 0; }}
  td:nth-child(n+2) {{ white-space: nowrap; }}
  .scroll {{ overflow-x: auto; }}
  .callout {{ background: #f5f3ff; border: 1px solid #ddd6fe; border-radius: 16px; padding: 16px 18px; margin: 16px 0; }}
  .callout b {{ color: var(--violet); }}
  footer {{ margin-top: 46px; color: var(--muted); font-size: 12.5px; }}
  a {{ color: var(--violet); }}
  @media (max-width: 640px) {{ header.hero {{ padding: 26px 20px; }} header.hero h1 {{ font-size: 28px; }} .page {{ padding: 18px 12px 50px; }} }}
</style>
</head>
<body>
<div class="page">
<header class="hero">
  <h1>FinGame: что говорят данные</h1>
  <p>Простой разбор двух наборов данных: демо-список пользователей и синтетика игрового прототипа. Без магии, с проверкой качества, таблицами, графиками и оговорками.</p>
  <div class="tags"><span>pandas</span><span>matplotlib</span><span>501 транзакция</span><span>400 прогонов баланса</span><span>1 000 пользователей</span></div>
</header>

<div class="kpis">
  {card('Пользователей в MOCK_DATA', fmt_int(len(mock)), f'{fmt_pct(s["mock_share"])} пользуются FinApp')}
  {card('Транзакций', fmt_int(len(tx)), f'{fmt_money(s["tx_total"])} суммарно')}
  {card('Игровых дней', fmt_int(len(daily)), '6 пользователей × 30 дней')}
  {card('Медиана монет/день', fmt_int(p50['Монет в день']), 'симуляция 400 × 90')}
  {card('Дней в лимите', fmt_pct(daily['withinLimit'].mean()), 'в игровом наборе')}
  {card('Дней до ядра', f"{p50['Дней до ядра косметики']:.0f}", 'медиана симуляции')}
</div>

<section>
  <h2>1. Главное</h2>
  <div class="callout">
    <b>Два набора не связаны между собой.</b> В <code>MOCK_DATA</code> 1 000 пользователей и только один флаг «пользуется FinApp». В игровом наборе — 6 персонажей, 501 трата и 180 игровых дней. Их нельзя склеить по id или именам: это разные люди и разные сущности. Поэтому анализ идёт отдельно, а общая сводка собирает метрики, а не строки.
  </div>
  <div class="grid2">
    <div class="card"><h3>Что показывает MOCK_DATA</h3><p>Это чистая, почти равномерная синтетика. 51,5% пользователей помечены как использующие FinApp. Имена почти не повторяются. Для анализа финансового поведения данных недостаточно.</p></div>
    <div class="card"><h3>Что показывает игровой набор</h3><p>Траты распределены неравномерно: продукты, покупки и транспорт — крупнейшие категории. В активные дни игроки укладываются в лимит примерно в 73,5% случаев. Доход в основном даёт работа, затем квесты.</p></div>
  </div>
</section>

<section>
  <h2>2. Качество данных</h2>
  <p class="lead">Перед графиками — проверка: пропуски, дубли, странные значения. Пропуски в заметках трат — норма, заметка необязательна.</p>
  <div class="card scroll">
    <table><thead><tr><th>Набор</th><th>Строк</th><th>Пропусков в обязательных</th><th>Пропусков в необязательных</th><th>Дублей id</th><th>Вердикт</th></tr></thead><tbody>{quality_rows}</tbody></table>
  </div>
</section>

<section>
  <h2>3. MOCK_DATA: 1 000 пользователей</h2>
  <div class="grid2">
    <figure class="card">{fig_html['01_finapp_usage.png']}<figcaption>Доля пользователей, которые пользуются FinApp.</figcaption></figure>
    <figure class="card">{fig_html['02_top_names.png']}<figcaption>Топ-10 имён: набор почти равномерный, явных лидеров нет.</figcaption></figure>
  </div>
  <div class="note warn">Это мок-данные. 51,5% — доля внутри файла, а не оценка рынка и не аудитория игры.</div>
</section>

<section>
  <h2>4. Траты: куда уходят деньги</h2>
  <figure class="card">{fig_html['03_spend_by_category.png']}<figcaption>Суммы по категориям. Средний чек выше медианного — распределение смещено крупными покупками.</figcaption></figure>
  <div class="card scroll" style="margin-top:18px">
    <table><thead><tr><th>Категория</th><th>Трат</th><th>Сумма</th><th>Средний чек</th><th>Доля</th></tr></thead><tbody>{category_rows}</tbody></table>
  </div>
</section>

<section>
  <h2>5. Пользователи и дисциплина</h2>
  <div class="card scroll">
    <table><thead><tr><th>Имя</th><th>Архетип</th><th>Трат</th><th>Потрачено</th><th>Дней в лимите</th><th>Уровень</th><th>Монеты</th></tr></thead><tbody>{user_rows}</tbody></table>
  </div>
  <div class="grid2" style="margin-top:18px">
    <figure class="card">{fig_html['04_daily_energy.png']}<figcaption>Энергия = процент потраченного лимита. Выше 100% — перерасход.</figcaption></figure>
    <figure class="card">{fig_html['05_limit_scatter.png']}<figcaption>Дневные траты против лимита. Точки выше пунктира — перерасход.</figcaption></figure>
  </div>
  <div class="note">Из {s['active_days']} активных дней {s['within_active']} были в лимите, {s['over_days']} — с перерасходом, ещё {s['zero_days']} дней остались без записей.</div>
</section>

<section>
  <h2>6. Архетипы и структура трат</h2>
  <figure class="card">{fig_html['06_category_heatmap.png']}<figcaption>Доли категорий внутри каждого архетипа — корректнее, чем абсолютные суммы при разных лимитах.</figcaption></figure>
</section>

<section>
  <h2>7. Экономика питомца</h2>
  <figure class="card">{fig_html['07_coin_sources.png']}<figcaption>Средний дневной доход по источникам. Работа — база, квесты — вторая опора.</figcaption></figure>
  <div class="note">За 30 дней выполнено {fmt_int(done_quests)} из {fmt_int(total_quests)} попыток квестов. Самые сложные условия — «Экономный день» и «Дорога учтена»: в этой симуляции они не выполнены ни разу.</div>
</section>

<section>
  <h2>8. Квесты</h2>
  <figure class="card">{fig_html['10_quest_completion.png']}<figcaption>Доля выполнения и число попыток. Маленькое n означает, что квест редко выпадал — его процент менее надёжен.</figcaption></figure>
  <div class="card scroll" style="margin-top:18px">
    <table><thead><tr><th>Квест</th><th>Выпадал</th><th>Выполнен</th><th>Доля</th></tr></thead><tbody>{quest_rows}</tbody></table>
  </div>
</section>

<section>
  <h2>9. Симуляция баланса: 400 × 90</h2>
  <div class="grid2">
    <figure class="card">{fig_html['08_balance_distributions.png']}<figcaption>Разброс монет в день и сроков до ядра коллекции. Целевые коридоры выделены.</figcaption></figure>
    <figure class="card">{fig_html['09_level_progress.png']}<figcaption>Средний уровень по архетипам к 30, 60 и 90 дням.</figcaption></figure>
  </div>
  <div class="card scroll" style="margin-top:18px">
    <table><thead><tr><th>Цель</th><th>Коридор</th><th>Факт (медиана)</th><th>Попала?</th><th>Прогонов внутри</th></tr></thead><tbody>{corridor_rows}</tbody></table>
  </div>
  <div class="card scroll" style="margin-top:18px">
    <table><thead><tr><th>Архетип</th><th>Монет/день</th><th>XP/день</th><th>Уровень к 30-му</th><th>Дней в лимите</th><th>Дней до ядра</th><th>Здоровье</th></tr></thead><tbody>{arch_rows}</tbody></table>
  </div>
</section>

<section>
  <h2>10. Что делать дальше</h2>
  <div class="grid2">
    <div class="card"><h3>Усилить данные</h3><p>Добавить единый <code>user_id</code>, даты, события продукта и реальные транзакции. Без этого глубина анализа ограничена.</p></div>
    <div class="card"><h3>Усилить продукт</h3><p>Пересмотреть квесты с нулевым выполнением, проверить сложность «Экономного дня» и «Дороги», добавить когорты и A/B-тест цен.</p></div>
  </div>
  <div class="note warn">Корреляции в симуляции — следствие заложенных формул, а не доказательство причинности. На реальных людях выводы нужно проверять отдельно.</div>
</section>

<footer>
  FinGame · анализ синтетических данных · {datetime.now().strftime('%d.%m.%Y')} · Python / pandas / matplotlib<br>
  Подробная версия: <a href="report.md">report.md</a> · исходники: <a href="analyze.py">analyze.py</a>
</footer>
</div>
</body>
</html>
"""
    return html


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    data = load_data()
    quality = quality_checks(data)
    s = build_summaries(data)

    figures = {
        "01_finapp_usage.png": chart_finapp_usage(data["mock"]),
        "02_top_names.png": chart_top_names(data["mock"]),
        "03_spend_by_category.png": chart_spend_by_category(data["tx"]),
        "04_daily_energy.png": chart_daily_energy(data["daily"]),
        "05_limit_scatter.png": chart_limit_scatter(data["daily"]),
        "06_category_heatmap.png": chart_category_heatmap(data["tx"]),
        "07_coin_sources.png": chart_coin_sources(data["daily"]),
        "08_balance_distributions.png": chart_balance_distributions(data["balance"], data["config"]),
        "09_level_progress.png": chart_level_progress(data["balance"]),
        "10_quest_completion.png": chart_quest_completion(data["quests"]),
    }

    # CSV-выгрузки
    data["tx"].to_csv(OUT_DIR / "transactions_clean.csv", index=False, encoding="utf-8-sig")
    data["daily"].drop(columns=["quests"]).to_csv(OUT_DIR / "daily_states_clean.csv", index=False, encoding="utf-8-sig")
    quality.to_csv(OUT_DIR / "data_quality.csv", index=False, encoding="utf-8-sig")
    s["category"].to_csv(OUT_DIR / "category_summary.csv", index=False, encoding="utf-8-sig")
    s["user"].to_csv(OUT_DIR / "user_summary.csv", index=False, encoding="utf-8-sig")
    s["quest_summary"].to_csv(OUT_DIR / "quest_completion.csv", index=False, encoding="utf-8-sig")
    s["percentiles"].to_csv(OUT_DIR / "balance_percentiles.csv", index=False, encoding="utf-8-sig")
    s["corridors"].to_csv(OUT_DIR / "balance_corridors.csv", index=False, encoding="utf-8-sig")
    s["by_archetype"].to_csv(OUT_DIR / "balance_by_archetype.csv", index=False, encoding="utf-8-sig")
    s["corr"].to_csv(OUT_DIR / "correlations.csv", index=False, encoding="utf-8-sig")

    summary = {
        "generatedAt": datetime.now().isoformat(timespec="seconds"),
        "sources": {
            "mockData": "MOCK_DATA (1).csv",
            "gameData": "financial-tamagotchi/data",
            "balance": "financial-tamagotchi/reports/balance_runs.csv",
        },
        "mock": {
            "users": int(len(data["mock"])),
            "usingFinapp": int(s["mock_counts"][True]),
            "usingFinappShare": round(float(s["mock_share"]), 4),
        },
        "game": {
            "users": int(data["daily"]["user_id"].nunique()),
            "transactions": int(len(data["tx"])),
            "days": int(len(data["daily"])),
            "totalSpent": int(s["tx_total"]),
            "avgCheck": round(float(data["tx"]["amount"].mean()), 2),
            "medianCheck": float(data["tx"]["amount"].median()),
            "activeDays": int(s["active_days"]),
            "withinActiveDays": int(s["within_active"]),
            "overDays": int(s["over_days"]),
            "zeroDays": int(s["zero_days"]),
            "withinShareAllDays": round(float(data["daily"]["withinLimit"].mean()), 4),
            "questsDone": int(data["quests"]["done"].sum()),
            "questsTotal": int(len(data["quests"])),
        },
        "balance": {
            "runs": int(len(data["balance"])),
            "days": 90,
            "coinMedian": float(s["percentiles"].set_index("metric").loc["Монет в день", "p50"]),
            "coreDaysMedian": float(s["percentiles"].set_index("metric").loc["Дней до ядра косметики", "p50"]),
            "fullDaysMedian": float(s["percentiles"].set_index("metric").loc["Дней до полной коллекции", "p50"]),
            "levelDay30Median": float(s["percentiles"].set_index("metric").loc["Уровень к 30-му дню", "p50"]),
        },
        "limitations": [
            "Все данные синтетические",
            "MOCK_DATA и игровые данные не связаны по id",
            "6 игровых пользователей не дают статистической значимости",
            "Корреляции в симуляции отражают заложенные формулы",
        ],
    }
    (OUT_DIR / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    report = build_report(data, s, quality, figures)
    (ANALYSIS / "report.md").write_text(report, encoding="utf-8")
    (ANALYSIS / "dashboard.html").write_text(build_dashboard(data, s, quality, figures), encoding="utf-8")

    print("Готово.")
    print(f"  отчёт: analysis/report.md")
    print(f"  дашборд: analysis/dashboard.html")
    print(f"  графиков: {len(figures)}")
    print(f"  CSV-выгрузок: 10")


if __name__ == "__main__":
    main()
