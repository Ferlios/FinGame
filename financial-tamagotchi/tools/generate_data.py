"""Генератор всех прототипных данных. Запуск: python tools/generate_data.py"""

from __future__ import annotations

import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

from content import (
    ACHIEVEMENTS,
    ARCHETYPES,
    CATEGORIES,
    PETS,
    QUESTS,
    SHOP_ITEMS,
    USERS,
    generate_raw_days,
)
from game_model import CONFIG, LEVELS, replay_user, total_xp_for_level

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
REPORTS = ROOT / "reports"
SEED = 20261106
END_DATE = date(2026, 11, 6)
DAYS = 30


def write_json(path: Path, payload) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"  wrote {path.relative_to(ROOT)}")


def main() -> None:
    DATA.mkdir(exist_ok=True)
    REPORTS.mkdir(exist_ok=True)
    rng = random.Random(SEED)

    write_json(DATA / "game_config.json", CONFIG)
    write_json(DATA / "levels.json", LEVELS)
    write_json(DATA / "categories.json", CATEGORIES)
    write_json(DATA / "pets.json", PETS)
    write_json(DATA / "shop_items.json", SHOP_ITEMS)
    write_json(DATA / "quests.json", QUESTS)
    write_json(DATA / "achievements.json", ACHIEVEMENTS)

    start = END_DATE - timedelta(days=DAYS - 1)

    users_out = []
    csv_rows = []
    summary_rows = []

    print("Генерирую мок-пользователей...")
    for user in USERS:
        level = user["startLevel"]
        xp_to_next = LEVELS[level - 1]["xpToNext"]
        profile = {
            **ARCHETYPES[user["archetype"]],
            **user,
            "startTotalXp": total_xp_for_level(level) + int(xp_to_next * rng.uniform(0.15, 0.7)),
        }
        raw_days = generate_raw_days(profile, start, DAYS, rng)
        result = replay_user(profile, raw_days, rng, QUESTS, ACHIEVEMENTS)

        transactions = []
        for day in raw_days:
            for j, tx in enumerate(day["transactions"], start=1):
                tx_id = f"tx_{user['id']}_{day['date'].strftime('%m%d')}_{j:02d}"
                cat = next(c for c in CATEGORIES if c["id"] == tx["categoryId"])
                row = {
                    "id": tx_id,
                    "userId": user["id"],
                    "date": day["date"].isoformat(),
                    "time": tx["time"],
                    "amount": tx["amount"],
                    "categoryId": tx["categoryId"],
                    "categoryName": cat["name"],
                    "note": tx["note"],
                    "limit": day["limit"],
                }
                transactions.append(row)
                csv_rows.append(
                    {
                        "user_id": user["id"],
                        "archetype": user["archetype"],
                        "tx_id": tx_id,
                        "date": row["date"],
                        "time": row["time"],
                        "amount": row["amount"],
                        "category_id": row["categoryId"],
                        "category_name": row["categoryName"],
                        "note": row["note"],
                        "daily_limit": day["limit"],
                    }
                )

        pet_id = "moss"
        for pet in PETS:
            if pet["price"] > 0 and user["startLevel"] >= pet["unlockLevel"]:
                pet_id = pet["id"]
        stage = 1
        for st in next(p for p in PETS if p["id"] == pet_id)["stages"]:
            if user["startLevel"] >= st["level"]:
                stage = st["stage"]

        last_day = result["days"][-1]
        quest_by_id = {q["id"]: q for q in QUESTS}
        quests_today = [
            {
                "id": q["id"],
                "title": quest_by_id[q["id"]]["title"],
                "description": quest_by_id[q["id"]]["description"],
                "icon": quest_by_id[q["id"]]["icon"],
                "done": q["done"],
                "coins": q["coins"],
                "xp": q["xp"],
            }
            for q in last_day["quests"]
        ]

        users_out.append(
            {
                "id": user["id"],
                "profile": {
                    "name": user["name"],
                    "avatar": user["avatar"],
                    "archetype": user["archetype"],
                    "archetypeLabel": ARCHETYPES[user["archetype"]]["label"],
                    "dailyLimit": user["dailyLimit"],
                    "monthlyIncome": user["income"],
                    "timezone": user["timezone"],
                },
                "pet": {"speciesId": pet_id, "stage": stage, "equipped": {"hat": "hat_beanie" if user["startLevel"] > 3 else None, "accessory": None, "theme": "theme_cozy", "furniture": ["furn_plant"]}},
                "initialState": {
                    "level": level,
                    "totalXp": profile["startTotalXp"],
                    "coins": user["startCoins"],
                    "health": user["startHealth"],
                    "logStreak": user["startLogStreak"],
                    "budgetStreak": user["startBudgetStreak"],
                },
                "state": result["state"],
                "totals": result["totals"],
                "days": result["days"],
                "transactions": transactions,
                "questsToday": quests_today,
            }
        )

        summary_rows.append(
            {
                "user_id": user["id"],
                "name": user["name"],
                "archetype": user["archetype"],
                "daily_limit": user["dailyLimit"],
                "expenses": result["totals"]["expenses"],
                "spent": result["totals"]["spent"],
                "avg_daily_spent": result["totals"]["avgDailySpent"],
                "days_within_limit": result["totals"]["daysWithinLimit"],
                "final_level": result["state"]["level"],
                "final_coins": result["state"]["coins"],
                "best_log_streak": result["state"]["bestLogStreak"],
                "best_budget_streak": result["state"]["bestBudgetStreak"],
                "avg_daily_coins": result["totals"]["avgDailyCoins"],
                "avg_daily_xp": result["totals"]["avgDailyXp"],
                "achievements": len(result["state"]["achievements"]),
            }
        )

    write_json(
        DATA / "mock_users.json",
        {
            "meta": {
                "seed": SEED,
                "days": DAYS,
                "startDate": start.isoformat(),
                "endDate": END_DATE.isoformat(),
                "users": len(users_out),
                "transactions": len(csv_rows),
                "note": "Синтетические данные, сгенерированы по правилам из game_config.json",
            },
            "users": users_out,
        },
    )

    with (DATA / "transactions.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys()))
        writer.writeheader()
        writer.writerows(csv_rows)
    print(f"  wrote data/transactions.csv ({len(csv_rows)} строк)")

    with (REPORTS / "mock_users_summary.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)
    print("  wrote reports/mock_users_summary.csv")

    print("\nГотово.")
    print(f"  пользователей: {len(users_out)}")
    print(f"  транзакций: {len(csv_rows)}")


if __name__ == "__main__":
    main()
