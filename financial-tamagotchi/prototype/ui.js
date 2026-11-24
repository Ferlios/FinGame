/* ============================================================
   Рендер интерфейса
   ============================================================ */

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
const fmt = n => new Intl.NumberFormat('ru-RU').format(Math.round(n));
const esc = s => String(s).replace(/[&<>"']/g, m => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
}[m]));

const RARITY = {
  common: { label: 'обычное', color: '#94a3b8' },
  rare: { label: 'редкое', color: '#38bdf8' },
  epic: { label: 'эпическое', color: '#c084fc' },
  legendary: { label: 'легендарное', color: '#fbbf24' }
};

let lastCoins = null;
let bubbleTimer = null;

const BUBBLES = {
  happy: ['Мне нравится, как мы сегодня держимся!', 'Ещё чуть-чуть — и будет красивый стрик.', 'Ты молодец. Погладь меня!'],
  neutral: ['Энергия тает. Давай без лишнего?', 'Я слегка волнуюсь за бюджет…', 'Может, обойдёмся без спонтанной покупки?'],
  sad: ['Мы вышли за лимит… но завтра новый день.', 'Я грущу. Давай вернёмся в норму?', 'Ничего, главное — не бросать учёт.'],
  sick: ['Мне бы полечиться… купи что-нибудь вкусное.', 'Я приболел. Позаботься обо мне?', 'Чувствую себя не очень. Может, яблочко?']
};

const defaultBubble = () => {
  const list = BUBBLES[currentMood()] || BUBBLES.happy;
  return list[Math.floor(Math.random() * list.length)];
};

function setBubble(text, ms = 5200) {
  const b = $('#bubble');
  if (!b) return;
  b.textContent = text;
  b.classList.remove('pop');
  void b.offsetWidth;
  b.classList.add('pop');
  clearTimeout(bubbleTimer);
  bubbleTimer = setTimeout(() => setBubble(defaultBubble(), ms), ms);
}

function toast(text) {
  const wrap = $('#toasts');
  if (!wrap) return;
  const el = document.createElement('div');
  el.className = 'toast';
  el.textContent = text;
  wrap.appendChild(el);
  setTimeout(() => {
    el.style.transition = 'opacity .25s, transform .25s';
    el.style.opacity = '0';
    el.style.transform = 'translateY(8px)';
    setTimeout(() => el.remove(), 260);
  }, 3000);
}

function confettiBurst(count = 16) {
  const layer = $('#confetti');
  if (!layer) return;
  const colors = ['#c084fc', '#f472b6', '#fbbf24', '#4ade80', '#38bdf8', '#fb7185'];
  for (let i = 0; i < count; i++) {
    const p = document.createElement('i');
    p.style.left = (10 + Math.random() * 80) + 'vw';
    p.style.background = colors[Math.floor(Math.random() * colors.length)];
    p.style.animationDelay = (Math.random() * 0.35) + 's';
    p.style.animationDuration = (1.3 + Math.random() * 0.9) + 's';
    p.style.transform = `rotate(${Math.random() * 360}deg)`;
    layer.appendChild(p);
    setTimeout(() => p.remove(), 2600);
  }
}

/* ---------------- header / room ---------------- */

function renderHeader() {
  const info = levelInfo(S.totalXp);
  $('#dayNum').textContent = S.day;
  $('#dateText').textContent = prettyDate(S.date);
  $('#coinNum').textContent = fmt(S.coins);
  $('#levelNum').textContent = info.level;
  $('#levelTitle').textContent = info.title;
  $('#xpFill').style.width = Math.min(100, info.progress * 100) + '%';
  $('#xpText').textContent = info.next
    ? `${fmt(info.into)} / ${fmt(info.next)} XP`
    : 'максимальный уровень';
  $('#streakNum').textContent = S.logStreak;
  $('#healthNum').textContent = Math.round(S.health);
  $('#healthFill').style.width = S.health + '%';

  const chip = $('#coinChip');
  if (lastCoins !== null && S.coins > lastCoins) {
    chip.classList.add('bump');
    setTimeout(() => chip.classList.remove('bump'), 200);
  }
  lastCoins = S.coins;
}

function applyTheme() {
  const item = SHOP_BY_ID[S.equipped.theme];
  const c = (item && item.colors) || {};
  const room = $('#room');
  room.style.setProperty('--wall', c.wall || '#3b2f4a');
  room.style.setProperty('--wall2', c.wall2 || '#57416b');
  room.style.setProperty('--floor', c.floor || '#2a2233');
  room.style.setProperty('--accentRoom', c.accent || '#f0abfc');
}

function speciesDecor(id, c, a) {
  switch (id) {
    case 'plusha':
      return `
        <path d="M56 76 L64 34 L94 62 Z" fill="${c}" stroke="${a}" stroke-width="3" stroke-linejoin="round"/>
        <path d="M144 76 L136 34 L106 62 Z" fill="${c}" stroke="${a}" stroke-width="3" stroke-linejoin="round"/>
        <path d="M66 66 L69 45 L85 61 Z" fill="#fbcfe8" opacity=".8"/>
        <path d="M134 66 L131 45 L115 61 Z" fill="#fbcfe8" opacity=".8"/>`;
    case 'iskra':
      return `
        <path d="M158 142 q36 8 26 38 q-10 -18 -30 -18" fill="${c}" stroke="${a}" stroke-width="3"/>
        <path d="M56 78 L60 32 L92 60 Z" fill="${c}" stroke="${a}" stroke-width="3" stroke-linejoin="round"/>
        <path d="M144 78 L140 32 L108 60 Z" fill="${c}" stroke="${a}" stroke-width="3" stroke-linejoin="round"/>
        <path d="M66 66 L68 44 L84 60 Z" fill="#fed7aa" opacity=".85"/>
        <path d="M134 66 L132 44 L116 60 Z" fill="#fed7aa" opacity=".85"/>`;
    case 'bublik':
      return `
        <circle cx="56" cy="64" r="16" fill="${c}" stroke="${a}" stroke-width="3"/>
        <circle cx="144" cy="64" r="16" fill="${c}" stroke="${a}" stroke-width="3"/>
        <circle cx="56" cy="64" r="8" fill="#fef3c7" opacity=".7"/>
        <circle cx="144" cy="64" r="8" fill="#fef3c7" opacity=".7"/>`;
    case 'kefir':
      return `
        <path d="M100 48 q-10 -16 2 -26 q10 10 2 26" fill="${a}" opacity=".8"/>
        <path d="M62 62 q-8 -12 4 -18 q10 6 6 18" fill="${c}" opacity=".55"/>
        <path d="M138 62 q8 -12 -4 -18 q-10 6 -6 18" fill="${c}" opacity=".55"/>`;
    case 'drak':
      return `
        <path d="M160 140 q34 10 22 34 q-8 -16 -26 -14" fill="${c}" stroke="${a}" stroke-width="3"/>
        <path d="M66 62 L60 28 L88 52 Z" fill="${a}"/>
        <path d="M134 62 L140 28 L112 52 Z" fill="${a}"/>
        <path d="M78 46 L82 30 L92 48 Z" fill="#bbf7d0" opacity=".8"/>
        <path d="M122 46 L118 30 L108 48 Z" fill="#bbf7d0" opacity=".8"/>`;
    default:
      return `
        <path d="M94 54 q-18 -20 -2 -30 q16 10 6 30" fill="${a}"/>
        <path d="M108 54 q18 -20 2 -30 q-16 10 -6 30" fill="${a}" opacity=".8"/>`;
  }
}

function petSvgMarkup(pet, stage, mood) {
  const c = stage.color;
  const a = stage.accent;
  const ink = '#2b1b3d';

  let eyes;
  if (mood === 'sick') {
    eyes = `
      <g stroke="${ink}" stroke-width="4.5" stroke-linecap="round">
        <path d="M73 95 l16 16 M89 95 l-16 16"/>
        <path d="M111 95 l16 16 M127 95 l-16 16"/>
      </g>`;
  } else if (mood === 'sad') {
    eyes = `
      <ellipse cx="82" cy="102" rx="6" ry="4.2" fill="${ink}"/>
      <ellipse cx="118" cy="102" rx="6" ry="4.2" fill="${ink}"/>
      <path d="M71 90 q11 -7 21 -1" stroke="${ink}" stroke-width="3" fill="none" stroke-linecap="round"/>
      <path d="M108 89 q10 -6 21 1" stroke="${ink}" stroke-width="3" fill="none" stroke-linecap="round"/>`;
  } else {
    eyes = `
      <circle cx="82" cy="100" r="7.2" fill="${ink}"/>
      <circle cx="118" cy="100" r="7.2" fill="${ink}"/>
      <circle cx="84.4" cy="97.4" r="2.3" fill="#fff" opacity=".92"/>
      <circle cx="120.4" cy="97.4" r="2.3" fill="#fff" opacity=".92"/>`;
  }

  const mouths = {
    happy: `<path d="M84 116 q16 15 32 0" stroke="${ink}" stroke-width="4" fill="none" stroke-linecap="round"/>`,
    neutral: `<path d="M88 121 q12 5 24 0" stroke="${ink}" stroke-width="4" fill="none" stroke-linecap="round"/>`,
    sad: `<path d="M84 129 q16 -14 32 0" stroke="${ink}" stroke-width="4" fill="none" stroke-linecap="round"/>`,
    sick: `<path d="M84 123 q8 -7 16 0 t16 0" stroke="${ink}" stroke-width="3.6" fill="none" stroke-linecap="round"/>`
  };

  const blush = mood === 'sad' || mood === 'sick'
    ? ''
    : `<ellipse cx="66" cy="116" rx="9" ry="5" fill="#fb7185" opacity=".26"/>
       <ellipse cx="134" cy="116" rx="9" ry="5" fill="#fb7185" opacity=".26"/>`;

  const sparkles = mood === 'happy'
    ? `<text x="150" y="72" font-size="14" opacity=".8">✦</text>
       <text x="38" y="94" font-size="9" opacity=".55">✦</text>`
    : '';

  return `
    <svg class="petSvg" viewBox="0 0 200 200" aria-hidden="true">
      <ellipse cx="100" cy="174" rx="54" ry="9" fill="rgba(0,0,0,.28)"/>
      ${speciesDecor(pet.id, c, a)}
      <ellipse cx="100" cy="112" rx="62" ry="56" fill="${c}"/>
      <ellipse cx="100" cy="128" rx="41" ry="33" fill="${a}" opacity=".22"/>
      <ellipse cx="100" cy="132" rx="26" ry="19" fill="#fff" opacity=".10"/>
      ${eyes}
      ${blush}
      ${mouths[mood] || mouths.happy}
      ${sparkles}
    </svg>`;
}

function renderRoom() {
  const { pet, stage } = petStage();
  const mood = currentMood();
  applyTheme();

  const furnitureIds = S.equipped.furniture || [];
  const positions = [
    { left: '7%', bottom: '12%', fontSize: '40px' },
    { right: '7%', bottom: '14%', fontSize: '36px' },
    { left: '12%', top: '26%', fontSize: '30px' }
  ];
  $('#furniture').innerHTML = furnitureIds.slice(0, 3).map((id, i) => {
    const item = SHOP_BY_ID[id];
    if (!item) return '';
    const p = positions[i] || positions[2];
    return `<span style="left:${p.left || 'auto'};right:${p.right || 'auto'};bottom:${p.bottom || 'auto'};top:${p.top || 'auto'};font-size:${p.fontSize}">${item.emoji}</span>`;
  }).join('');

  const hat = S.equipped.hat ? SHOP_BY_ID[S.equipped.hat] : null;
  const acc = S.equipped.accessory ? SHOP_BY_ID[S.equipped.accessory] : null;

  const wrap = $('#petWrap');
  wrap.className = `petWrap mood-${mood}`;
  wrap.innerHTML = `
    ${hat ? `<div class="hat">${hat.emoji}</div>` : ''}
    ${petSvgMarkup(pet, stage, mood)}
    ${acc ? `<div class="acc">${acc.emoji}</div>` : ''}`;

  $('#moodTag').textContent = CONFIG.energy.moodLabels[mood] || '';
}

/* ---------------- energy / quests / transactions ---------------- */

function renderEnergy() {
  const pct = energyUsed();
  const shown = Math.min(100, Math.max(0, pct));
  const bar = $('#energyBar');
  bar.classList.toggle('warn', pct > CONFIG.energy.happyMax && pct <= 100);
  bar.classList.toggle('over', pct > 100);
  $('#energyFill').style.width = shown + '%';
  $('#energyPct').textContent = pct + '%';
  $('#spentText').textContent = fmt(S.spent) + ' ₽';
  $('#limitText').textContent = fmt(S.dailyLimit) + ' ₽';
  const left = Math.max(0, S.dailyLimit - S.spent);
  $('#leftText').textContent = left > 0
    ? `Осталось ${fmt(left)} ₽`
    : `Перерасход ${fmt(S.spent - S.dailyLimit)} ₽`;
}

function questView(qs) {
  const q = QUEST_BY_ID[qs.id];
  if (!q) return null;
  const c = q.condition;
  const ctx = questCtx();
  let cur = 0;
  let tar = c.target || 1;
  let label = '';
  let bar = true;

  switch (c.type) {
    case 'log_count':
      cur = ctx.txCount; label = `${cur} из ${tar} трат`; break;
    case 'category_count':
      cur = ctx.catCounts[c.categoryId] || 0; label = `${cur} из ${tar}`; break;
    case 'note_count':
      cur = ctx.noteCount; label = `${cur} из ${tar} с заметкой`; break;
    case 'work_sessions':
      cur = ctx.workSessions; label = `${cur} из ${tar} смен`; break;
    case 'under_limit':
      cur = qs.failed ? 0 : (ctx.spent <= S.dailyLimit ? 1 : 0); tar = 1;
      label = qs.failed ? 'лимит превышен' : (ctx.spent <= S.dailyLimit ? 'пока в лимите' : '—');
      bar = false; break;
    case 'avoid_category':
      cur = qs.failed ? 0 : 1; tar = 1;
      label = qs.failed ? 'категория попала в траты' : (ctx.txCount ? 'пока чисто' : 'нужна хотя бы одна запись');
      bar = false; break;
    case 'energy_left':
      cur = Math.max(0, 100 - ctx.energy); tar = 100 - (c.target || 0);
      label = `${cur}% энергии сэкономлено`; break;
    case 'check_pet':
      cur = ctx.petChecked ? 1 : 0; tar = 1;
      label = ctx.petChecked ? 'питомец поглажен' : 'погладь питомца'; break;
    case 'early_log':
      cur = ctx.earlyLog ? 1 : 0; tar = 1;
      label = ctx.earlyLog ? 'до полудня' : 'запиши трату до 12:00'; break;
    case 'weekly_review':
      cur = 0; tar = 1; label = 'откроется в воскресенье'; bar = false; break;
  }

  const status = qs.done ? 'done' : qs.failed ? 'failed' : 'pending';
  const pct = Math.min(100, tar ? (cur / tar) * 100 : 0);
  return { q, cur, tar, label, bar, status, pct };
}

function questCard(qs) {
  const v = questView(qs);
  if (!v) return '';
  const icon = v.status === 'done' ? '✅' : v.status === 'failed' ? '✖️' : '⏳';
  return `
    <div class="quest ${v.status}">
      <div class="qIco">${v.q.icon}</div>
      <div class="qBody">
        <div class="qTitle">${v.q.title}</div>
        <div class="qDesc">${v.q.description}</div>
        ${v.bar ? `<div class="qBar"><i style="width:${v.pct}%"></i></div>` : ''}
        <div class="qDesc" style="margin-top:3px">${v.label}</div>
      </div>
      <div class="qReward">+${v.q.rewards.coins} 🪙<br><span style="color:var(--muted)">+${v.q.rewards.xp} XP</span></div>
      <div class="qStatus">${icon}</div>
    </div>`;
}

function renderQuests() {
  const html = S.quests.map(questCard).join('');
  const main = $('#questList');
  const full = $('#questListFull');
  if (main) main.innerHTML = html;
  if (full) full.innerHTML = html;

  const done = S.quests.filter(q => q.done).length;
  const hint = $('#questHint');
  if (hint) hint.textContent = `выполнено ${done} из ${S.quests.length}`;
  const left = $('#questLeft');
  if (left) left.textContent = `${done}/${S.quests.length}`;
}

function renderTx() {
  const list = $('#txList');
  if (!list) return;
  const count = $('#txCount');
  if (count) count.textContent = S.tx.length
    ? `${S.tx.length} ${S.tx.length === 1 ? 'запись' : S.tx.length < 5 ? 'записи' : 'записей'}`
    : 'пока пусто';

  if (!S.tx.length) {
    list.innerHTML = '<div class="empty">Сегодня ещё нет трат. Начни с любой записи — даже 100 ₽.</div>';
    return;
  }

  list.innerHTML = S.tx.map(t => {
    const cat = CAT_BY_ID[t.categoryId] || CAT_BY_ID.other;
    return `
      <div class="tx">
        <div class="tIco" style="background:${cat.color}22">${cat.icon}</div>
        <div class="tBody">
          <div class="tName">${esc(cat.name)}</div>
          <div class="tNote">${t.note ? esc(t.note) : t.time}</div>
        </div>
        <div class="tAmount">−${fmt(t.amount)} ₽</div>
      </div>`;
  }).join('');
}

function renderActions() {
  const left = $('#workLeft');
  if (left) left.textContent = `${Math.max(0, CONFIG.work.sessionsPerDay - S.workUsed)}/${CONFIG.work.sessionsPerDay}`;
  const done = S.quests.filter(q => q.done).length;
  const ql = $('#questLeft');
  if (ql) ql.textContent = `${done}/${S.quests.length}`;

  const btn = $('#endDay');
  if (btn && !S.endWarn) {
    btn.classList.remove('warn');
    btn.textContent = '🌙 Завершить день';
  }
}

function renderAll() {
  renderHeader();
  renderRoom();
  renderEnergy();
  renderQuests();
  renderTx();
  renderActions();
}

/* ---------------- shop ---------------- */

const SHOP_TABS = [
  { id: 'all', label: 'Всё' },
  { id: 'hat', label: 'Шляпы' },
  { id: 'accessory', label: 'Аксессуары' },
  { id: 'furniture', label: 'Мебель' },
  { id: 'theme', label: 'Темы' },
  { id: 'food', label: 'Еда' },
  { id: 'pet', label: 'Питомцы' }
];

let shopTab = 'all';

function renderShopTabs() {
  const wrap = $('#shopTabs');
  if (!wrap) return;
  wrap.innerHTML = SHOP_TABS.map(t =>
    `<button class="tab ${shopTab === t.id ? 'active' : ''}" data-tab="${t.id}">${t.label}</button>`
  ).join('');
}

function isEquipped(item) {
  if (item.slot === 'theme') return S.equipped.theme === item.id;
  if (item.slot === 'hat' || item.slot === 'accessory') return S.equipped[item.slot] === item.id;
  if (item.slot === 'furniture') return (S.equipped.furniture || []).includes(item.id);
  return false;
}

function shopItemCard(item) {
  const lvl = levelInfo(S.totalXp).level;
  const owned = S.owned.includes(item.id);
  const equipped = isEquipped(item);
  const locked = item.unlockLevel > lvl;
  const r = RARITY[item.rarity] || RARITY.common;

  let btnLabel = 'Купить';
  let btnClass = '';
  if (item.consumable) {
    btnLabel = `Съесть`;
  } else if (owned) {
    btnLabel = equipped ? 'Снять' : (item.slot === 'theme' ? 'Включить' : item.slot === 'furniture' ? 'Поставить' : 'Надеть');
    btnClass = equipped ? 'equipped' : '';
  }
  if (locked && !owned) { btnLabel = `LVL ${item.unlockLevel}`; btnClass = 'locked'; }

  return `
    <div class="shopItem ${owned && !item.consumable ? 'owned' : ''}">
      <span class="rarity r-${item.rarity}"></span>
      ${owned && !item.consumable ? '<span class="ownedMark">✓</span>' : ''}
      <div class="siIco">${item.emoji}</div>
      <div class="siName">${item.name}</div>
      <div class="siDesc">${item.description}</div>
      <div class="siBottom">
        <span class="siPrice">${owned && !item.consumable ? 'в коллекции' : `🪙 ${fmt(item.price)}`}</span>
        <button class="siBtn ${btnClass}" data-buy="${item.id}" ${locked && !owned ? 'disabled' : ''}>${btnLabel}</button>
      </div>
    </div>`;
}

function petCard(pet) {
  const lvl = levelInfo(S.totalXp).level;
  const owned = S.ownedPets.includes(pet.id);
  const selected = S.petId === pet.id;
  const locked = pet.unlockLevel > lvl && !owned;
  const r = RARITY[pet.rarity] || RARITY.common;
  const stage = pet.stages.filter(st => lvl >= st.level).pop() || pet.stages[0];

  return `
    <div class="shopItem ${selected ? 'owned' : ''}">
      <span class="rarity r-${pet.rarity}"></span>
      <div class="siIco">${pet.icon}</div>
      <div class="siName">${pet.name} · ${stage.name}</div>
      <div class="siDesc">${pet.description}</div>
      <div class="siBottom">
        <span class="siPrice">${owned ? 'в коллекции' : `🪙 ${fmt(pet.price)}`}</span>
        <button class="siBtn ${selected ? 'equipped' : ''} ${locked ? 'locked' : ''}"
          data-pet="${pet.id}" ${locked ? 'disabled' : ''}>
          ${selected ? 'Выбран' : owned ? 'Выбрать' : locked ? `LVL ${pet.unlockLevel}` : 'Купить'}
        </button>
      </div>
    </div>`;
}

function renderShop() {
  const grid = $('#shopGrid');
  if (!grid) return;
  const coins = $('#shopCoins');
  if (coins) coins.textContent = fmt(S.coins);

  if (shopTab === 'pet') {
    grid.innerHTML = PETS.map(petCard).join('');
    return;
  }

  const items = SHOP.filter(i => shopTab === 'all' ? true : i.category === shopTab);
  grid.innerHTML = items.map(shopItemCard).join('');
}

/* ---------------- achievements ---------------- */

function achCurrent(a) {
  const c = a.condition;
  switch (c.type) {
    case 'expense_count': return S.lifetimeExpenses;
    case 'total_spent': return S.lifetimeSpent;
    case 'log_streak': return S.bestLogStreak;
    case 'budget_streak': return S.bestBudgetStreak;
    case 'level': return levelInfo(S.totalXp).level;
    case 'purchases': return S.purchasesCount;
    case 'owned_items': return S.owned.length;
    case 'work_sessions': return S.lifetimeWork;
    case 'quests_completed': return S.lifetimeQuests;
    case 'categories_used': return Object.keys(S.lifetimeCategories).length;
    case 'coins_earned': return S.lifetimeCoinsEarned;
    case 'energy_left_once': return S.minEnergyWithTx;
    case 'no_category_streak': return S.bestCafeFreeStreak;
    case 'comeback': return S.comebackDone ? 1 : 0;
    default: return 0;
  }
}

function renderAchievements() {
  const grid = $('#achGrid');
  if (!grid) return;
  const count = $('#achCount');
  if (count) count.textContent = `${S.achievements.length} из ${ACHIEVEMENTS.length} открыто`;

  grid.innerHTML = ACHIEVEMENTS.map(a => {
    const on = S.achievements.includes(a.id);
    const cur = achCurrent(a);
    const target = a.condition.target || 1;
    const progress = a.condition.type === 'energy_left_once'
      ? (on ? 'выполнено' : 'потрать меньше половины лимита')
      : `${Math.min(cur, target)} / ${target}`;
    return `
      <div class="ach ${on ? 'on' : 'off'}">
        <div class="aIco">${a.icon}</div>
        <div class="aBody">
          <div class="aTitle">${a.title}</div>
          <div class="aDesc">${a.description}</div>
          <div class="aReward">${on ? '✓ получено' : progress} · +${a.rewards.coins} 🪙</div>
        </div>
      </div>`;
  }).join('');
}
