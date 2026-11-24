/* ============================================================
   Бюджетный питомец — игровая логика прототипа
   Все правила взяты из data/game_config.json
   ============================================================ */

const CONFIG = DATA.CONFIG;
const LEVELS = DATA.LEVELS;
const CATEGORIES = DATA.CATEGORIES;
const PETS = DATA.PETS;
const SHOP = DATA.SHOP_ITEMS;
const QUESTS = DATA.QUESTS;
const ACHIEVEMENTS = DATA.ACHIEVEMENTS;

const CAT_BY_ID = Object.fromEntries(CATEGORIES.map(c => [c.id, c]));
const QUEST_BY_ID = Object.fromEntries(QUESTS.map(q => [q.id, q]));
const SHOP_BY_ID = Object.fromEntries(SHOP.map(i => [i.id, i]));
const PET_BY_ID = Object.fromEntries(PETS.map(p => [p.id, p]));
const ACH_BY_ID = Object.fromEntries(ACHIEVEMENTS.map(a => [a.id, a]));

const LS_KEY = 'budget-buddy-prototype-v1';
let S = null;

/* ---------------- helpers ---------------- */

const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
const pad2 = n => String(n).padStart(2, '0');
const isoDate = d => `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;
const addDays = (iso, n) => {
  const d = new Date(iso + 'T12:00:00');
  d.setDate(d.getDate() + n);
  return isoDate(d);
};
const prettyDate = iso => new Date(iso + 'T12:00:00')
  .toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' });
const nowTime = () => {
  const d = new Date();
  return `${pad2(d.getHours())}:${pad2(d.getMinutes())}`;
};

function xpForLevel(level) {
  return LEVELS.filter(l => l.level < level).reduce((sum, l) => sum + l.xpToNext, 0);
}

function levelInfo(totalXp) {
  let remaining = Math.max(0, Math.round(totalXp));
  for (const l of LEVELS) {
    if (l.level === LEVELS.length) {
      return { level: l.level, title: l.title, into: 0, next: 0, progress: 1 };
    }
    if (remaining < l.xpToNext) {
      return {
        level: l.level, title: l.title, into: remaining, next: l.xpToNext,
        progress: remaining / l.xpToNext
      };
    }
    remaining -= l.xpToNext;
  }
  return { level: 30, title: 'Гуру денег', into: 0, next: 0, progress: 1 };
}

const streakMult = () => Math.min(
  CONFIG.streak.maxMultiplier,
  1 + S.logStreak * CONFIG.streak.coinMultiplierPerDay
);

const energyUsed = () => Math.round((S.spent / Math.max(1, S.dailyLimit)) * 100);

function currentMood() {
  if (S.health < 25) return 'sick';
  const e = energyUsed();
  if (e <= CONFIG.energy.happyMax) return 'happy';
  if (e <= CONFIG.energy.neutralMax) return 'neutral';
  return 'sad';
}

function petStage() {
  const pet = PET_BY_ID[S.petId] || PETS[0];
  const lvl = levelInfo(S.totalXp).level;
  let stage = pet.stages[0];
  for (const st of pet.stages) if (lvl >= st.level) stage = st;
  return { pet, stage };
}

function catCounts() {
  const counts = {};
  for (const t of S.tx) counts[t.categoryId] = (counts[t.categoryId] || 0) + 1;
  return counts;
}

function questCtx() {
  const counts = catCounts();
  return {
    txCount: S.tx.length,
    noteCount: S.tx.filter(t => t.note).length,
    catCounts: counts,
    workSessions: S.workUsed,
    energy: energyUsed(),
    spent: S.spent,
    petChecked: S.petChecked,
    earlyLog: S.earlyLogged,
    weekday: new Date(S.date + 'T12:00:00').getDay()
  };
}

/* ---------------- state ---------------- */

function seedState() {
  const totalXp = xpForLevel(4) + 120;
  return {
    version: 1,
    day: 7,
    date: isoDate(new Date()),
    dailyLimit: 1500,
    spent: 570,
    coins: 640,
    totalXp,
    health: 84,
    logStreak: 6,
    budgetStreak: 3,
    bestLogStreak: 6,
    bestBudgetStreak: 5,
    workUsed: 1,
    logXpToday: 14,
    dayXp: 0,
    dayCoins: 0,
    petChecked: false,
    earlyLogged: false,
    endWarn: false,
    quests: [
      { id: 'q_log3', done: false, failed: false },
      { id: 'q_cafe', done: true, failed: false },
      { id: 'q_under', done: false, failed: false }
    ],
    achievements: ['ach_first_expense', 'ach_first_thousand', 'ach_ten', 'ach_first_buy'],
    owned: ['hat_beanie', 'acc_bow', 'furn_plant', 'furn_rug', 'theme_cozy'],
    ownedPets: ['moss'],
    equipped: {
      hat: 'hat_beanie',
      accessory: 'acc_bow',
      theme: 'theme_cozy',
      furniture: ['furn_plant', 'furn_rug']
    },
    petId: 'moss',
    purchasesCount: 3,
    lifetimeExpenses: 68,
    lifetimeSpent: 41200,
    lifetimeWork: 21,
    lifetimeQuests: 34,
    lifetimeCoinsEarned: 1900,
    lifetimeXp: totalXp,
    lifetimeCategories: {
      grocery: 24, cafe: 16, transport: 12, shopping: 8, entertainment: 8
    },
    minEnergyWithTx: 60,
    cafeFreeStreak: 0,
    bestCafeFreeStreak: 0,
    comebackDone: false,
    tx: [
      { id: 'seed1', amount: 250, categoryId: 'cafe', note: 'Кофе с собой', time: '09:40' },
      { id: 'seed2', amount: 320, categoryId: 'grocery', note: 'Продукты', time: '18:10' }
    ]
  };
}

function loadState() {
  try {
    const raw = localStorage.getItem(LS_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed || parsed.version !== 1) return null;
    return Object.assign(seedState(), parsed);
  } catch (e) {
    return null;
  }
}

function save() {
  try {
    localStorage.setItem(LS_KEY, JSON.stringify(S));
  } catch (e) { /* приватный режим — просто живём без сохранения */ }
}

function resetProgress() {
  try { localStorage.removeItem(LS_KEY); } catch (e) {}
  S = seedState();
  save();
}

/* ---------------- economy actions ---------------- */

function addXp(n, opts = {}) {
  if (!n) return;
  const before = levelInfo(S.totalXp).level;
  S.totalXp += n;
  S.dayXp += n;
  S.lifetimeXp += n;
  const after = levelInfo(S.totalXp).level;
  if (after > before) {
    const info = levelInfo(S.totalXp);
    setTimeout(() => {
      toast(`🎉 Уровень ${after} — ${info.title}!`);
      confettiBurst(26);
    }, 260);
  }
}

function addCoins(n) {
  if (!n) return;
  S.coins += n;
  if (n > 0) {
    S.dayCoins += n;
    S.lifetimeCoinsEarned += n;
  }
}

function addExpense(amount, categoryId, note) {
  if (!Number.isFinite(amount) || amount <= 0) {
    return { ok: false, error: 'Введи сумму больше нуля' };
  }
  const cat = CAT_BY_ID[categoryId] ? categoryId : 'other';
  const cleanNote = (note || '').trim();

  S.tx.unshift({
    id: 'tx' + Date.now().toString(36) + Math.random().toString(36).slice(2, 5),
    amount: Math.round(amount),
    categoryId: cat,
    note: cleanNote,
    time: nowTime()
  });
  S.spent += Math.round(amount);
  S.lifetimeExpenses += 1;
  S.lifetimeSpent += Math.round(amount);
  S.lifetimeCategories[cat] = (S.lifetimeCategories[cat] || 0) + 1;

  let xp = CONFIG.xp.perExpense + CONFIG.xp.categoryBonus + (cleanNote ? CONFIG.xp.noteBonus : 0);
  const room = Math.max(0, CONFIG.xp.dailyLogCap - S.logXpToday);
  const gained = Math.min(xp, room);
  S.logXpToday += gained;
  addXp(gained);

  if (S.tx.length === 1) S.earlyLogged = new Date().getHours() < 12;
  S.minEnergyWithTx = Math.min(S.minEnergyWithTx, energyUsed());

  checkQuests(false);
  checkAchievements();
  save();

  return { ok: true, xp: gained, energy: energyUsed(), amount: Math.round(amount) };
}

function finishWork(bonus) {
  const lvl = levelInfo(S.totalXp).level;
  const base = Math.round(
    (CONFIG.work.baseCoins + lvl * CONFIG.work.coinsPerLevel) * streakMult()
  );
  const total = base + bonus;
  S.workUsed += 1;
  S.lifetimeWork += 1;
  addCoins(total);
  addXp(CONFIG.xp.workSessionXp);
  checkQuests(false);
  checkAchievements();
  save();
  return { base, bonus, total };
}

function canEquipFurniture(id) {
  const arr = S.equipped.furniture || [];
  if (arr.includes(id)) return true;
  return arr.length < CONFIG.shop.equipSlots.furniture;
}

function equipItem(item) {
  if (item.slot === 'theme') {
    S.equipped.theme = S.equipped.theme === item.id ? null : item.id;
  } else if (item.slot === 'hat' || item.slot === 'accessory') {
    S.equipped[item.slot] = S.equipped[item.slot] === item.id ? null : item.id;
  } else if (item.slot === 'furniture') {
    const arr = S.equipped.furniture || [];
    if (arr.includes(item.id)) {
      S.equipped.furniture = arr.filter(x => x !== item.id);
    } else if (arr.length < CONFIG.shop.equipSlots.furniture) {
      S.equipped.furniture = [...arr, item.id];
    }
  }
  return true;
}

function buyItem(id) {
  const item = SHOP_BY_ID[id];
  if (!item) return { ok: false, error: 'Предмет не найден' };
  const lvl = levelInfo(S.totalXp).level;
  if (item.unlockLevel > lvl) {
    return { ok: false, error: `Откроется на ${item.unlockLevel} уровне` };
  }

  if (item.consumable) {
    if (S.coins < item.price) return { ok: false, error: 'Не хватает монет' };
    S.coins -= item.price;
    S.purchasesCount += 1;
    const heal = (item.effect && item.effect.health) || 0;
    S.health = clamp(S.health + heal, 0, 100);
    addXp(2);
    checkAchievements();
    save();
    return { ok: true, fed: true, heal };
  }

  const owned = S.owned.includes(item.id);
  if (owned) {
    if (item.slot === 'furniture' && !canEquipFurniture(item.id)) {
      return { ok: false, error: 'В комнате максимум 3 предмета мебели' };
    }
    equipItem(item);
    save();
    return { ok: true, equipped: true };
  }

  if (S.coins < item.price) return { ok: false, error: 'Не хватает монет' };
  if (item.slot === 'furniture' && !canEquipFurniture(item.id)) {
    return { ok: false, error: 'В комнате максимум 3 предмета мебели' };
  }
  S.coins -= item.price;
  S.purchasesCount += 1;
  S.owned.push(item.id);
  equipItem(item);
  checkAchievements();
  save();
  return { ok: true, bought: true };
}

function buyPet(id) {
  const pet = PET_BY_ID[id];
  if (!pet) return { ok: false, error: 'Питомец не найден' };
  const lvl = levelInfo(S.totalXp).level;
  if (!S.ownedPets.includes(id)) {
    if (pet.unlockLevel > lvl) return { ok: false, error: `Откроется на ${pet.unlockLevel} уровне` };
    if (S.coins < pet.price) return { ok: false, error: 'Не хватает монет' };
    S.coins -= pet.price;
    S.purchasesCount += 1;
    S.ownedPets.push(id);
  }
  S.petId = id;
  checkAchievements();
  save();
  return { ok: true };
}

/* ---------------- quests ---------------- */

function assignQuests() {
  const lvl = levelInfo(S.totalXp).level;
  const weekday = new Date(S.date + 'T12:00:00').getDay();
  const pool = QUESTS.filter(q =>
    q.minLevel <= lvl && (q.condition.type !== 'weekly_review' || weekday === 0)
  );
  const picked = [];
  const pickedDefs = [];
  while (picked.length < CONFIG.quests.perDay && pool.length) {
    const weights = pool.map(q => q.weight * (
      pickedDefs.some(d => d.condition.type === q.condition.type) ? 0.3 : 1
    ));
    let r = Math.random() * weights.reduce((a, b) => a + b, 0);
    let idx = 0;
    for (; idx < weights.length; idx++) {
      r -= weights[idx];
      if (r <= 0) break;
    }
    idx = Math.min(idx, pool.length - 1);
    const [def] = pool.splice(idx, 1);
    picked.push({ id: def.id, done: false, failed: false });
    pickedDefs.push(def);
  }
  return picked;
}

function evalQuest(q, ctx, settle) {
  const c = q.condition;
  const t = c.target || 1;
  switch (c.type) {
    case 'log_count': return ctx.txCount >= t;
    case 'under_limit': return settle && ctx.txCount > 0 && ctx.spent <= S.dailyLimit;
    case 'category_count': return (ctx.catCounts[c.categoryId] || 0) >= t;
    case 'note_count': return ctx.noteCount >= t;
    case 'work_sessions': return ctx.workSessions >= t;
    case 'avoid_category': return settle && ctx.txCount > 0 && !(ctx.catCounts[c.categoryId] > 0);
    case 'check_pet': return ctx.petChecked;
    case 'early_log': return ctx.earlyLog;
    case 'weekly_review': return settle && ctx.weekday === 0;
    case 'energy_left': return settle && ctx.txCount > 0 && ctx.energy <= t;
    default: return false;
  }
}

function checkQuests(settle) {
  const ctx = questCtx();
  let changed = false;
  for (const qs of S.quests) {
    const q = QUEST_BY_ID[qs.id];
    if (!q || qs.done || qs.failed) continue;
    const c = q.condition;

    if (c.type === 'avoid_category' && (ctx.catCounts[c.categoryId] || 0) > 0) {
      qs.failed = true;
      changed = true;
      continue;
    }
    if (c.type === 'under_limit' && ctx.txCount > 0 && ctx.spent > S.dailyLimit) {
      qs.failed = true;
      changed = true;
      continue;
    }
    if (c.type === 'energy_left' && ctx.txCount > 0 && ctx.energy > c.target) {
      qs.failed = true;
      changed = true;
      continue;
    }

    if (evalQuest(q, ctx, settle)) {
      qs.done = true;
      changed = true;
      S.lifetimeQuests += 1;
      addCoins(q.rewards.coins);
      addXp(q.rewards.xp);
      toast(`📜 Квест выполнен: ${q.title} · +${q.rewards.coins} 🪙`);
      confettiBurst(10);
    }
  }
  if (changed && typeof renderQuests === 'function') renderQuests();
  return changed;
}

/* ---------------- achievements ---------------- */

function achMet(a) {
  const c = a.condition;
  const t = c.target || 1;
  switch (c.type) {
    case 'expense_count': return S.lifetimeExpenses >= t;
    case 'total_spent': return S.lifetimeSpent >= t;
    case 'log_streak': return S.bestLogStreak >= t;
    case 'budget_streak': return S.bestBudgetStreak >= t;
    case 'level': return levelInfo(S.totalXp).level >= t;
    case 'purchases': return S.purchasesCount >= t;
    case 'owned_items': return S.owned.length >= t;
    case 'work_sessions': return S.lifetimeWork >= t;
    case 'quests_completed': return S.lifetimeQuests >= t;
    case 'categories_used': return Object.keys(S.lifetimeCategories).length >= t;
    case 'coins_earned': return S.lifetimeCoinsEarned >= t;
    case 'energy_left_once': return S.minEnergyWithTx <= t;
    case 'no_category_streak': return S.bestCafeFreeStreak >= t;
    case 'comeback': return S.comebackDone === true;
    default: return false;
  }
}

function checkAchievements() {
  const newly = [];
  for (const a of ACHIEVEMENTS) {
    if (S.achievements.includes(a.id)) continue;
    if (achMet(a)) newly.push(a);
  }
  for (const a of newly) {
    S.achievements.push(a.id);
    addCoins(a.rewards.coins);
    addXp(a.rewards.xp);
    toast(`🏆 Достижение: ${a.title} · +${a.rewards.coins} 🪙`);
    confettiBurst(14);
  }
  if (newly.length && typeof renderAchievements === 'function') renderAchievements();
  return newly;
}

/* ---------------- day loop ---------------- */

function settleDay() {
  const streakBefore = S.logStreak;
  const energy = energyUsed();
  const within = S.tx.length > 0 && S.spent <= S.dailyLimit;

  checkQuests(true);

  S.health = clamp(S.health + CONFIG.energy.healthRegenDaily, 0, 100);

  if (S.tx.length > 0) {
    S.logStreak += 1;
    S.bestLogStreak = Math.max(S.bestLogStreak, S.logStreak);
  } else {
    S.logStreak = 0;
  }

  if (within) {
    S.budgetStreak += 1;
    S.bestBudgetStreak = Math.max(S.bestBudgetStreak, S.budgetStreak);
    S.health = clamp(S.health + CONFIG.energy.healthGainWithinLimit, 0, 100);
    addXp(CONFIG.xp.withinLimitBonus);
  } else {
    S.budgetStreak = 0;
    if (S.tx.length > 0) {
      const loss = Math.min(
        CONFIG.energy.healthLossMax,
        CONFIG.energy.healthLossOverspendBase
          + Math.round(Math.max(0, energy - 100) * CONFIG.energy.healthLossOverspendPerPct)
      );
      S.health = clamp(S.health - loss, 5, 100);
    }
  }

  const hadCafe = S.tx.some(t => t.categoryId === 'cafe');
  if (S.tx.length > 0 && !hadCafe) {
    S.cafeFreeStreak += 1;
    S.bestCafeFreeStreak = Math.max(S.bestCafeFreeStreak, S.cafeFreeStreak);
  } else if (S.tx.length > 0) {
    S.cafeFreeStreak = 0;
  }

  let weekly = 0;
  if (S.budgetStreak > 0 && S.budgetStreak % CONFIG.streak.weeklyBonusEvery === 0) {
    weekly = CONFIG.streak.weeklyBonusCoins;
    addCoins(weekly);
    addXp(CONFIG.xp.weeklyBonusXp);
  }

  const leftover = Math.floor(
    Math.max(0, CONFIG.energy.max - energy) * CONFIG.energy.leftoverEnergyToCoins
  );
  if (leftover > 0) addCoins(leftover);

  checkAchievements();

  const summary = {
    day: S.day,
    date: S.date,
    spent: S.spent,
    limit: S.dailyLimit,
    energy,
    within,
    streakBefore,
    streakAfter: S.logStreak,
    dayXp: S.dayXp,
    dayCoins: S.dayCoins,
    weekly,
    leftover,
    mood: currentMood(),
    txCount: S.tx.length
  };

  S.day += 1;
  S.date = addDays(S.date, 1);
  S.spent = 0;
  S.tx = [];
  S.workUsed = 0;
  S.logXpToday = 0;
  S.dayXp = 0;
  S.dayCoins = 0;
  S.petChecked = false;
  S.earlyLogged = false;
  S.endWarn = false;
  S.minEnergyWithTx = 999;
  S.quests = assignQuests();

  save();
  return summary;
}
