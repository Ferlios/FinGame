/* ============================================================
   События, модалки и мини-игра
   ============================================================ */

let selCat = null;

const workState = {
  running: false,
  timer: null,
  spawn: null,
  remaining: CONFIG.work.minigameSeconds,
  bonus: 0
};

/* ---------------- modals ---------------- */

function openModal(name) {
  if ($('#modal-work').classList.contains('open') && name !== 'work') stopWork();
  $$('.modal.open').forEach(m => m.classList.remove('open'));
  const modal = $('#modal-' + name);
  if (!modal) return;

  if (name === 'shop') { renderShopTabs(); renderShop(); }
  if (name === 'quests') renderQuests();
  if (name === 'ach') renderAchievements();
  if (name === 'settings') fillSettings();
  if (name === 'expense') resetExpenseForm();

  modal.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  stopWork();
  $$('.modal.open').forEach(m => m.classList.remove('open'));
  document.body.style.overflow = '';
}

/* ---------------- expense ---------------- */

function renderCatGrid() {
  const grid = $('#catGrid');
  if (!grid) return;
  grid.innerHTML = CATEGORIES.map(c => `
    <button class="catBtn ${selCat === c.id ? 'sel' : ''}" data-cat="${c.id}">
      <span>${c.icon}</span>${c.name}
    </button>`).join('');
}

function parseAmount(value) {
  return Math.round(Number(String(value).replace(/\s/g, '').replace(',', '.')) || 0);
}

function updateXpPreview() {
  const note = $('#noteInput') ? $('#noteInput').value.trim() : '';
  const base = CONFIG.xp.perExpense + CONFIG.xp.categoryBonus + (note ? CONFIG.xp.noteBonus : 0);
  const room = Math.max(0, CONFIG.xp.dailyLogCap - S.logXpToday);
  const gain = Math.min(base, room);
  const el = $('#xpPreview');
  if (!el) return;
  el.textContent = gain > 0
    ? `Запись даст ≈ +${gain} XP${note ? ' (с бонусом за заметку)' : ''}`
    : `Дневной лимит XP за записи исчерпан (${CONFIG.xp.dailyLogCap})`;
}

function resetExpenseForm() {
  selCat = null;
  $('#amountInput').value = '';
  $('#noteInput').value = '';
  renderCatGrid();
  updateXpPreview();
  setTimeout(() => $('#amountInput').focus(), 180);
}

function submitExpense() {
  const amount = parseAmount($('#amountInput').value);
  const result = addExpense(amount, selCat || 'other', $('#noteInput').value);
  if (!result.ok) {
    toast('⚠️ ' + result.error);
    return;
  }
  renderAll();
  renderShop();
  closeModal();
  toast(`−${fmt(result.amount)} ₽ · +${result.xp} XP`);
  if (result.energy > 100) {
    setBubble('Ой… мы вышли за лимит. Давай завтра аккуратнее.');
  } else if (result.energy > CONFIG.energy.happyMax) {
    setBubble('Энергия тает, но мы ещё держимся.');
  } else {
    setBubble('Записал! Так держать.');
  }
}

/* ---------------- shop ---------------- */

function handleShopResult(res) {
  if (!res.ok) {
    toast('⚠️ ' + res.error);
    return;
  }
  if (res.fed) {
    toast(`🍽 Вкусно! +${res.heal} ❤️`);
    setBubble('Спасибо, это было вкусно!');
  } else if (res.bought) {
    toast('🛍️ Покупка! Питомец доволен.');
    confettiBurst(12);
    setBubble('Ух, обновка! Спасибо!');
  } else if (res.equipped) {
    toast('✨ Образ обновлён');
  }
  renderAll();
  renderShop();
  renderAchievements();
}

/* ---------------- day loop ---------------- */

function onEndDay() {
  if (S.tx.length === 0 && !S.endWarn) {
    S.endWarn = true;
    const btn = $('#endDay');
    btn.classList.add('warn');
    btn.textContent = '⚠️ Стрик сгорит. Нажми ещё раз';
    toast('Нет записей за сегодня. Второе нажатие завершит день без стрика.');
    save();
    return;
  }
  const summary = settleDay();
  renderAll();
  renderShop();
  renderAchievements();
  showSummary(summary);
}

function showSummary(s) {
  $('#sumHero').textContent = s.within ? '🌟' : s.txCount === 0 ? '🌫️' : '🌧️';
  $('#sumTitle').textContent = `День ${s.day} завершён`;
  $('#sumSub').textContent = s.txCount === 0
    ? 'Без записей — стрик обнулился'
    : s.within
      ? 'Ты уложился в лимит'
      : 'Перерасход, но завтра новый день';

  const cells = [
    ['Потрачено', `${fmt(s.spent)} ₽`],
    ['Энергия', `${s.energy}%`],
    ['XP', `+${fmt(s.dayXp)}`],
    ['Монеты', `+${fmt(s.dayCoins)} 🪙`],
    ['Стрик', `🔥 ${s.streakAfter}`],
    ['Здоровье', `${Math.round(S.health)} ❤️`]
  ];
  $('#sumGrid').innerHTML = cells.map(([k, v]) =>
    `<div class="sumCell"><span>${k}</span><b>${v}</b></div>`
  ).join('');

  const notes = [];
  if (s.weekly) notes.push(`Недельный бонус: +${s.weekly} 🪙 и +${CONFIG.xp.weeklyBonusXp} XP.`);
  if (s.leftover) notes.push(`Сэкономленная энергия: +${s.leftover} 🪙.`);
  if (s.within) notes.push('Питомец доволен и восстановил здоровье.');
  else if (s.txCount > 0) notes.push('Питомец расстроен перерасходом — покорми его в магазине.');
  if (s.txCount > 0 && s.streakAfter > s.streakBefore) notes.push(`Стрик вырос: ${s.streakBefore} → ${s.streakAfter} 🔥`);
  $('#sumNote').textContent = notes.join(' ');

  openModal('summary');
}

/* ---------------- settings ---------------- */

function fillSettings() {
  $('#limitInput').value = S.dailyLimit;
  $('#settingsStreak').textContent = S.logStreak;
  $('#settingsHealth').textContent = Math.round(S.health);
}

function saveSettings() {
  const value = clamp(parseInt($('#limitInput').value, 10) || 1500, 300, 20000);
  S.dailyLimit = value;
  save();
  renderAll();
  closeModal();
  toast(`Лимит обновлён: ${fmt(value)} ₽`);
}

function onReset() {
  if (!confirm('Сбросить прогресс демо? Питомец начнёт заново.')) return;
  resetProgress();
  renderAll();
  renderShop();
  renderAchievements();
  closeModal();
  toast('Прогресс сброшен. Новый питомец ждёт!');
}

/* ---------------- work minigame ---------------- */

function openWork() {
  if (S.workUsed >= CONFIG.work.sessionsPerDay) {
    toast('Смены на сегодня закончились. Возвращайся завтра!');
    return;
  }
  resetWorkUI();
  openModal('work');
}

function resetWorkUI() {
  stopWork();
  $('#coinField').innerHTML = '';
  $('#workScore').textContent = '0';
  $('#workTimer').textContent = CONFIG.work.minigameSeconds.toFixed(1);
  $('#workOverlay').style.display = 'flex';
  $('#workOverlayTitle').textContent = 'Питомец готов к смене';
  $('#workOverlayText').textContent = 'Базовые монеты зависят от уровня и стрика. Успей поймать как можно больше монет.';
  $('#workResult').innerHTML = '';
  $('#workPet').textContent = PET_BY_ID[S.petId].icon;
  const btn = $('#workStartBtn');
  btn.style.display = '';
  btn.textContent = 'Начать смену';
  btn.dataset.mode = 'start';
}

function spawnCoin() {
  if (!workState.running) return;
  const field = $('#coinField');
  const coin = document.createElement('button');
  coin.type = 'button';
  coin.className = 'miniCoin';
  coin.textContent = '🪙';
  coin.style.left = (6 + Math.random() * 80) + '%';
  coin.style.top = (12 + Math.random() * 68) + '%';
  coin.addEventListener('click', () => {
    if (!workState.running) return;
    workState.bonus += 2;
    $('#workScore').textContent = workState.bonus;
    coin.remove();
  });
  field.appendChild(coin);
  setTimeout(() => coin.remove(), 1200);
}

function startWork() {
  if (workState.running) return;
  workState.running = true;
  workState.bonus = 0;
  workState.remaining = CONFIG.work.minigameSeconds;
  $('#workOverlay').style.display = 'none';
  $('#workScore').textContent = '0';
  $('#workTimer').textContent = workState.remaining.toFixed(1);
  spawnCoin();
  workState.spawn = setInterval(spawnCoin, 360);
  workState.timer = setInterval(() => {
    workState.remaining = Math.max(0, workState.remaining - 0.1);
    $('#workTimer').textContent = workState.remaining.toFixed(1);
    if (workState.remaining <= 0) endWork();
  }, 100);
}

function endWork() {
  if (!workState.running) return;
  workState.running = false;
  clearInterval(workState.timer);
  clearInterval(workState.spawn);
  $('#coinField').innerHTML = '';

  const res = finishWork(workState.bonus);
  renderAll();
  renderShop();
  renderAchievements();

  $('#workOverlay').style.display = 'flex';
  $('#workOverlayTitle').textContent = 'Смена окончена!';
  $('#workOverlayText').textContent = `База ${res.base} 🪙 + поймано ${res.bonus} 🪙`;
  $('#workResult').innerHTML = `<b>+${res.total} 🪙</b> и +${CONFIG.xp.workSessionXp} XP`;
  const btn = $('#workStartBtn');
  btn.textContent = 'Забрать';
  btn.dataset.mode = 'collect';
  confettiBurst(12);
  setBubble('Устал, но заработал!');
}

function stopWork() {
  clearInterval(workState.timer);
  clearInterval(workState.spawn);
  workState.running = false;
  const field = $('#coinField');
  if (field) field.innerHTML = '';
}

function onWorkStart() {
  const btn = $('#workStartBtn');
  if (btn.dataset.mode === 'collect') {
    closeModal();
    return;
  }
  startWork();
}

/* ---------------- events ---------------- */

function bindEvents() {
  $$('[data-modal]').forEach(btn => {
    btn.addEventListener('click', () => openModal(btn.dataset.modal));
  });
  document.addEventListener('click', e => {
    if (e.target.closest('[data-close]')) closeModal();
  });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeModal();
  });

  $('#achBtn').addEventListener('click', () => openModal('ach'));
  $('#settingsBtn').addEventListener('click', () => openModal('settings'));
  $('#workBtn').addEventListener('click', openWork);
  $('#endDay').addEventListener('click', onEndDay);
  $('#petWrap').addEventListener('click', onPet);
  $('#addExpenseBtn').addEventListener('click', submitExpense);
  $('#workStartBtn').addEventListener('click', onWorkStart);
  $('#saveSettings').addEventListener('click', saveSettings);
  $('#resetBtn').addEventListener('click', onReset);

  $('#quickAmounts').addEventListener('click', e => {
    const btn = e.target.closest('[data-amount]');
    if (!btn) return;
    $('#amountInput').value = btn.dataset.amount;
    updateXpPreview();
  });

  $('#catGrid').addEventListener('click', e => {
    const btn = e.target.closest('[data-cat]');
    if (!btn) return;
    selCat = btn.dataset.cat;
    renderCatGrid();
  });

  $('#amountInput').addEventListener('input', updateXpPreview);
  $('#noteInput').addEventListener('input', updateXpPreview);
  $('#amountInput').addEventListener('keydown', e => {
    if (e.key === 'Enter') submitExpense();
  });

  $('#shopTabs').addEventListener('click', e => {
    const tab = e.target.closest('[data-tab]');
    if (!tab) return;
    shopTab = tab.dataset.tab;
    renderShopTabs();
    renderShop();
  });

  $('#shopGrid').addEventListener('click', e => {
    const buy = e.target.closest('[data-buy]');
    if (buy && !buy.disabled) {
      handleShopResult(buyItem(buy.dataset.buy));
      return;
    }
    const pet = e.target.closest('[data-pet]');
    if (pet && !pet.disabled) {
      const res = buyPet(pet.dataset.pet);
      if (!res.ok) {
        toast('⚠️ ' + res.error);
        return;
      }
      toast(`🐾 Питомец: ${PET_BY_ID[pet.dataset.pet].name}`);
      renderAll();
      renderShop();
      renderAchievements();
    }
  });
}

function onPet() {
  const first = !S.petChecked;
  S.petChecked = true;
  if (first) {
    S.health = clamp(S.health + 1, 0, 100);
    toast('🐾 Питомец рад! +1 ❤️');
  }
  checkQuests(false);
  checkAchievements();
  save();
  renderAll();
  const phrase = BUBBLES[currentMood()][Math.floor(Math.random() * BUBBLES[currentMood()].length)];
  setBubble(phrase);
}

/* ---------------- init ---------------- */

function init() {
  S = loadState() || seedState();
  bindEvents();
  renderAll();
  renderShopTabs();
  renderShop();
  renderAchievements();
  setBubble(defaultBubble(), 7000);
  checkAchievements();
  save();
}

document.addEventListener('DOMContentLoaded', init);
