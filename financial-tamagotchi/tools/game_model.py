"""
Единая модель правил «Финансового тамагочи».

Здесь живут все формулы: энергия, XP, уровни, стрики, монеты, квесты.
И генератор мок-данных, и симулятор баланса используют этот модуль,
поэтому цифры в прототипе и в отчётах всегда сходятся.
"""

from __future__ import annotations

import math
import random
from datetime import date, timedelta

CONFIG = {
    "meta": {
        "name": "Бюджетный питомец",
        "slug": "budget-buddy",
        "version": "0.1.0-prototype",
        "locale": "ru-RU",
        "currency": "RUB",
        "generatedFor": "портфолио / гейм-дизайн",
        "disclaimer": "Все данные синтетические. Совпадения с реальными людьми случайны.",
    },
    "energy": {
        "max": 100,
        "defaultDailyLimit": 1500,
        "happyMax": 70,
        "neutralMax": 100,
        "healthGainWithinLimit": 5,
        "healthRegenDaily": 2,
        "healthLossOverspendBase": 4,
        "healthLossOverspendPerPct": 0.15,
        "healthLossMax": 15,
        "healthStart": 80,
        "leftoverEnergyToCoins": 0.25,
        "moodLabels": {
            "happy": "Сыт и доволен",
            "neutral": "Слегка волнуется",
            "sad": "Грустит из-за перерасхода",
            "sick": "Приболел, нужно позаботиться",
        },
    },
    "xp": {
        "perExpense": 5,
        "categoryBonus": 2,
        "noteBonus": 3,
        "dailyLogCap": 45,
        "withinLimitBonus": 10,
        "workSessionXp": 4,
        "weeklyBonusXp": 120,
        "levelCurve": {"base": 40, "exponent": 1.15, "roundTo": 5, "maxLevel": 30},
    },
    "streak": {
        "coinMultiplierPerDay": 0.02,
        "maxMultiplier": 1.6,
        "freezeCost": 120,
        "maxFreezes": 2,
        "weeklyBonusCoins": 150,
        "weeklyBonusEvery": 7,
    },
    "work": {
        "sessionsPerDay": 3,
        "baseCoins": 12,
        "coinsPerLevel": 0.6,
        "perfectChance": 0.25,
        "perfectBonusCoins": 8,
        "cooldownSeconds": 30,
        "minigameSeconds": 5,
    },
    "quests": {
        "perDay": 3,
        "rerollCost": 40,
        "maxRerolls": 1,
    },
    "shop": {
        "sellRefundRatio": 0.35,
        "dailyFoodLimit": 3,
        "equipSlots": {"hat": 1, "accessory": 1, "theme": 1, "furniture": 3},
    },
    "balanceTargets": {
        "avgDailyCoins": [90, 160],
        "daysToCoreCosmetics": [18, 35],
        "daysToFullCollection": [90, 150],
        "overspendDaysShare": [0.15, 0.35],
        "day30Level": [9, 14],
    },
}

LEVEL_TITLES = {
    1: "Новичок",
    3: "Ученик",
    5: "Джуниор",
    8: "Хранитель бюджета",
    12: "Эконом-мастер",
    16: "Стратег",
    20: "Маг бюджета",
    25: "Легенда",
    30: "Гуру денег",
}

LEVEL_UNLOCKS = {
    2: ["Магазин косметики"],
    3: ["Ежедневные квесты"],
    5: ["Питомец «Плюша»"],
    8: ["Вторая стадия эволюции"],
    10: ["Питомец «Искра»"],
    12: ["Второй слот питомца"],
    14: ["Питомец «Кефир»"],
    18: ["Третья стадия эволюции", "Питомец «Бублик»"],
    24: ["Питомец «Драк»"],
    30: ["Легендарный скин «Космос»"],
}


def round_to(value: float, step: int) -> int:
    return int(step * round(value / step))


def build_levels() -> list[dict]:
    curve = CONFIG["xp"]["levelCurve"]
    levels: list[dict] = []
    for lvl in range(1, curve["maxLevel"] + 1):
        is_max = lvl == curve["maxLevel"]
        xp_to_next = 0 if is_max else round_to(
            curve["base"] * (lvl ** curve["exponent"]), curve["roundTo"]
        )
        title = LEVEL_TITLES.get(lvl)
        if title is None:
            title = next(
                LEVEL_TITLES[k] for k in sorted(LEVEL_TITLES, reverse=True) if k <= lvl
            )
        levels.append(
            {
                "level": lvl,
                "title": title,
                "xpToNext": xp_to_next,
                "unlocks": LEVEL_UNLOCKS.get(lvl, []),
            }
        )
    return levels


LEVELS = build_levels()


def total_xp_for_level(level: int) -> int:
    return sum(l["xpToNext"] for l in LEVELS if l["level"] < level)


def level_state(total_xp: int) -> dict:
    remaining = max(0, int(total_xp))
    for lvl in LEVELS:
        if lvl["level"] == len(LEVELS):
            return {
                "level": lvl["level"],
                "title": lvl["title"],
                "xpIntoLevel": 0,
                "xpToNext": 0,
                "progress": 1.0,
            }
        if remaining < lvl["xpToNext"]:
            return {
                "level": lvl["level"],
                "title": lvl["title"],
                "xpIntoLevel": remaining,
                "xpToNext": lvl["xpToNext"],
                "progress": round(remaining / lvl["xpToNext"], 3),
            }
        remaining -= lvl["xpToNext"]
    return {"level": 30, "title": "Гуру денег", "xpIntoLevel": 0, "xpToNext": 0, "progress": 1.0}


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def energy_used(spent: float, daily_limit: float) -> int:
    if daily_limit <= 0:
        return 999
    return int(round(spent / daily_limit * 100))


def mood_for(energy: int, health: int) -> str:
    if health < 25:
        return "sick"
    if energy <= CONFIG["energy"]["happyMax"]:
        return "happy"
    if energy <= CONFIG["energy"]["neutralMax"]:
        return "neutral"
    return "sad"


def streak_multiplier(log_streak: int) -> float:
    cfg = CONFIG["streak"]
    return round(min(cfg["maxMultiplier"], 1 + log_streak * cfg["coinMultiplierPerDay"]), 3)


def pick_quests(rng: random.Random, quests: list[dict], day: date, level: int) -> list[dict]:
    cfg = CONFIG["quests"]
    pool = [
        q
        for q in quests
        if q["minLevel"] <= level
        and not (q["condition"]["type"] == "weekly_review" and day.weekday() != 6)
    ]
    chosen: list[dict] = []
    used_types: set[str] = set()
    while pool and len(chosen) < cfg["perDay"]:
        weights = [
            q["weight"] * (0.25 if q["condition"]["type"] in used_types else 1.0)
            for q in pool
        ]
        quest = rng.choices(pool, weights=weights, k=1)[0]
        chosen.append(quest)
        used_types.add(quest["condition"]["type"])
        pool = [q for q in pool if q["id"] != quest["id"]]
    return chosen


def quest_is_complete(quest: dict, ctx: dict, rng: random.Random) -> bool:
    cond = quest["condition"]
    kind = cond["type"]
    target = cond.get("target", 1)
    if kind == "log_count":
        return ctx["txCount"] >= target
    if kind == "under_limit":
        return ctx["txCount"] > 0 and ctx["withinLimit"]
    if kind == "category_count":
        return ctx["catCounts"].get(cond["categoryId"], 0) >= target
    if kind == "note_count":
        return ctx["noteCount"] >= target
    if kind == "work_sessions":
        return ctx["workSessions"] >= target
    if kind == "avoid_category":
        return ctx["txCount"] > 0 and ctx["catCounts"].get(cond["categoryId"], 0) == 0
    if kind == "check_pet":
        return ctx["engaged"] and rng.random() < 0.9
    if kind == "early_log":
        return ctx["earlyLog"] and rng.random() < 0.85
    if kind == "weekly_review":
        return ctx["weekday"] == 6 and rng.random() < 0.8
    if kind == "energy_left":
        return ctx["energy"] <= target
    return False


def achievement_unlocked(cond: dict, state: dict, totals: dict, days: list[dict]) -> bool:
    kind = cond["type"]
    target = cond.get("target", 1)
    if kind == "expense_count":
        return totals["expenses"] >= target
    if kind == "total_spent":
        return totals["spent"] >= target
    if kind == "log_streak":
        return state["bestLogStreak"] >= target
    if kind == "budget_streak":
        return state["bestBudgetStreak"] >= target
    if kind == "level":
        return level_state(state["totalXp"])["level"] >= target
    if kind == "purchases":
        return totals["purchases"] >= target
    if kind == "owned_items":
        return totals["ownedItems"] >= target
    if kind == "work_sessions":
        return totals["workSessions"] >= target
    if kind == "quests_completed":
        return totals["questsCompleted"] >= target
    if kind == "categories_used":
        return len(totals["categoriesUsed"]) >= target
    if kind == "coins_earned":
        return totals["coinsEarned"] >= target
    if kind == "energy_left_once":
        return any(d["txCount"] > 0 and d["energy"] <= target for d in days)
    if kind == "no_category_streak":
        best = cur = 0
        for d in days:
            if d["txCount"] > 0 and d["catCounts"].get(cond["categoryId"], 0) == 0:
                cur += 1
                best = max(best, cur)
            else:
                cur = 0
        return best >= target
    if kind == "comeback":
        return any(d["gapDays"] >= 3 and d["txCount"] > 0 for d in days)
    return False


def replay_user(
    profile: dict,
    raw_days: list[dict],
    rng: random.Random,
    quests: list[dict],
    achievements: list[dict],
) -> dict:
    """Прогоняет 30 дней пользователя через правила и возвращает полный стейт."""
    energy_cfg = CONFIG["energy"]
    xp_cfg = CONFIG["xp"]
    streak_cfg = CONFIG["streak"]
    work_cfg = CONFIG["work"]

    total_xp = int(profile["startTotalXp"])
    state = {
        "totalXp": total_xp,
        "coins": int(profile["startCoins"]),
        "health": int(profile["startHealth"]),
        "logStreak": int(profile["startLogStreak"]),
        "budgetStreak": int(profile["startBudgetStreak"]),
        "bestLogStreak": int(profile["startLogStreak"]),
        "bestBudgetStreak": int(profile["startBudgetStreak"]),
    }
    totals = {
        "expenses": 0,
        "spent": 0,
        "daysWithinLimit": 0,
        "workSessions": 0,
        "questsCompleted": 0,
        "coinsEarned": 0,
        "xpEarned": 0,
        "purchases": int(profile.get("startPurchases", 0)) + int(profile.get("periodPurchases", 0)),
        "ownedItems": int(profile.get("startOwnedItems", 0)) + int(profile.get("periodPurchases", 0)),
        "categoriesUsed": set(),
    }
    day_records: list[dict] = []
    prev_date: date | None = None

    for day in raw_days:
        d = day["date"]
        gap = (d - prev_date).days if prev_date else 0
        prev_date = d

        level_before = level_state(state["totalXp"])["level"]
        quest_list = pick_quests(rng, quests, d, level_before)
        work_sessions = int(
            clamp(round(rng.gauss(profile["workMean"], 0.8)), 0, work_cfg["sessionsPerDay"])
        )

        tx = day["transactions"]
        spent = sum(t["amount"] for t in tx)
        tx_count = len(tx)
        note_count = sum(1 for t in tx if t.get("note"))
        cat_counts: dict[str, int] = {}
        for t in tx:
            cat_counts[t["categoryId"]] = cat_counts.get(t["categoryId"], 0) + 1
            totals["categoriesUsed"].add(t["categoryId"])
        energy = energy_used(spent, day["limit"])
        within = tx_count > 0 and spent <= day["limit"]

        ctx = {
            "txCount": tx_count,
            "noteCount": note_count,
            "catCounts": cat_counts,
            "workSessions": work_sessions,
            "energy": energy,
            "withinLimit": within,
            "engaged": rng.random() < profile["engagement"],
            "earlyLog": tx_count > 0 and rng.random() < profile["earlyChance"],
            "weekday": d.weekday(),
        }

        # --- XP за ведение учёта ---
        log_xp = min(
            xp_cfg["dailyLogCap"],
            tx_count * (xp_cfg["perExpense"] + xp_cfg["categoryBonus"])
            + note_count * xp_cfg["noteBonus"],
        )
        xp_gain = log_xp
        if within:
            xp_gain += xp_cfg["withinLimitBonus"]
        xp_gain += work_sessions * xp_cfg["workSessionXp"]

        # --- Здоровье и стрики ---
        if tx_count > 0:
            state["logStreak"] += 1
            state["bestLogStreak"] = max(state["bestLogStreak"], state["logStreak"])
        else:
            state["logStreak"] = 0

        state["health"] = int(
            clamp(state["health"] + energy_cfg["healthRegenDaily"], 0, 100)
        )
        if within:
            state["budgetStreak"] += 1
            state["bestBudgetStreak"] = max(state["bestBudgetStreak"], state["budgetStreak"])
            state["health"] = int(
                clamp(state["health"] + energy_cfg["healthGainWithinLimit"], 0, 100)
            )
        else:
            state["budgetStreak"] = 0
            if tx_count > 0:
                loss = min(
                    energy_cfg["healthLossMax"],
                    energy_cfg["healthLossOverspendBase"]
                    + round(max(0, energy - 100) * energy_cfg["healthLossOverspendPerPct"]),
                )
                state["health"] = int(clamp(state["health"] - loss, 5, 100))

        # --- Монеты ---
        multiplier = streak_multiplier(state["logStreak"])
        work_coins = 0
        perfects = 0
        for _ in range(work_sessions):
            work_coins += (work_cfg["baseCoins"] + level_before * work_cfg["coinsPerLevel"]) * multiplier
            if rng.random() < work_cfg["perfectChance"]:
                work_coins += work_cfg["perfectBonusCoins"]
                perfects += 1
        work_coins = int(round(work_coins))

        leftover_coins = int(
            math.floor(max(0, energy_cfg["max"] - energy) * energy_cfg["leftoverEnergyToCoins"])
        )

        quests_done = 0
        quest_coins = 0
        quest_xp = 0
        quest_records = []
        for q in quest_list:
            done = quest_is_complete(q, ctx, rng)
            if done:
                quests_done += 1
                quest_coins += q["rewards"]["coins"]
                quest_xp += q["rewards"]["xp"]
            quest_records.append(
                {
                    "id": q["id"],
                    "title": q["title"],
                    "done": done,
                    "coins": q["rewards"]["coins"] if done else 0,
                    "xp": q["rewards"]["xp"] if done else 0,
                }
            )

        weekly_bonus = 0
        if (
            state["budgetStreak"] > 0
            and state["budgetStreak"] % streak_cfg["weeklyBonusEvery"] == 0
        ):
            weekly_bonus = streak_cfg["weeklyBonusCoins"]
            xp_gain += xp_cfg["weeklyBonusXp"]

        coins_gain = work_coins + leftover_coins + quest_coins + weekly_bonus
        xp_gain += quest_xp

        state["coins"] += coins_gain
        state["totalXp"] += xp_gain
        totals["coinsEarned"] += coins_gain
        totals["xpEarned"] += xp_gain

        if tx_count > 0:
            totals["expenses"] += tx_count
            totals["spent"] += spent
        if within:
            totals["daysWithinLimit"] += 1
        totals["workSessions"] += work_sessions
        totals["questsCompleted"] += quests_done

        day_records.append(
            {
                "date": d.isoformat(),
                "gapDays": gap,
                "limit": day["limit"],
                "spent": spent,
                "energy": energy,
                "withinLimit": within,
                "txCount": tx_count,
                "noteCount": note_count,
                "catCounts": cat_counts,
                "workSessions": work_sessions,
                "perfects": perfects,
                "xpEarned": xp_gain,
                "coinsEarned": coins_gain,
                "coinsWork": work_coins,
                "coinsLeftover": leftover_coins,
                "coinsQuests": quest_coins,
                "coinsWeeklyBonus": weekly_bonus,
                "quests": quest_records,
                "questsCompleted": quests_done,
                "mood": mood_for(energy, state["health"]),
                "health": state["health"],
                "logStreak": state["logStreak"],
                "budgetStreak": state["budgetStreak"],
                "level": level_state(state["totalXp"])["level"],
            }
        )

    unlocked = []
    for ach in achievements:
        if achievement_unlocked(ach["condition"], state, totals, day_records):
            unlocked.append(ach["id"])

    totals["categoriesUsed"] = sorted(totals["categoriesUsed"])
    final_level = level_state(state["totalXp"])

    return {
        "state": {
            "totalXp": state["totalXp"],
            "level": final_level["level"],
            "levelTitle": final_level["title"],
            "xpIntoLevel": final_level["xpIntoLevel"],
            "xpToNext": final_level["xpToNext"],
            "coins": state["coins"],
            "health": state["health"],
            "logStreak": state["logStreak"],
            "budgetStreak": state["budgetStreak"],
            "bestLogStreak": state["bestLogStreak"],
            "bestBudgetStreak": state["bestBudgetStreak"],
            "mood": mood_for(day_records[-1]["energy"], state["health"]) if day_records else "happy",
            "achievements": unlocked,
        },
        "totals": {
            **totals,
            "categoriesUsed": totals["categoriesUsed"],
            "days": len(day_records),
            "avgDailySpent": round(
                sum(d["spent"] for d in day_records) / max(1, len(day_records))
            ),
            "avgDailyCoins": round(
                sum(d["coinsEarned"] for d in day_records) / max(1, len(day_records))
            ),
            "avgDailyXp": round(
                sum(d["xpEarned"] for d in day_records) / max(1, len(day_records))
            ),
        },
        "days": day_records,
    }
