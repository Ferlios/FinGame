"""
Монте-Карло симулятор баланса. Запуск: python tools/simulate_balance.py

Прогоняет 400 синтетических игроков по 90 дней и проверяет,
попадает ли экономика в целевые коридоры из game_config.json.
"""

from __future__ import annotations

import csv
import json
import random
import statistics
from datetime import date, timedelta
from pathlib import Path

from content import (
    ACHIEVEMENTS,
    ARCHETYPES,
    CATEGORIES,
    PETS,
    QUESTS,
    SHOP_ITEMS,
    generate_raw_days,
)
from game_model import CONFIG, LEVELS, replay_user, total_xp_for_level

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
REPORTS = ROOT / "reports"
RUNS = 400
DAYS = 90
END_DATE = date(2026, 11, 6)
START_DATE = END_DATE - timedelta(days=DAYS - 1)

ARCHETYPE_MIX = [
    ("disciplined", 0.25),
    ("coffee_addict", 0.16),
    ("impulse_buyer", 0.15),
    ("weekend_spender", 0.15),
    ("newbie", 0.14),
    ("frugal_saver", 0.15),
]


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = (len(ordered) - 1) * p / 100
    lo, hi = int(idx), min(int(idx) + 1, len(ordered) - 1)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (idx - lo)


def median(values: list[float]) -> float:
    return statistics.median(values) if values else 0.0


def day_when(cumulative: list[float], threshold: float) -> int | None:
    total = 0.0
    for i, value in enumerate(cumulative, start=1):
        total += value
        if total >= threshold:
            return i
    return None


def main() -> None:
    rng = random.Random(777001)
    non_consumable = [i for i in SHOP_ITEMS if not i.get("consumable")]
    core_price = sum(i["price"] for i in non_consumable if i["category"] in {"hat", "furniture"})
    full_price = sum(i["price"] for i in non_consumable) + sum(p["price"] for p in PETS)

    runs = []
    for i in range(RUNS):
        arch_name = rng.choices(
            [a for a, _ in ARCHETYPE_MIX], weights=[w for _, w in ARCHETYPE_MIX], k=1
        )[0]
        arch = ARCHETYPES[arch_name]
        level = rng.randint(1, 12)
        profile = {
            **arch,
            "id": f"sim_{i:04d}",
            "archetype": arch_name,
            "dailyLimit": rng.choice([1000, 1200, 1500, 1800, 2000, 2500, 3000]),
            "startLevel": level,
            "startTotalXp": total_xp_for_level(level)
            + int(LEVELS[level - 1]["xpToNext"] * rng.uniform(0, 0.6)),
            "startCoins": rng.randint(0, 900),
            "startHealth": rng.randint(50, 100),
            "startLogStreak": rng.randint(0, 10),
            "startBudgetStreak": rng.randint(0, 6),
            "startPurchases": rng.randint(0, 3),
            "startOwnedItems": rng.randint(0, 3),
            "periodPurchases": 0,
        }
        raw_days = generate_raw_days(profile, START_DATE, DAYS, rng)
        result = replay_user(profile, raw_days, rng, QUESTS, ACHIEVEMENTS)
        days = result["days"]
        active_days = [d for d in days if d["txCount"] > 0]
        daily_coins = [d["coinsEarned"] for d in days]
        runs.append(
            {
                "archetype": arch_name,
                "limit": profile["dailyLimit"],
                "avgDailyCoins": result["totals"]["avgDailyCoins"],
                "avgDailyXp": result["totals"]["avgDailyXp"],
                "finalLevel": result["state"]["level"],
                "levelDay30": days[29]["level"] if len(days) > 29 else result["state"]["level"],
                "levelDay60": days[59]["level"] if len(days) > 59 else result["state"]["level"],
                "withinShare": len([d for d in active_days if d["withinLimit"]]) / max(1, len(active_days)),
                "bestLogStreak": result["state"]["bestLogStreak"],
                "bestBudgetStreak": result["state"]["bestBudgetStreak"],
                "finalCoins": result["state"]["coins"],
                "coinsEarned": result["totals"]["coinsEarned"],
                "coreDays": core_price / max(1.0, result["totals"]["avgDailyCoins"]),
                "fullDays": full_price / max(1.0, result["totals"]["avgDailyCoins"]),
                "dayTo500": day_when(daily_coins, 500),
                "dayTo1500": day_when(daily_coins, 1500),
                "dayTo3000": day_when(daily_coins, 3000),
                "dayTo6000": day_when(daily_coins, 6000),
                "health": result["state"]["health"],
            }
        )

    metrics = {
        "avgDailyCoins": [r["avgDailyCoins"] for r in runs],
        "avgDailyXp": [r["avgDailyXp"] for r in runs],
        "levelDay30": [r["levelDay30"] for r in runs],
        "finalLevel": [r["finalLevel"] for r in runs],
        "withinShare": [r["withinShare"] for r in runs],
        "bestLogStreak": [r["bestLogStreak"] for r in runs],
        "bestBudgetStreak": [r["bestBudgetStreak"] for r in runs],
        "coreDays": [r["coreDays"] for r in runs],
        "fullDays": [r["fullDays"] for r in runs],
        "health": [r["health"] for r in runs],
    }

    def p_table(key: str, label: str, fmt: str = "{:.0f}") -> str:
        vals = metrics[key]
        return (
            f"| {label} | {fmt.format(percentile(vals, 10))} | {fmt.format(percentile(vals, 50))} "
            f"| {fmt.format(percentile(vals, 90))} |"
        )

    def median_day(key: str) -> str:
        vals = [r[key] for r in runs if r[key] is not None]
        return f"{median(vals):.0f}" if vals else "—"

    # --- отчёт ---
    targets = CONFIG["balanceTargets"]
    lines: list[str] = []
    lines.append("# Отчёт по балансу экономики")
    lines.append("")
    lines.append(f"Симуляция: **{RUNS} игроков × {DAYS} дней**, старт {START_DATE.isoformat()}, финиш {END_DATE.isoformat()}.")
    lines.append("")
    lines.append("Смесь архетипов: 25% дисциплинированные, по 15–16% остальные. Дневной лимит 1 000–3 000 ₽.")
    lines.append("")
    lines.append("## 1. Ключевые метрики (перцентили p10 / p50 / p90)")
    lines.append("")
    lines.append("| Метрика | p10 | p50 | p90 |")
    lines.append("|---|---:|---:|---:|")
    lines.append(p_table("avgDailyCoins", "Монет в день"))
    lines.append(p_table("avgDailyXp", "XP в день"))
    lines.append(p_table("levelDay30", "Уровень к 30-му дню"))
    lines.append(p_table("finalLevel", "Уровень к 90-му дню"))
    lines.append(p_table("withinShare", "Дней в пределах лимита", "{:.0%}"))
    lines.append(p_table("bestLogStreak", "Лучший стрик учёта"))
    lines.append(p_table("bestBudgetStreak", "Лучший стрик без перерасхода"))
    lines.append(p_table("health", "Здоровье питомца"))
    lines.append("")
    lines.append("## 2. Экономика магазина")
    lines.append("")
    lines.append(f"Стоимость «ядра» косметики (шляпы + мебель): **{core_price:,} монет**.".replace(",", " "))
    lines.append(f"Стоимость полной коллекции (все предметы + питомцы): **{full_price:,} монет**.".replace(",", " "))
    lines.append("")
    lines.append("| Сколько дней копить | p10 | p50 | p90 |")
    lines.append("|---|---:|---:|---:|")
    lines.append(p_table("coreDays", "Дней до ядра косметики"))
    lines.append(p_table("fullDays", "Дней до полной коллекции"))
    lines.append("")
    lines.append("## 3. Вехи прогресса (медиана по симуляции)")
    lines.append("")
    lines.append("| Веха | Медианный день |")
    lines.append("|---|---:|")
    lines.append(f"| Заработать 500 монет | {median_day('dayTo500')} |")
    lines.append(f"| Заработать 1 500 монет | {median_day('dayTo1500')} |")
    lines.append(f"| Заработать 3 000 монет (легендарный питомец) | {median_day('dayTo3000')} |")
    lines.append(f"| Заработать 6 000 монет | {median_day('dayTo6000')} |")
    lines.append("")
    lines.append("## 4. Проверка целевых коридоров")
    lines.append("")
    lines.append("| Цель | Коридор | Факт (p50) | Статус |")
    lines.append("|---|---:|---:|---|")

    checks = [
        ("Средние монеты в день", targets["avgDailyCoins"], median(metrics["avgDailyCoins"]), "{:.0f} монет"),
        ("Дней до ядра косметики", targets["daysToCoreCosmetics"], median(metrics["coreDays"]), "{:.0f} дней"),
        ("Дней до полной коллекции", targets["daysToFullCollection"], median(metrics["fullDays"]), "{:.0f} дней"),
        ("Доля дней с перерасходом", targets["overspendDaysShare"], 1 - median(metrics["withinShare"]), "{:.0%}"),
        ("Уровень к 30-му дню", targets["day30Level"], median(metrics["levelDay30"]), "{:.0f}"),
    ]
    for label, (lo, hi), value, fmt in checks:
        if lo <= value <= hi:
            status = "✅ в коридоре"
        elif value < lo:
            status = "🔽 ниже цели"
        else:
            status = "🔼 выше цели"
        lines.append(f"| {label} | {lo}–{hi} | {fmt.format(value)} | {status} |")

    lines.append("")
    lines.append("## 5. По архетипам")
    lines.append("")
    lines.append("| Архетип | Монет/день | XP/день | Уровень к дню 30 | Дней в лимите | Лучший стрик |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for arch_name, _ in ARCHETYPE_MIX:
        subset = [r for r in runs if r["archetype"] == arch_name]
        if not subset:
            continue
        lines.append(
            f"| {ARCHETYPES[arch_name]['label']} | {median([r['avgDailyCoins'] for r in subset]):.0f} "
            f"| {median([r['avgDailyXp'] for r in subset]):.0f} "
            f"| {median([r['levelDay30'] for r in subset]):.0f} "
            f"| {median([r['withinShare'] for r in subset]):.0%} "
            f"| {median([r['bestLogStreak'] for r in subset]):.0f} |"
        )

    lines.append("")
    lines.append("## 6. Выводы и что крутить")
    lines.append("")
    lines.append("- **Петля замыкается:** реальные траты дают XP и энергию, игра возвращает монеты за работу и квесты, монеты уходят в косметику. Ни одна валюта не висит без стока.")
    lines.append("- **Стрик — главный ускоритель.** Множитель до ×1.6 делает недельную дисциплину ощутимо выгоднее разовых рывков, но не блокирует новичка.")
    lines.append("- **Лимит трат не наказывает мгновенно.** Перерасход бьёт по настроению и здоровью питомца, а не отнимает уже заработанное. Это сохраняет мотивацию вернуться завтра.")
    lines.append("- **Основные ручки баланса:** `work.baseCoins`, `quests` награды, `streak.coinMultiplierPerDay`, цены легендарок. Если монеты капают слишком быстро — поднимайте цены на эпики, а не режьте базовую награду: базовый доход важен для ощущения прогресса.")
    lines.append("")
    lines.append("> Все цифры синтетические и предназначены для демонстрации дизайн-логики, а не для финансовых выводов.")
    lines.append("")

    (REPORTS / "balance_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  wrote reports/balance_report.md")

    with (REPORTS / "balance_runs.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(runs[0].keys()))
        writer.writeheader()
        writer.writerows(runs)
    print(f"  wrote reports/balance_runs.csv ({len(runs)} прогонов)")

    summary = {
        "runs": RUNS,
        "days": DAYS,
        "corePrice": core_price,
        "fullPrice": full_price,
        "p50": {k: round(percentile(v, 50), 2) for k, v in metrics.items()},
    }
    (REPORTS / "balance_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("  wrote reports/balance_summary.json")


if __name__ == "__main__":
    main()
