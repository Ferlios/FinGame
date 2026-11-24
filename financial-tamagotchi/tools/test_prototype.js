/* Быстрые проверки игровой логики без браузера.
   Запуск: node tools/test_prototype.js */

const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert');

const ROOT = path.resolve(__dirname, '..');
const files = ['prototype/data.js', 'prototype/game.js'];
const store = new Map();

const sandbox = {
  console,
  setTimeout,
  clearTimeout,
  localStorage: {
    getItem: k => (store.has(k) ? store.get(k) : null),
    setItem: (k, v) => store.set(k, String(v)),
    removeItem: k => store.delete(k)
  },
  toast: () => {},
  confettiBurst: () => {}
};
sandbox.globalThis = sandbox;
const ctx = vm.createContext(sandbox);

for (const file of files) {
  vm.runInContext(fs.readFileSync(path.join(ROOT, file), 'utf8'), ctx, { filename: file });
}

const run = code => vm.runInContext(code, ctx);

// 1. Стартовое состояние
run('S = seedState()');
let state = run('S');
assert.equal(state.day, 7);
assert.equal(state.coins, 640);
assert.equal(state.spent, 570);
assert.equal(run('levelInfo(S.totalXp).level'), 4);
assert.equal(run('energyUsed()'), 38);
assert.equal(run('currentMood()'), 'happy');

// 2. Трата: энергия, XP, квест, сохранение
const expense = run('addExpense(100, "cafe", "Тест")');
assert.equal(expense.ok, true);
assert.equal(expense.energy, 45);
assert.equal(run('S.spent'), 670);
assert.equal(run('S.tx.length'), 3);
assert.equal(run('S.lifetimeExpenses'), 69);
assert.ok(run('S.logXpToday') > 14);
assert.ok(store.size > 0);

// 3. Перерасход и здоровье при завершении дня
run('S.spent = 2200; S.tx = [{amount:2200, categoryId:"shopping", note:"", time:"12:00"}]');
let healthBefore = run('S.health');
let summary = run('settleDay()');
assert.equal(summary.within, false);
assert.equal(summary.energy, 147);
assert.ok(run('S.health') < healthBefore);
assert.equal(run('S.day'), 8);
assert.equal(run('S.spent'), 0);
assert.equal(run('S.tx.length'), 0);
assert.equal(run('S.quests.length'), 3);

// 4. Работа: 3 смены, четвёртая недоступна по счётчику
run('S.workUsed = 0; S.coins = 100');
const work = run('finishWork(8)');
assert.ok(work.total > 8);
assert.equal(run('S.workUsed'), 1);
run('finishWork(0); finishWork(0); S.workUsed = 3;');
assert.equal(run('S.workUsed'), 3);

// 5. Магазин: еда, предмет, повторное использование, уровень
run('S.coins = 1000; S.health = 50; S.owned = []; S.equipped = {hat:null, accessory:null, theme:null, furniture:[]}');
const fed = run('buyItem("food_apple")');
assert.equal(fed.ok, true);
assert.equal(fed.heal, 2);
assert.equal(run('S.health'), 52);
assert.equal(run('S.coins'), 985);

const bought = run('buyItem("hat_beanie")');
assert.equal(bought.ok, true);
assert.equal(run('S.owned.includes("hat_beanie")'), true);
assert.equal(run('S.equipped.hat'), 'hat_beanie');
const equipped = run('buyItem("hat_beanie")');
assert.equal(equipped.ok, true);
assert.equal(run('S.equipped.hat'), null);

// тема включается и снимается по повторному клику
run('S.coins = 1000; S.owned = []; S.equipped.theme = null');
assert.equal(run('buyItem("theme_cozy")').ok, true);
assert.equal(run('S.equipped.theme'), 'theme_cozy');
assert.equal(run('buyItem("theme_cozy")').ok, true);
assert.equal(run('S.equipped.theme'), null);

run('S.totalXp = 0; S.coins = 1000');
const locked = run('buyItem("hat_grad")');
assert.equal(locked.ok, false);
assert.match(locked.error, /уровн/i);

// 6. Питомцы
run('S.coins = 5000; S.totalXp = xpForLevel(12); S.ownedPets = ["moss"]');
const pet = run('buyPet("plusha")');
assert.equal(pet.ok, true);
assert.equal(run('S.petId'), 'plusha');
assert.equal(run('S.ownedPets.includes("plusha")'), true);

// 7. Достижения выдаются один раз
run('S.achievements = []; S.lifetimeExpenses = 1; S.coins = 0');
const ach = run('checkAchievements()');
assert.ok(ach.length >= 1);
const coinsAfter = run('S.coins');
const ach2 = run('checkAchievements()');
assert.equal(ach2.length, 0);
assert.equal(run('S.coins'), coinsAfter);

// 8. Сохранение/загрузка
run('S.coins = 777; save()');
assert.equal(run('loadState().coins'), 777);
run('resetProgress()');
assert.equal(run('S.coins'), 640);
assert.equal(run('S.day'), 7);

console.log('OK: 8 групп проверок игровой логики пройдены.');
