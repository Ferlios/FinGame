"""Проверка целостности сгенерированных данных. Запуск: python tools/validate_data.py"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

ERRORS: list[str] = []
WARNINGS: list[str] = []


def load(name: str):
    path = DATA / name
    if not path.exists():
        ERRORS.append(f"нет файла data/{name}")
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def check(condition: bool, message: str) -> None:
    if not condition:
        ERRORS.append(message)


def unique_ids(rows: list[dict], label: str) -> set[str]:
    ids = [row.get("id") for row in rows]
    check(len(ids) == len(set(ids)), f"{label}: повторяющиеся id")
    check(all(ids), f"{label}: пустой id")
    return set(ids)


def main() -> int:
    config = load("game_config.json")
    levels = load("levels.json")
    categories = load("categories.json")
    pets = load("pets.json")
    shop = load("shop_items.json")
    quests = load("quests.json")
    achievements = load("achievements.json")
    mock = load("mock_users.json")
    if any(x is None for x in (config, levels, categories, pets, shop, quests, achievements, mock)):
        return report()

    # --- config ---
    for section in ("meta", "energy", "xp", "streak", "work", "quests", "shop", "balanceTargets"):
        check(section in config, f"config: нет секции {section}")
    check(config["energy"]["defaultDailyLimit"] > 0, "config: дневной лимит должен быть > 0")
    check(config["xp"]["dailyLogCap"] > 0, "config: дневной кап XP должен быть > 0")
    check(config["work"]["minigameSeconds"] > 0, "config: длительность мини-игры должна быть > 0")

    # --- levels ---
    check(len(levels) == config["xp"]["levelCurve"]["maxLevel"], "levels: число уровней не совпадает с конфигом")
    for i, level in enumerate(levels, start=1):
        check(level["level"] == i, f"levels: уровень {i} нарушает порядок")
        if i < len(levels):
            check(level["xpToNext"] > 0, f"levels: на уровне {i} нет xpToNext")
        else:
            check(level["xpToNext"] == 0, "levels: максимальный уровень должен иметь xpToNext = 0")

    # --- categories ---
    cat_ids = unique_ids(categories, "categories")
    check(len(categories) == 12, f"categories: ожидалось 12, получено {len(categories)}")
    for cat in categories:
        check(bool(cat.get("name") and cat.get("icon") and cat.get("color")), f"categories: неполная карточка {cat.get('id')}")
        check(cat.get("typicalMin", 0) <= cat.get("typicalMax", 0), f"categories: перевёрнутый диапазон {cat.get('id')}")
    check("other" in cat_ids, "categories: нет запасной категории other")

    # --- pets ---
    pet_ids = unique_ids(pets, "pets")
    check(len(pets) == 6, f"pets: ожидалось 6, получено {len(pets)}")
    for pet in pets:
        stages = pet.get("stages") or []
        check(len(stages) >= 2, f"pets: у {pet['id']} меньше двух стадий")
        check([s["level"] for s in stages] == sorted(s["level"] for s in stages), f"pets: стадии {pet['id']} не по порядку")
        check(stages[0]["level"] == 1, f"pets: первая стадия {pet['id']} должна быть с 1 уровня")
        check(pet.get("price", 0) >= 0, f"pets: отрицательная цена {pet['id']}")

    # --- shop ---
    shop_ids = unique_ids(shop, "shop_items")
    allowed_slots = {"hat", "accessory", "theme", "furniture", "food"}
    allowed_rarity = {"common", "rare", "epic", "legendary"}
    for item in shop:
        item_id = item.get("id")
        check(item.get("slot") in allowed_slots, f"shop: неизвестный слот у {item_id}")
        check(item.get("rarity") in allowed_rarity, f"shop: неизвестная редкость у {item_id}")
        check(item.get("category") in allowed_slots, f"shop: категория не совпадает со слотом у {item_id}")
        check(isinstance(item.get("price"), int) and item["price"] >= 0, f"shop: цена {item_id}")
        check(1 <= item.get("unlockLevel", 0) <= len(levels), f"shop: уровень разблокировки {item_id}")
        if item.get("consumable"):
            check(item.get("slot") == "food", f"shop: расходник {item_id} должен быть едой")
            check(bool(item.get("effect", {}).get("health")), f"shop: у еды {item_id} нет эффекта здоровья")
    food = [i for i in shop if i.get("consumable")]
    check(len(food) >= 5, "shop: слишком мало еды")

    # --- quests ---
    quest_ids = unique_ids(quests, "quests")
    quest_types = {
        "log_count", "under_limit", "category_count", "note_count", "work_sessions",
        "avoid_category", "check_pet", "early_log", "weekly_review", "energy_left",
    }
    for quest in quests:
        cond = quest.get("condition", {})
        check(cond.get("type") in quest_types, f"quests: неизвестное условие у {quest.get('id')}")
        check(1 <= quest.get("minLevel", 0) <= len(levels), f"quests: minLevel у {quest.get('id')}")
        check(quest.get("weight", 0) > 0, f"quests: вес у {quest.get('id')}")
        check(quest.get("rewards", {}).get("coins", 0) > 0, f"quests: нет награды монетами у {quest.get('id')}")
        if cond.get("type") in {"log_count", "category_count", "note_count", "work_sessions", "energy_left"}:
            check(cond.get("target", 0) > 0, f"quests: нет target у {quest.get('id')}")
        if cond.get("type") in {"category_count", "avoid_category"}:
            check(cond.get("categoryId") in cat_ids, f"quests: неизвестная категория у {quest.get('id')}")

    # --- achievements ---
    ach_ids = unique_ids(achievements, "achievements")
    ach_types = {
        "expense_count", "total_spent", "log_streak", "budget_streak", "level",
        "purchases", "owned_items", "work_sessions", "quests_completed",
        "categories_used", "coins_earned", "energy_left_once", "no_category_streak", "comeback",
    }
    for ach in achievements:
        cond = ach.get("condition", {})
        check(cond.get("type") in ach_types, f"achievements: неизвестное условие у {ach.get('id')}")
        check(cond.get("target", 0) >= 1, f"achievements: нет target у {ach.get('id')}")
        check(ach.get("rewards", {}).get("coins", 0) >= 0, f"achievements: награда у {ach.get('id')}")
        if cond.get("type") == "no_category_streak":
            check(cond.get("categoryId") in cat_ids, f"achievements: категория у {ach.get('id')}")

    # --- mock users ---
    users = mock.get("users") or []
    check(len(users) == 6, f"mock_users: ожидалось 6 пользователей, получено {len(users)}")
    total_tx = 0
    for user in users:
        days = user.get("days") or []
        tx = user.get("transactions") or []
        check(len(days) == mock["meta"]["days"], f"mock_users: у {user.get('id')} неверное число дней")
        check(len(tx) > 0, f"mock_users: у {user.get('id')} нет транзакций")
        check(user.get("state", {}).get("level") == days[-1]["level"], f"mock_users: уровень {user.get('id')} не сходится с последним днём")
        check(user.get("pet", {}).get("speciesId") in pet_ids, f"mock_users: неизвестный питомец у {user.get('id')}")
        check(len(user.get("questsToday") or []) == config["quests"]["perDay"], f"mock_users: квесты дня у {user.get('id')}")
        total_tx += len(tx)
        for t in tx:
            check(t.get("categoryId") in cat_ids, f"mock_users: категория транзакции {t.get('id')}")
            check(t.get("amount", 0) > 0, f"mock_users: сумма транзакции {t.get('id')}")
    if (DATA / "transactions.csv").exists():
        with (DATA / "transactions.csv").open(encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        check(len(rows) == total_tx, f"transactions.csv: {len(rows)} строк против {total_tx} в mock_users")
        check(len(rows[0].keys()) == 10, "transactions.csv: ожидалось 10 колонок")
    else:
        ERRORS.append("нет файла data/transactions.csv")

    check(len(shop_ids) == 36, f"shop_items: ожидалось 36 предметов, получено {len(shop_ids)}")
    check(len(quest_ids) == 18, f"quests: ожидалось 18, получено {len(quest_ids)}")
    check(len(ach_ids) == 22, f"achievements: ожидалось 22, получено {len(ach_ids)}")
    check(len(pet_ids) == 6, "pets: ожидалось 6")

    print(f"Пользователей: {len(users)}")
    print(f"Транзакций: {total_tx}")
    print(f"Категорий: {len(categories)} · питомцев: {len(pets)} · товаров: {len(shop)}")
    print(f"Квестов: {len(quests)} · достижений: {len(achievements)}")
    return report()


def report() -> int:
    for warning in WARNINGS:
        print(f"WARN  {warning}")
    for error in ERRORS:
        print(f"ERROR {error}")
    if ERRORS:
        print(f"\nПровалено проверок: {len(ERRORS)}")
        return 1
    print("\nOK: данные согласованы.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
