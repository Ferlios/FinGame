"""
Контент прототипа: категории, питомцы, магазин, квесты, ачивки, архетипы игроков.

Все названия и цены — выдуманные, это прототипный контент для портфолио.
"""

from __future__ import annotations

import random
from datetime import date, timedelta

CATEGORIES = [
    {"id": "grocery", "name": "Продукты", "icon": "🛒", "color": "#6ee7b7", "examples": ["Пятёрочка", "ВкусВилл", "Продукты на неделю"], "typicalMin": 250, "typicalMax": 1600},
    {"id": "cafe", "name": "Кафе и кофе", "icon": "☕", "color": "#fbbf24", "examples": ["Кофе с собой", "Обед в кафе", "Завтрак с друзьями"], "typicalMin": 120, "typicalMax": 550},
    {"id": "transport", "name": "Транспорт", "icon": "🚌", "color": "#60a5fa", "examples": ["Метро", "Такси", "Проездной"], "typicalMin": 60, "typicalMax": 450},
    {"id": "shopping", "name": "Покупки", "icon": "🛍️", "color": "#f472b6", "examples": ["Кроссовки", "Футболка", "Маркетплейс"], "typicalMin": 400, "typicalMax": 3500},
    {"id": "entertainment", "name": "Развлечения", "icon": "🎮", "color": "#a78bfa", "examples": ["Кино", "Концерт", "Игра в Steam"], "typicalMin": 250, "typicalMax": 1400},
    {"id": "health", "name": "Здоровье", "icon": "💊", "color": "#34d399", "examples": ["Аптека", "Врач", "Витамины"], "typicalMin": 200, "typicalMax": 1800},
    {"id": "home", "name": "Дом", "icon": "🏠", "color": "#fb923c", "examples": ["Аренда", "Хозтовары", "Ремонт"], "typicalMin": 300, "typicalMax": 2500},
    {"id": "subscriptions", "name": "Подписки", "icon": "📱", "color": "#38bdf8", "examples": ["Музыка", "Кино", "Облако"], "typicalMin": 199, "typicalMax": 799},
    {"id": "education", "name": "Образование", "icon": "📚", "color": "#c084fc", "examples": ["Курс", "Книги", "Вебинар"], "typicalMin": 500, "typicalMax": 4500},
    {"id": "gifts", "name": "Подарки", "icon": "🎁", "color": "#f87171", "examples": ["День рождения", "Цветы", "Сувенир"], "typicalMin": 400, "typicalMax": 2200},
    {"id": "pets", "name": "Питомцы", "icon": "🐾", "color": "#facc15", "examples": ["Корм", "Ветклиника", "Игрушка"], "typicalMin": 250, "typicalMax": 1200},
    {"id": "other", "name": "Другое", "icon": "📦", "color": "#94a3b8", "examples": ["Разное", "Мелкие траты"], "typicalMin": 100, "typicalMax": 900},
]

PETS = [
    {
        "id": "moss", "name": "Мох", "icon": "🟢", "rarity": "common", "price": 0, "unlockLevel": 1,
        "description": "Мшистый комочек, который впитывает твои траты как воду. Спокойный и очень голодный.",
        "stages": [
            {"stage": 1, "name": "Мох-малыш", "level": 1, "color": "#7dd3a0", "accent": "#3f9c6b"},
            {"stage": 2, "name": "Мох-копилка", "level": 8, "color": "#5cc98a", "accent": "#2f7d55"},
            {"stage": 3, "name": "Мох-хранитель", "level": 18, "color": "#3fb87a", "accent": "#1f5e40"},
        ],
    },
    {
        "id": "plusha", "name": "Плюша", "icon": "🐱", "rarity": "rare", "price": 400, "unlockLevel": 5,
        "description": "Плюшевая кошка с карманом вместо сердца. Мурчит, когда бюджет в плюсе.",
        "stages": [
            {"stage": 1, "name": "Плюша-котёнок", "level": 1, "color": "#f9a8d4", "accent": "#be185d"},
            {"stage": 2, "name": "Плюша-фея", "level": 8, "color": "#f472b6", "accent": "#9d174d"},
            {"stage": 3, "name": "Плюша-львица", "level": 18, "color": "#ec4899", "accent": "#831843"},
        ],
    },
    {
        "id": "iskra", "name": "Искра", "icon": "🦊", "rarity": "rare", "price": 900, "unlockLevel": 10,
        "description": "Лисёнок из искр. Обожает стрики и ненавидит импульсивные покупки.",
        "stages": [
            {"stage": 1, "name": "Искра-уголёк", "level": 1, "color": "#fdba74", "accent": "#c2410c"},
            {"stage": 2, "name": "Искра-пламя", "level": 8, "color": "#fb923c", "accent": "#9a3412"},
            {"stage": 3, "name": "Искра-солнце", "level": 18, "color": "#f97316", "accent": "#7c2d12"},
        ],
    },
    {
        "id": "kefir", "name": "Кефир", "icon": "👻", "rarity": "epic", "price": 1400, "unlockLevel": 14,
        "description": "Полупрозрачный дух старой копилки. Появляется, когда ты не тратишь лишнего.",
        "stages": [
            {"stage": 1, "name": "Кефир-дымка", "level": 1, "color": "#c4b5fd", "accent": "#6d28d9"},
            {"stage": 2, "name": "Кефир-туман", "level": 8, "color": "#a78bfa", "accent": "#5b21b6"},
            {"stage": 3, "name": "Кефир-призрак", "level": 18, "color": "#8b5cf6", "accent": "#4c1d95"},
        ],
    },
    {
        "id": "bublik", "name": "Бублик", "icon": "🐹", "rarity": "epic", "price": 1800, "unlockLevel": 18,
        "description": "Круглый хомяк-бухгалтер. Считает каждую копейку и прячет монеты в щеках.",
        "stages": [
            {"stage": 1, "name": "Бублик-кроха", "level": 1, "color": "#fde68a", "accent": "#b45309"},
            {"stage": 2, "name": "Бублик-счётчик", "level": 8, "color": "#fcd34d", "accent": "#92400e"},
            {"stage": 3, "name": "Бублик-банкир", "level": 18, "color": "#fbbf24", "accent": "#78350f"},
        ],
    },
    {
        "id": "drak", "name": "Драк", "icon": "🐲", "rarity": "legendary", "price": 3000, "unlockLevel": 24,
        "description": "Мини-дракон, который копит на сокровищницу. Легендарный питомец для легендарной дисциплины.",
        "stages": [
            {"stage": 1, "name": "Драк-ящерка", "level": 1, "color": "#86efac", "accent": "#15803d"},
            {"stage": 2, "name": "Драк-змей", "level": 8, "color": "#4ade80", "accent": "#166534"},
            {"stage": 3, "name": "Драк-сокровище", "level": 18, "color": "#22c55e", "accent": "#14532d"},
        ],
    },
]

SHOP_ITEMS = [
    # --- Шляпы ---
    {"id": "hat_beanie", "name": "Шапка-бини", "category": "hat", "slot": "hat", "price": 60, "rarity": "common", "unlockLevel": 1, "emoji": "🧢", "description": "Тёплая шапка для холодного бюджета."},
    {"id": "hat_beret", "name": "Берет", "category": "hat", "slot": "hat", "price": 90, "rarity": "common", "unlockLevel": 1, "emoji": "👒", "description": "Для тех, кто тратит с французским шармом."},
    {"id": "hat_cap", "name": "Цилиндр", "category": "hat", "slot": "hat", "price": 120, "rarity": "rare", "unlockLevel": 3, "emoji": "🎩", "description": "Формальный вид для серьёзных накоплений."},
    {"id": "hat_grad", "name": "Академическая шапочка", "category": "hat", "slot": "hat", "price": 180, "rarity": "rare", "unlockLevel": 6, "emoji": "🎓", "description": "Диплом по экономии уже в кармане."},
    {"id": "hat_party", "name": "Праздничный колпак", "category": "hat", "slot": "hat", "price": 220, "rarity": "epic", "unlockLevel": 9, "emoji": "🥳", "description": "Когда неделя без перерасхода — это праздник."},
    {"id": "hat_wizard", "name": "Шляпа волшебника", "category": "hat", "slot": "hat", "price": 280, "rarity": "epic", "unlockLevel": 12, "emoji": "🪄", "description": "Превращает импульс в накопления."},
    {"id": "hat_crown", "name": "Корона", "category": "hat", "slot": "hat", "price": 700, "rarity": "legendary", "unlockLevel": 20, "emoji": "👑", "description": "Только для настоящей королевской экономии."},
    # --- Аксессуары ---
    {"id": "acc_bow", "name": "Бантик", "category": "accessory", "slot": "accessory", "price": 90, "rarity": "common", "unlockLevel": 1, "emoji": "🎀", "description": "Маленькая деталь — большой уют."},
    {"id": "acc_scarf", "name": "Шарф", "category": "accessory", "slot": "accessory", "price": 120, "rarity": "common", "unlockLevel": 2, "emoji": "🧣", "description": "Согревает даже в месяц без отпуска."},
    {"id": "acc_glasses", "name": "Очки", "category": "accessory", "slot": "accessory", "price": 140, "rarity": "rare", "unlockLevel": 4, "emoji": "🕶️", "description": "Видит все мелкие подписки."},
    {"id": "acc_headphones", "name": "Наушники", "category": "accessory", "slot": "accessory", "price": 220, "rarity": "rare", "unlockLevel": 7, "emoji": "🎧", "description": "Музыка для работы над бюджетом."},
    {"id": "acc_medal", "name": "Медаль", "category": "accessory", "slot": "accessory", "price": 300, "rarity": "epic", "unlockLevel": 10, "emoji": "🏅", "description": "За заслуги перед семейным бюджетом."},
    {"id": "acc_halo", "name": "Нимб", "category": "accessory", "slot": "accessory", "price": 650, "rarity": "legendary", "unlockLevel": 18, "emoji": "😇", "description": "Святая дисциплина трат."},
    # --- Мебель ---
    {"id": "furn_plant", "name": "Растение", "category": "furniture", "slot": "furniture", "price": 80, "rarity": "common", "unlockLevel": 1, "emoji": "🪴", "description": "Живой уголок в комнате питомца."},
    {"id": "furn_rug", "name": "Коврик", "category": "furniture", "slot": "furniture", "price": 100, "rarity": "common", "unlockLevel": 1, "emoji": "🧶", "description": "Мягко, уютно, по-домашнему."},
    {"id": "furn_lamp", "name": "Лампа", "category": "furniture", "slot": "furniture", "price": 120, "rarity": "common", "unlockLevel": 2, "emoji": "💡", "description": "Свет для вечерних подсчётов."},
    {"id": "furn_books", "name": "Книги", "category": "furniture", "slot": "furniture", "price": 150, "rarity": "common", "unlockLevel": 3, "emoji": "📚", "description": "Финансовая грамотность на полке."},
    {"id": "furn_teddy", "name": "Плюшевый друг", "category": "furniture", "slot": "furniture", "price": 180, "rarity": "rare", "unlockLevel": 4, "emoji": "🧸", "description": "Тот, кто всегда выслушает про траты."},
    {"id": "furn_guitar", "name": "Гитара", "category": "furniture", "slot": "furniture", "price": 220, "rarity": "rare", "unlockLevel": 6, "emoji": "🎸", "description": "Хобби без подписки."},
    {"id": "furn_aquarium", "name": "Аквариум", "category": "furniture", "slot": "furniture", "price": 280, "rarity": "rare", "unlockLevel": 8, "emoji": "🐠", "description": "Рыбки не просят повышения бюджета."},
    {"id": "furn_pc", "name": "Компьютер", "category": "furniture", "slot": "furniture", "price": 320, "rarity": "epic", "unlockLevel": 9, "emoji": "🖥️", "description": "Для ведения таблиц и работы мечты."},
    {"id": "furn_fireplace", "name": "Камин", "category": "furniture", "slot": "furniture", "price": 400, "rarity": "epic", "unlockLevel": 13, "emoji": "🔥", "description": "Сжигает лишние подписки. Шутка."},
    {"id": "furn_piano", "name": "Пианино", "category": "furniture", "slot": "furniture", "price": 520, "rarity": "legendary", "unlockLevel": 16, "emoji": "🎹", "description": "Рояль в кустах твоей финансовой стабильности."},
    # --- Темы комнаты ---
    {"id": "theme_cozy", "name": "Уют", "category": "theme", "slot": "theme", "price": 150, "rarity": "common", "unlockLevel": 2, "emoji": "🛋️", "description": "Тёплый бежевый вечер.", "colors": {"wall": "#3b2f4a", "wall2": "#57416b", "floor": "#2a2233", "accent": "#f0abfc"}},
    {"id": "theme_night", "name": "Ночной город", "category": "theme", "slot": "theme", "price": 250, "rarity": "rare", "unlockLevel": 5, "emoji": "🌃", "description": "Огни за окном и тишина.", "colors": {"wall": "#1e293b", "wall2": "#334155", "floor": "#0f172a", "accent": "#38bdf8"}},
    {"id": "theme_forest", "name": "Лесная хижина", "category": "theme", "slot": "theme", "price": 300, "rarity": "rare", "unlockLevel": 7, "emoji": "🌲", "description": "Дерево, мох и запах хвои.", "colors": {"wall": "#1f3a2e", "wall2": "#2f5a45", "floor": "#16261f", "accent": "#86efac"}},
    {"id": "theme_space", "name": "Космос", "category": "theme", "slot": "theme", "price": 500, "rarity": "epic", "unlockLevel": 11, "emoji": "🚀", "description": "Бюджет на орбите.", "colors": {"wall": "#1b1035", "wall2": "#3b1d6e", "floor": "#120a26", "accent": "#c4b5fd"}},
    {"id": "theme_sakura", "name": "Сакура", "category": "theme", "slot": "theme", "price": 700, "rarity": "legendary", "unlockLevel": 15, "emoji": "🌸", "description": "Цветение и дзен.", "colors": {"wall": "#4a2338", "wall2": "#7a3657", "floor": "#2e1622", "accent": "#f9a8d4"}},
    # --- Еда (расходники) ---
    {"id": "food_apple", "name": "Яблоко", "category": "food", "slot": "food", "price": 15, "rarity": "common", "unlockLevel": 1, "emoji": "🍎", "description": "Полезный перекус.", "consumable": True, "effect": {"health": 2, "mood": "happy"}},
    {"id": "food_cookie", "name": "Печенье", "category": "food", "slot": "food", "price": 20, "rarity": "common", "unlockLevel": 1, "emoji": "🍪", "description": "Маленькая радость.", "consumable": True, "effect": {"health": 1, "mood": "happy"}},
    {"id": "food_coffee", "name": "Кофе", "category": "food", "slot": "food", "price": 25, "rarity": "common", "unlockLevel": 2, "emoji": "☕", "description": "Бодрость для подсчётов.", "consumable": True, "effect": {"health": 1, "mood": "happy"}},
    {"id": "food_sushi", "name": "Суши", "category": "food", "slot": "food", "price": 40, "rarity": "rare", "unlockLevel": 4, "emoji": "🍣", "description": "Праздник среди недели.", "consumable": True, "effect": {"health": 4, "mood": "happy"}},
    {"id": "food_boba", "name": "Бабл-ти", "category": "food", "slot": "food", "price": 45, "rarity": "rare", "unlockLevel": 5, "emoji": "🧋", "description": "Сладкий антистресс.", "consumable": True, "effect": {"health": 3, "mood": "happy"}},
    {"id": "food_pizza", "name": "Пицца", "category": "food", "slot": "food", "price": 55, "rarity": "rare", "unlockLevel": 6, "emoji": "🍕", "description": "Для вечера с друзьями.", "consumable": True, "effect": {"health": 5, "mood": "happy"}},
    {"id": "food_cake", "name": "Тортик", "category": "food", "slot": "food", "price": 60, "rarity": "epic", "unlockLevel": 8, "emoji": "🎂", "description": "Праздник живота.", "consumable": True, "effect": {"health": 8, "mood": "happy"}},
    {"id": "food_golden", "name": "Золотое яблоко", "category": "food", "slot": "food", "price": 120, "rarity": "legendary", "unlockLevel": 12, "emoji": "🍏", "description": "Лечит даже финансовую грусть.", "consumable": True, "effect": {"health": 20, "mood": "happy"}},
]

QUESTS = [
    {"id": "q_log3", "title": "Дневник дня", "description": "Запиши 3 траты", "icon": "📝", "type": "daily", "weight": 10, "minLevel": 1, "condition": {"type": "log_count", "target": 3}, "rewards": {"coins": 30, "xp": 15}},
    {"id": "q_log5", "title": "Полный учёт", "description": "Запиши 5 трат за день", "icon": "🗂️", "type": "daily", "weight": 6, "minLevel": 4, "condition": {"type": "log_count", "target": 5}, "rewards": {"coins": 45, "xp": 20}},
    {"id": "q_under", "title": "Уложись в лимит", "description": "Не превысь дневной лимит", "icon": "🎯", "type": "daily", "weight": 10, "minLevel": 1, "condition": {"type": "under_limit"}, "rewards": {"coins": 50, "xp": 25}},
    {"id": "q_half", "title": "Энергия на завтра", "description": "Потрать не больше половины лимита", "icon": "🔋", "type": "daily", "weight": 5, "minLevel": 5, "condition": {"type": "energy_left", "target": 50}, "rewards": {"coins": 60, "xp": 30}},
    {"id": "q_cafe", "title": "Кофейный чек", "description": "Запиши трату в категории «Кафе»", "icon": "☕", "type": "daily", "weight": 7, "minLevel": 1, "condition": {"type": "category_count", "categoryId": "cafe", "target": 1}, "rewards": {"coins": 25, "xp": 10}},
    {"id": "q_grocery", "title": "Продуктовая миссия", "description": "Запиши покупку продуктов", "icon": "🛒", "type": "daily", "weight": 7, "minLevel": 1, "condition": {"type": "category_count", "categoryId": "grocery", "target": 1}, "rewards": {"coins": 25, "xp": 10}},
    {"id": "q_transport", "title": "Дорога учтена", "description": "Запиши 2 траты на транспорт", "icon": "🚌", "type": "daily", "weight": 4, "minLevel": 2, "condition": {"type": "category_count", "categoryId": "transport", "target": 2}, "rewards": {"coins": 30, "xp": 15}},
    {"id": "q_note", "title": "С заметками", "description": "Добавь заметки к 2 тратам", "icon": "✍️", "type": "daily", "weight": 5, "minLevel": 3, "condition": {"type": "note_count", "target": 2}, "rewards": {"coins": 35, "xp": 15}},
    {"id": "q_work1", "title": "Одна смена", "description": "Отправь питомца на работу", "icon": "💼", "type": "daily", "weight": 8, "minLevel": 1, "condition": {"type": "work_sessions", "target": 1}, "rewards": {"coins": 20, "xp": 10}},
    {"id": "q_work2", "title": "Две смены", "description": "Отработай 2 смены за день", "icon": "🛠️", "type": "daily", "weight": 4, "minLevel": 4, "condition": {"type": "work_sessions", "target": 2}, "rewards": {"coins": 35, "xp": 15}},
    {"id": "q_nocafe", "title": "Без кофе с собой", "description": "День без трат в категории «Кафе»", "icon": "🚫", "type": "daily", "weight": 5, "minLevel": 3, "condition": {"type": "avoid_category", "categoryId": "cafe"}, "rewards": {"coins": 55, "xp": 25}},
    {"id": "q_noimpulse", "title": "Без импульсов", "description": "День без категории «Покупки»", "icon": "🧘", "type": "daily", "weight": 4, "minLevel": 5, "condition": {"type": "avoid_category", "categoryId": "shopping"}, "rewards": {"coins": 55, "xp": 25}},
    {"id": "q_pet", "title": "Проверь питомца", "description": "Загляни к питомцу и погладь его", "icon": "🐾", "type": "daily", "weight": 8, "minLevel": 1, "condition": {"type": "check_pet"}, "rewards": {"coins": 15, "xp": 5}},
    {"id": "q_early", "title": "Ранняя запись", "description": "Запиши трату до полудня", "icon": "🌅", "type": "daily", "weight": 5, "minLevel": 2, "condition": {"type": "early_log"}, "rewards": {"coins": 30, "xp": 15}},
    {"id": "q_weekly", "title": "Итоги недели", "description": "Загляни в недельный отчёт", "icon": "📊", "type": "weekly", "weight": 3, "minLevel": 5, "condition": {"type": "weekly_review"}, "rewards": {"coins": 70, "xp": 35}},
    {"id": "q_health", "title": "Здоровье в фокусе", "description": "Запиши трату на здоровье", "icon": "💊", "type": "daily", "weight": 4, "minLevel": 3, "condition": {"type": "category_count", "categoryId": "health", "target": 1}, "rewards": {"coins": 30, "xp": 15}},
    {"id": "q_fun", "title": "Культурный досуг", "description": "Запиши трату на развлечения", "icon": "🎭", "type": "daily", "weight": 4, "minLevel": 2, "condition": {"type": "category_count", "categoryId": "entertainment", "target": 1}, "rewards": {"coins": 30, "xp": 15}},
    {"id": "q_save30", "title": "Экономный день", "description": "Оставь 30% энергии неистраченной", "icon": "🌱", "type": "daily", "weight": 4, "minLevel": 6, "condition": {"type": "energy_left", "target": 30}, "rewards": {"coins": 40, "xp": 20}},
]

ACHIEVEMENTS = [
    {"id": "ach_first_expense", "title": "Первая запись", "description": "Запиши свою первую трату", "icon": "🌱", "tier": "bronze", "hidden": False, "condition": {"type": "expense_count", "target": 1}, "rewards": {"coins": 20, "xp": 10}},
    {"id": "ach_first_thousand", "title": "Первая тысяча", "description": "Учти трат на 1 000 ₽", "icon": "💵", "tier": "bronze", "hidden": False, "condition": {"type": "total_spent", "target": 1000}, "rewards": {"coins": 40, "xp": 20}},
    {"id": "ach_ten", "title": "Дневник начат", "description": "Запиши 10 трат", "icon": "📒", "tier": "bronze", "hidden": False, "condition": {"type": "expense_count", "target": 10}, "rewards": {"coins": 30, "xp": 15}},
    {"id": "ach_hundred", "title": "Сотня записей", "description": "Запиши 100 трат", "icon": "📚", "tier": "gold", "hidden": False, "condition": {"type": "expense_count", "target": 100}, "rewards": {"coins": 150, "xp": 80}},
    {"id": "ach_week", "title": "Первая неделя", "description": "Веди учёт 7 дней подряд", "icon": "🔥", "tier": "silver", "hidden": False, "condition": {"type": "log_streak", "target": 7}, "rewards": {"coins": 80, "xp": 50}},
    {"id": "ach_streak30", "title": "Железная дисциплина", "description": "Стрик 30 дней", "icon": "🛡️", "tier": "gold", "hidden": False, "condition": {"type": "log_streak", "target": 30}, "rewards": {"coins": 300, "xp": 150}},
    {"id": "ach_within7", "title": "Экономная неделя", "description": "7 дней подряд в пределах лимита", "icon": "✅", "tier": "silver", "hidden": False, "condition": {"type": "budget_streak", "target": 7}, "rewards": {"coins": 100, "xp": 60}},
    {"id": "ach_within30", "title": "Экономный месяц", "description": "30 дней подряд в пределах лимита", "icon": "🏆", "tier": "gold", "hidden": False, "condition": {"type": "budget_streak", "target": 30}, "rewards": {"coins": 500, "xp": 250}},
    {"id": "ach_nocoffee", "title": "Неделя без кофе с собой", "description": "7 дней подряд без трат в «Кафе»", "icon": "☕", "tier": "silver", "hidden": False, "condition": {"type": "no_category_streak", "categoryId": "cafe", "target": 7}, "rewards": {"coins": 120, "xp": 70}},
    {"id": "ach_lvl5", "title": "Пятый уровень", "description": "Достигни 5 уровня", "icon": "⭐", "tier": "bronze", "hidden": False, "condition": {"type": "level", "target": 5}, "rewards": {"coins": 40, "xp": 20}},
    {"id": "ach_lvl10", "title": "Десятка", "description": "Достигни 10 уровня", "icon": "🌟", "tier": "silver", "hidden": False, "condition": {"type": "level", "target": 10}, "rewards": {"coins": 100, "xp": 60}},
    {"id": "ach_lvl20", "title": "Маг бюджета", "description": "Достигни 20 уровня", "icon": "🧙", "tier": "gold", "hidden": False, "condition": {"type": "level", "target": 20}, "rewards": {"coins": 300, "xp": 150}},
    {"id": "ach_first_buy", "title": "Первая покупка", "description": "Купи первый предмет в магазине", "icon": "🛍️", "tier": "bronze", "hidden": False, "condition": {"type": "purchases", "target": 1}, "rewards": {"coins": 20, "xp": 10}},
    {"id": "ach_collector10", "title": "Коллекционер", "description": "Собери 10 предметов", "icon": "🎒", "tier": "silver", "hidden": False, "condition": {"type": "owned_items", "target": 10}, "rewards": {"coins": 200, "xp": 100}},
    {"id": "ach_collector25", "title": "Гардероб мечты", "description": "Собери 25 предметов", "icon": "👗", "tier": "gold", "hidden": False, "condition": {"type": "owned_items", "target": 25}, "rewards": {"coins": 500, "xp": 250}},
    {"id": "ach_work50", "title": "Трудяга", "description": "Отработай 50 смен питомцем", "icon": "💼", "tier": "silver", "hidden": False, "condition": {"type": "work_sessions", "target": 50}, "rewards": {"coins": 150, "xp": 80}},
    {"id": "ach_quest50", "title": "Квестоман", "description": "Выполни 50 квестов", "icon": "🗺️", "tier": "silver", "hidden": False, "condition": {"type": "quests_completed", "target": 50}, "rewards": {"coins": 150, "xp": 80}},
    {"id": "ach_categories", "title": "Все категории", "description": "Используй все 12 категорий трат", "icon": "🎨", "tier": "gold", "hidden": False, "condition": {"type": "categories_used", "target": 12}, "rewards": {"coins": 120, "xp": 60}},
    {"id": "ach_hero", "title": "Герой бюджета", "description": "20 дней в пределах лимита", "icon": "🦸", "tier": "gold", "hidden": False, "condition": {"type": "budget_streak", "target": 20}, "rewards": {"coins": 250, "xp": 120}},
    {"id": "ach_rich", "title": "Богач", "description": "Заработай 5 000 монет", "icon": "🪙", "tier": "gold", "hidden": False, "condition": {"type": "coins_earned", "target": 5000}, "rewards": {"coins": 300, "xp": 150}},
    {"id": "ach_perfect", "title": "Идеальный день", "description": "День с 50% неистраченной энергии", "icon": "🌈", "tier": "silver", "hidden": True, "condition": {"type": "energy_left_once", "target": 50}, "rewards": {"coins": 50, "xp": 30}},
    {"id": "ach_comeback", "title": "Возвращение", "description": "Вернись в учёт после 3 дней паузы", "icon": "🔁", "tier": "bronze", "hidden": True, "condition": {"type": "comeback", "target": 1}, "rewards": {"coins": 60, "xp": 30}},
]

# --- Архетипы игроков для мок-данных -------------------------------------

ARCHETYPES = {
    "disciplined": {
        "label": "Дисциплинированная",
        "spendFactor": 0.75, "weekendFactor": 1.1, "skipChance": 0.02,
        "meanTx": 3.4, "workMean": 2.6, "engagement": 0.9, "questBias": 1.0,
        "noteChance": 0.62, "earlyChance": 0.55, "impulseChance": 0.012,
        "weights": {"grocery": 30, "cafe": 8, "transport": 15, "shopping": 8, "entertainment": 8, "health": 5, "home": 8, "subscriptions": 4, "education": 4, "gifts": 4, "pets": 3, "other": 3},
    },
    "coffee_addict": {
        "label": "Кофеман",
        "spendFactor": 0.95, "weekendFactor": 1.12, "skipChance": 0.02,
        "meanTx": 2.6, "workMean": 1.9, "engagement": 0.72, "questBias": 0.85,
        "noteChance": 0.35, "earlyChance": 0.65, "impulseChance": 0.05,
        "weights": {"grocery": 18, "cafe": 30, "transport": 12, "shopping": 10, "entertainment": 10, "health": 3, "home": 5, "subscriptions": 4, "education": 2, "gifts": 2, "pets": 2, "other": 2},
    },
    "impulse_buyer": {
        "label": "Импульсивный",
        "spendFactor": 1.02, "weekendFactor": 1.22, "skipChance": 0.03,
        "meanTx": 2.8, "workMean": 2.1, "engagement": 0.78, "questBias": 0.8,
        "noteChance": 0.3, "earlyChance": 0.35, "impulseChance": 0.11,
        "weights": {"grocery": 15, "cafe": 10, "transport": 10, "shopping": 30, "entertainment": 15, "health": 3, "home": 5, "subscriptions": 3, "education": 2, "gifts": 4, "pets": 1, "other": 2},
    },
    "weekend_spender": {
        "label": "Тратит на выходных",
        "spendFactor": 0.7, "weekendFactor": 1.4, "skipChance": 0.02,
        "meanTx": 2.4, "workMean": 2.3, "engagement": 0.82, "questBias": 0.9,
        "noteChance": 0.4, "earlyChance": 0.4, "impulseChance": 0.08,
        "weights": {"grocery": 22, "cafe": 14, "transport": 10, "shopping": 18, "entertainment": 16, "health": 4, "home": 5, "subscriptions": 3, "education": 2, "gifts": 3, "pets": 1, "other": 2},
    },
    "newbie": {
        "label": "Новичок",
        "spendFactor": 0.85, "weekendFactor": 1.15, "skipChance": 0.18,
        "meanTx": 1.9, "workMean": 1.1, "engagement": 0.55, "questBias": 0.6,
        "noteChance": 0.25, "earlyChance": 0.3, "impulseChance": 0.07,
        "weights": {"grocery": 25, "cafe": 18, "transport": 12, "shopping": 15, "entertainment": 12, "health": 3, "home": 4, "subscriptions": 3, "education": 2, "gifts": 2, "pets": 1, "other": 3},
    },
    "frugal_saver": {
        "label": "Экономный",
        "spendFactor": 0.6, "weekendFactor": 1.08, "skipChance": 0.01,
        "meanTx": 3.8, "workMean": 3.0, "engagement": 0.94, "questBias": 1.05,
        "noteChance": 0.55, "earlyChance": 0.6, "impulseChance": 0.02,
        "weights": {"grocery": 35, "cafe": 5, "transport": 18, "shopping": 4, "entertainment": 5, "health": 6, "home": 8, "subscriptions": 5, "education": 5, "gifts": 3, "pets": 3, "other": 3},
    },
}

USERS = [
    {"id": "u_001", "name": "Аня", "avatar": "🦊", "archetype": "disciplined", "dailyLimit": 1800, "income": 95000, "startLevel": 9, "startCoins": 1240, "startHealth": 88, "startLogStreak": 12, "startBudgetStreak": 9, "startPurchases": 7, "startOwnedItems": 7, "periodPurchases": 4, "timezone": "Europe/Moscow"},
    {"id": "u_002", "name": "Марк", "avatar": "🐻", "archetype": "coffee_addict", "dailyLimit": 1500, "income": 72000, "startLevel": 6, "startCoins": 520, "startHealth": 64, "startLogStreak": 5, "startBudgetStreak": 0, "startPurchases": 3, "startOwnedItems": 3, "periodPurchases": 3, "timezone": "Europe/Moscow"},
    {"id": "u_003", "name": "Лиза", "avatar": "🐰", "archetype": "impulse_buyer", "dailyLimit": 2000, "income": 81000, "startLevel": 7, "startCoins": 860, "startHealth": 58, "startLogStreak": 3, "startBudgetStreak": 1, "startPurchases": 4, "startOwnedItems": 4, "periodPurchases": 5, "timezone": "Europe/Moscow"},
    {"id": "u_004", "name": "Дима", "avatar": "🐺", "archetype": "weekend_spender", "dailyLimit": 2500, "income": 120000, "startLevel": 8, "startCoins": 1500, "startHealth": 80, "startLogStreak": 9, "startBudgetStreak": 4, "startPurchases": 6, "startOwnedItems": 6, "periodPurchases": 4, "timezone": "Europe/Moscow"},
    {"id": "u_005", "name": "Тимур", "avatar": "🐣", "archetype": "newbie", "dailyLimit": 1000, "income": 42000, "startLevel": 2, "startCoins": 180, "startHealth": 72, "startLogStreak": 0, "startBudgetStreak": 0, "startPurchases": 1, "startOwnedItems": 1, "periodPurchases": 1, "timezone": "Europe/Moscow"},
    {"id": "u_006", "name": "Соня", "avatar": "🦉", "archetype": "frugal_saver", "dailyLimit": 2200, "income": 140000, "startLevel": 10, "startCoins": 2400, "startHealth": 96, "startLogStreak": 21, "startBudgetStreak": 16, "startPurchases": 9, "startOwnedItems": 9, "periodPurchases": 3, "timezone": "Europe/Moscow"},
]

NOTE_TEMPLATES = {
    "grocery": ["Пятёрочка", "ВкусВилл", "Ашан", "Продукты на неделю", "Фрукты и овощи", "Молочка"],
    "cafe": ["Кофе с собой", "Обед в кафе", "Капучино", "Завтрак с друзьями", "Чай и круассан"],
    "transport": ["Метро", "Такси до офиса", "Проездной", "Автобус", "Каршеринг"],
    "shopping": ["Кроссовки", "Футболка", "Заказ на маркетплейсе", "Косметика", "Чехол для телефона"],
    "entertainment": ["Кино", "Концерт", "Игра в Steam", "Настолки", "Выставка"],
    "health": ["Аптека", "Витамины", "Приём у врача", "Анализы", "Массаж"],
    "home": ["Хозтовары", "Аренда", "Ремонт", "Подушки", "Уборка"],
    "subscriptions": ["Музыка", "Киносервис", "Облако", "Игровая подписка", "Приложение"],
    "education": ["Курс", "Книги", "Вебинар", "Английский", "Мастер-класс"],
    "gifts": ["День рождения", "Цветы", "Сувенир", "Подарок маме", "Свадебный подарок"],
    "pets": ["Корм", "Ветклиника", "Игрушка", "Наполнитель", "Лакомство"],
    "other": ["Разное", "Мелкие траты", "Не помню на что", "Непредвиденное"],
}


def _weighted_category(rng: random.Random, weights: dict) -> str:
    ids = list(weights.keys())
    return rng.choices(ids, weights=[weights[i] for i in ids], k=1)[0]


def _split_amount(rng: random.Random, total: float, n: int) -> list[int]:
    raw = [rng.expovariate(1.0) for _ in range(n)]
    s = sum(raw) or 1
    parts = [max(40, int(round(total * r / s / 10) * 10)) for r in raw]
    return parts


def generate_raw_days(profile: dict, start: date, n_days: int, rng: random.Random) -> list[dict]:
    arch = ARCHETYPES[profile["archetype"]]
    limit = profile["dailyLimit"]
    days = []
    for i in range(n_days):
        d = start + timedelta(days=i)
        weekend = d.weekday() >= 5
        if rng.random() < arch["skipChance"]:
            days.append({"date": d, "limit": limit, "transactions": []})
            continue

        factor = arch["spendFactor"] * (arch["weekendFactor"] if weekend else 1.0)
        noise = rng.lognormvariate(0, 0.18)
        target = limit * factor * noise

        n_tx = int(max(1, min(8, round(rng.gauss(arch["meanTx"], 1.1)))))
        amounts = _split_amount(rng, target, n_tx)
        if arch["impulseChance"] and rng.random() < arch["impulseChance"]:
            amounts.append(int(round(rng.uniform(700, 2600) / 10) * 10))

        cats = [_weighted_category(rng, arch["weights"]) for _ in amounts]
        times = sorted(rng.randint(8 * 60, 22 * 60) for _ in amounts)

        transactions = []
        for amount, cat, minute in zip(amounts, cats, times):
            note = ""
            if rng.random() < arch["noteChance"]:
                note = rng.choice(NOTE_TEMPLATES[cat])
            transactions.append(
                {
                    "amount": int(amount),
                    "categoryId": cat,
                    "note": note,
                    "time": f"{minute // 60:02d}:{minute % 60:02d}",
                }
            )
        days.append({"date": d, "limit": limit, "transactions": transactions})
    return days
