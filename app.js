/* «Мій план» — веб-версія.
   Демонстраційна: усе живе в браузері, нічого не надсилається на сервер.
   Продукт навчання та роботи учасників «Освітнього простору №8». */
'use strict';

const DRAFT_KEY = 'plan-uvp8-draft';
const SCALE_KEY = 'plan-uvp8-scale';
const SCALES = [16, 18, 20];

// Постійна адреса: завжди веде на найсвіжіший реліз, міняти не треба.
const WIN_URL = 'https://github.com/Gregory-Ivd/plan-uvp8/releases/latest/download/plan-uvp8-windows.zip';

const WIN_WARNING = 'Програма не має цифрового підпису, тому під час першого запуску '
  + 'Windows покаже синє вікно «Система Windows захистила ваш комп\'ютер». '
  + 'Натисніть «Докладніше», далі «Виконати в будь-якому разі». Якщо архів не '
  + 'розпаковується — у властивостях файлу поставте позначку «Розблокувати». '
  + 'Так поводиться будь-яка непідписана програма.';

function downloadBlock(compact) {
  return `<div class="hint download" style="border-left-color:var(--orange)">
      <span class="label">Версія для Windows</span>
      <p style="margin-top:0">Працює без інтернету, запускається з флешки без встановлення.
         Додатково має редактор шаблону для адміністрації установи.</p>
      <p><a class="btn btn-primary" href="${WIN_URL}">Завантажити для Windows (≈24 МБ)</a></p>
      ${compact ? '' : `<p class="sub">${esc(WIN_WARNING)}</p>`}
    </div>`;
}

const TAB_COLORS = {
  green:  ['#E4F0E9', '#1E7A45'],
  blue:   ['#E3EAF4', '#15356B'],
  orange: ['#FBEBD6', '#A96400'],
  red:    ['#F6E4E3', '#98322B'],
  purple: ['#E8E6F1', '#4B3F73'],
  teal:   ['#E0EDEC', '#1F5F5B'],
  brown:  ['#EDE7DE', '#6B5433'],
};

/* ---------------- правила перевірки ---------------- */

const RUSSISMS = [
  ['на протязі всього', 'протягом усього'],
  ['на протязі', 'протягом'],
  ['у продовж', 'протягом'],
  ['прийняти участь', 'взяти участь'],
  ['приймати участь', 'брати участь'],
  ['поступив до', 'вступив до'],
  ['поступити до', 'вступити до'],
  ['зайняти перше місце', 'посісти перше місце'],
  ['відноситись до', 'ставитися до'],
  ['відношення до', 'ставлення до'],
  ['міроприємств', 'заходів'],
  ['міроприємства', 'заходи'],
  ['у якості', 'як'],
  ['згідно закону', 'згідно із законом'],
  ['не дивлячись на', 'попри'],
  ['співпадає', 'збігається'],
  ['в залежності від', 'залежно від'],
  ['на сьогоднішній день', 'сьогодні'],
  ['даний час', 'цей час'],
];

const PROCESS_STARTS = ['брати участь', 'приймати участь', 'проводити', 'відвідувати',
  'займатися', 'виконувати', 'здійснювати', 'продовжувати'];
const RESULT_MARKERS = ['маю', 'мав', 'досяг', 'опанував', 'здобув', 'закінчив', 'склав',
  'отримав', 'не маю', 'планую', 'хочу', 'зобов', 'стану', 'оформлю', 'результат', 'щоб', 'аби'];
const NO_OBSTACLE = ['не має', 'немає', 'нема', 'відсутні', 'відсутня', '-', '—', 'нет'];

/* ---------------- стан ---------------- */

let tpl = null;
let steps = [];
let index = 0;
const state = { header: {}, need: '', sections: {} };

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s == null ? '' : s)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const nl2br = (s) => esc(s).replace(/\n/g, '<br>');

/* ---------------- запуск ---------------- */

init();

async function init() {
  try {
    const res = await fetch('template.json', { cache: 'no-store' });
    tpl = await res.json();
  } catch (err) {
    $('screen').innerHTML = '<h1>Не вдалося завантажити шаблон</h1>' +
      '<p>Сторінку треба відкривати через веб-адресу, а не як локальний файл.</p>' +
      '<p class="sub">' + esc(String(err)) + '</p>';
    return;
  }

  (tpl.header_fields || []).forEach((f) => { state.header[f.id] = ''; });
  tpl.sections.forEach((s) => {
    state.sections[s.id] = { goals: '', term: '', obstacles: '', skipped: false };
  });

  steps = ['welcome', 'instruction', 'header']
    .concat(tpl.sections.map((s) => s.id))
    .concat(['review', 'preview', 'export']);

  applyScale(+localStorage.getItem(SCALE_KEY) || SCALES[0]);
  restoreDraft();

  $('btnBack').onclick = () => go(index - 1);
  $('btnNext').onclick = onNext;
  $('btnScale').onclick = cycleScale;
  $('btnReset').onclick = resetAll;
  $('demoClose').onclick = () => $('demoBar').classList.add('hidden');
  document.addEventListener('keydown', (e) => {
    if (e.altKey && e.key === 'ArrowRight') onNext();
    if (e.altKey && e.key === 'ArrowLeft') go(index - 1);
  });

  render();
}

/* ---------------- чернетка ---------------- */

function saveDraft() {
  try { localStorage.setItem(DRAFT_KEY, JSON.stringify(state)); } catch (e) { /* приватний режим */ }
}

function restoreDraft() {
  let raw;
  try { raw = localStorage.getItem(DRAFT_KEY); } catch (e) { return; }
  if (!raw) return;
  let data;
  try { data = JSON.parse(raw); } catch (e) { return; }
  const filled = (data.header && Object.values(data.header).some(Boolean))
    || (data.sections && Object.values(data.sections).some((s) => s.goals));
  if (!filled) return;
  if (!confirm('У цьому браузері збереглася незавершена чернетка. Продовжити з того місця?')) {
    localStorage.removeItem(DRAFT_KEY);
    return;
  }
  Object.assign(state.header, data.header || {});
  state.need = data.need || '';
  Object.keys(state.sections).forEach((id) => {
    if (data.sections && data.sections[id]) Object.assign(state.sections[id], data.sections[id]);
  });
}

function resetAll() {
  if (!confirm('Усе введене буде стерто. Продовжити?')) return;
  try { localStorage.removeItem(DRAFT_KEY); } catch (e) { /* ignore */ }
  Object.keys(state.header).forEach((k) => { state.header[k] = ''; });
  state.need = '';
  Object.keys(state.sections).forEach((id) => {
    state.sections[id] = { goals: '', term: '', obstacles: '', skipped: false };
  });
  index = 0;
  render();
}

/* ---------------- розмір тексту ---------------- */

function applyScale(px) {
  document.documentElement.style.setProperty('--fs', px + 'px');
  try { localStorage.setItem(SCALE_KEY, String(px)); } catch (e) { /* ignore */ }
}

function cycleScale() {
  const cur = +localStorage.getItem(SCALE_KEY) || SCALES[0];
  applyScale(SCALES[(SCALES.indexOf(cur) + 1) % SCALES.length] || SCALES[0]);
}

/* ---------------- навігація ---------------- */

function go(i) {
  collect();
  index = Math.max(0, Math.min(i, steps.length - 1));
  render();
  window.scrollTo(0, 0);
  $('screen').focus();
}

function onNext() {
  collect();
  if (steps[index] === 'review') {
    const blocking = check().filter((i) => i.level === 'block');
    if (blocking.length) {
      alert('Спершу виправте червоні пункти:\n\n'
        + blocking.slice(0, 6).map((i) => '• ' + i.where + ': ' + i.text).join('\n'));
      return;
    }
  }
  if (index < steps.length - 1) go(index + 1);
}

function isFilled(id) {
  const d = state.sections[id];
  return d.skipped || !!d.goals.trim();
}

function progress() {
  const total = tpl.sections.length;
  const done = tpl.sections.filter((s) => isFilled(s.id)).length;
  return [done, total];
}

/* ---------------- збір введеного ---------------- */

let collector = null;
function collect() { if (collector) collector(); }

/* ---------------- відображення ---------------- */

function render() {
  collector = null;
  const key = steps[index];
  const screen = $('screen');

  if (key === 'welcome') renderWelcome(screen);
  else if (key === 'instruction') renderInstruction(screen);
  else if (key === 'header') renderHeader(screen);
  else if (key === 'review') renderReview(screen);
  else if (key === 'preview') renderPreview(screen);
  else if (key === 'export') renderExport(screen);
  else renderSection(screen, tpl.sections.find((s) => s.id === key));

  const [done, total] = progress();
  $('progress').textContent = `Заповнено ${done} із ${total} розділів`;
  $('btnBack').disabled = index === 0;
  $('btnNext').style.display = key === 'export' ? 'none' : '';
  $('btnNext').textContent =
    key === 'welcome' ? 'Почати ›'
    : key === 'review' ? 'Дивитись чернетку ›'
    : key === 'preview' ? 'До вивантаження ›'
    : 'Далі ›';
  $('bottomHint').textContent =
    tpl.sections.some((s) => s.id === key) ? 'Порожній розділ можна пропустити галочкою' : '';
  renderSteps();
  saveDraft();
}

function renderSteps() {
  const box = $('steps');
  box.innerHTML = '';
  tpl.sections.forEach((s, i) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'step-dot'
      + (isFilled(s.id) ? ' done' : '')
      + (steps[index] === s.id ? ' current' : '');
    b.textContent = s.number;
    b.title = s.title;
    b.onclick = () => go(steps.indexOf(s.id));
    box.appendChild(b);
  });
}

function renderWelcome(el) {
  el.innerHTML = `
    <h1>${esc(tpl.app_title || 'Мій план')}</h1>
    <h2>${esc(tpl.doc_title)}</h2>
    <div class="card">
      <h3>Ця програма допоможе скласти власний план</h3>
      <p>Спочатку — коротка інструкція: що це за документ і на чому він ґрунтується.</p>
      <p>Потім ви заповните шапку і ${tpl.sections.length} розділів. У кожному розділі буде
         підказка й живий приклад.</p>
      <p>Наприкінці програма перевірить типові помилки, покаже чернетку і збереже готовий
         документ — його можна одразу роздрукувати.</p>
    </div>
    <div class="hint made-by">
      <img src="logo.png" alt="Логотип «Освітнього простору №8»">
      <div>
        <span class="label">Хто зробив цю програму</span>
        ${nl2br(tpl.made_by || '')}
      </div>
    </div>
    ${downloadBlock(true)}`;
}

function renderInstruction(el) {
  const blocks = (tpl.instruction && tpl.instruction.blocks) || [];
  el.innerHTML = '<h1>Коротка інструкція</h1>' + blocks.map((b) => `
    <div class="card">
      <h3>${esc(b.heading)}</h3>
      <p>${nl2br(b.text)}</p>
    </div>`).join('');
}

function renderHeader(el) {
  const need = tpl.need_field || {};
  el.innerHTML = `
    <h1>Шапка документа</h1>
    <h2>Так, як пишеться на паперовому бланку</h2>
    <div class="card">
      <div class="grid2">
        ${(tpl.header_fields || []).map((f) => `
          <div>
            <label class="field" for="h_${f.id}">${esc(f.label)}${f.required ? ' *' : ''}</label>
            <input type="text" id="h_${f.id}" value="${esc(state.header[f.id] || '')}">
            ${f.hint ? `<p class="sub">${esc(f.hint)}</p>` : ''}
          </div>`).join('')}
      </div>
    </div>
    <h2 style="margin-top:1.4rem">${esc(need.label || 'Криміногенна потреба')}</h2>
    ${need.hint ? `<div class="hint">${esc(need.hint)}</div>` : ''}
    <div class="card">
      <textarea id="needText">${esc(state.need)}</textarea>
    </div>
    ${need.example ? exampleHtml(need.example) : ''}`;

  collector = () => {
    (tpl.header_fields || []).forEach((f) => {
      const node = $('h_' + f.id);
      if (node) state.header[f.id] = node.value.trim();
    });
    const t = $('needText');
    if (t) state.need = t.value.trim();
  };
}

function exampleHtml(text) {
  return `<details class="example"><summary>Показати приклад</summary>
            <div class="body">${nl2br(text)}</div></details>`;
}

function renderSection(el, spec) {
  const data = state.sections[spec.id];
  const [chipBg, chipInk] = TAB_COLORS[spec.color] || TAB_COLORS.blue;

  el.innerHTML = `
    <span class="chip" style="background:${chipBg};color:${chipInk}">
      Розділ ${spec.number} із ${tpl.sections.length}
    </span>
    <h1 class="section-title" style="color:${chipInk}">${esc(spec.title)}</h1>
    ${spec.hint ? `<div class="hint"><span class="label">Що тут писати</span>${esc(spec.hint)}</div>` : ''}

    <div class="card" style="border-left-color:${chipInk}">
      <label class="field" for="goals">Проміжні цілі</label>
      <textarea id="goals">${esc(data.goals)}</textarea>
      <div class="counter" id="counter"></div>
    </div>
    ${spec.example ? exampleHtml(spec.example) : ''}
    ${(spec.avoid && spec.avoid.length) ? `<div class="avoid">Чого краще уникати:
      <ul>${spec.avoid.map((a) => `<li>${esc(a)}</li>`).join('')}</ul></div>` : ''}

    <div class="card" style="border-left-color:${chipInk}">
      <label class="field" for="term">Термін виконання</label>
      <input type="text" id="term" list="terms_${spec.id}" value="${esc(data.term)}">
      <datalist id="terms_${spec.id}">
        ${(spec.terms || []).map((t) => `<option value="${esc(t)}">`).join('')}
      </datalist>
      <p class="sub">Можна вибрати зі списку або написати свій.</p>
    </div>

    <div class="card" style="border-left-color:${chipInk}">
      <label class="field" for="obst">Перепони та їх можливе вирішення</label>
      ${spec.obstacles_hint ? `<p class="sub">${esc(spec.obstacles_hint)}</p>` : ''}
      <textarea id="obst" style="min-height:6.5rem">${esc(data.obstacles)}</textarea>
    </div>

    <label class="skip">
      <input type="checkbox" id="skip" ${data.skipped ? 'checked' : ''}>
      Цей розділ мене не стосується
    </label>`;

  const goals = $('goals');
  const counter = $('counter');
  const need = spec.min_chars || 0;
  const updateCounter = () => {
    const n = goals.value.trim().length;
    counter.textContent = need && n < need
      ? `${n} знаків — бажано хоча б ${need}` : `${n} знаків`;
    counter.className = 'counter' + (need && n < need ? ' short' : '');
  };
  goals.addEventListener('input', updateCounter);
  updateCounter();

  collector = () => {
    state.sections[spec.id] = {
      goals: goals.value.trim(),
      term: $('term').value.trim(),
      obstacles: $('obst').value.trim(),
      skipped: $('skip').checked,
    };
  };
}

/* ---------------- перевірка ---------------- */

function findRussisms(text) {
  const low = String(text || '').toLowerCase();
  const out = [];
  RUSSISMS.slice().sort((a, b) => b[0].length - a[0].length).forEach(([bad, good]) => {
    if (low.includes(bad) && !out.some(([f]) => f.includes(bad))) out.push([bad, good]);
  });
  return out;
}

function applyRussismFix(text, bad, good) {
  const re = new RegExp(bad.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
  return text.replace(re, (m) =>
    (m[0] === m[0].toUpperCase() ? good[0].toUpperCase() + good.slice(1) : good));
}

function check() {
  const issues = [];
  const add = (level, where, text, fix, sid) => issues.push({ level, where, text, fix, sid });

  (tpl.header_fields || []).forEach((f) => {
    if (f.required && !(state.header[f.id] || '').trim()) {
      add('block', 'Шапка документа', `Не заповнено поле «${f.label}».`);
    }
  });
  if (!state.need.trim()) {
    add('warn', 'Криміногенна потреба',
      'Блок «Криміногенна потреба» порожній. Це короткий зміст усього плану — комісія читає його першим.');
  }

  tpl.sections.forEach((spec) => {
    const d = state.sections[spec.id];
    const where = 'Розділ ' + spec.number;
    if (d.skipped) return;

    const goals = d.goals.trim();
    if (!goals) {
      add('block', where, 'Не заповнено «Проміжні цілі». Якщо розділ вас не стосується — '
        + 'позначте його галочкою.', null, spec.id);
      return;
    }
    if (spec.min_chars && goals.length < spec.min_chars) {
      add('warn', where, `Відповідь коротка (${goals.length} знаків). Для цього розділу варто `
        + `хоча б ${spec.min_chars}: додайте імена, назви, дати.`, null, spec.id);
    }
    if (!d.term.trim()) {
      add('warn', where, 'Не вказано «Термін виконання». Ціль без строку читається як намір без плану.',
        null, spec.id);
    }
    const low = goals.toLowerCase();
    if (PROCESS_STARTS.some((p) => low.startsWith(p)) && !RESULT_MARKERS.some((m) => low.includes(m))) {
      add('hint', where, 'Ціль сформульована як процес. Допишіть, якого результату хочете досягти: '
        + 'не «брати участь», а «опанував / маю / не маю».', null, spec.id);
    }
    if (spec.obstacles_required) {
      const obst = d.obstacles.trim();
      if (!obst) {
        add('warn', where, 'Не заповнено «Перепони та їх можливе вирішення».', null, spec.id);
      } else if (NO_OBSTACLE.includes(obst.toLowerCase().replace(/[.\s]+$/, ''))) {
        add('warn', where, 'У перепонах стоїть «Не має». Для цього розділу перепона зазвичай '
          + 'очевидна, і порожня клітинка читається як відписка. Напишіть, що заважає — і як ви це обходите.',
          null, spec.id);
      }
    }
    [['Проміжні цілі', goals], ['Термін виконання', d.term], ['Перепони', d.obstacles]]
      .forEach(([name, text]) => {
        findRussisms(text).forEach(([bad, good]) => {
          add('hint', where, `У полі «${name}»: «${bad}» → «${good}».`, [bad, good], spec.id);
        });
      });
  });

  return issues;
}

function renderReview(el) {
  const issues = check();
  const [done, total] = progress();
  const counts = { block: 0, warn: 0, hint: 0 };
  issues.forEach((i) => { counts[i.level] += 1; });

  if (!issues.length) {
    el.innerHTML = `<h1>Перевірка</h1>
      <p style="color:var(--green-ink);font-weight:600">
        Заповнено ${done} із ${total} розділів. Зауважень немає — можна дивитись чернетку.</p>`;
    return;
  }

  const label = { block: 'Треба виправити', warn: 'Варто подумати', hint: 'Дрібниця' };
  const order = { block: 0, warn: 1, hint: 2 };

  el.innerHTML = `<h1>Перевірка</h1>
    <p>Заповнено ${done} із ${total} розділів. Знайдено: ${counts.block} треба виправити,
       ${counts.warn} варто подумати, ${counts.hint} дрібниць.</p>
    <div class="hint">Виправити обов'язково потрібно лише червоні пункти.
       Решта — поради: ви маєте право написати по-своєму.</div>
    <div id="issues"></div>`;

  const box = $('issues');
  issues.sort((a, b) => order[a.level] - order[b.level]).forEach((issue) => {
    const div = document.createElement('div');
    div.className = 'card issue ' + issue.level;
    div.innerHTML = `<div class="head"><b>${esc(label[issue.level])} · ${esc(issue.where)}</b></div>
                     <p>${esc(issue.text)}</p>`;
    if (issue.fix) {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'btn btn-secondary btn-small';
      b.textContent = 'Виправити';
      b.onclick = () => {
        const d = state.sections[issue.sid];
        ['goals', 'term', 'obstacles'].forEach((k) => {
          d[k] = applyRussismFix(d[k], issue.fix[0], issue.fix[1]);
        });
        saveDraft();
        render();
      };
      div.querySelector('.head').appendChild(b);
    } else if (issue.sid) {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'btn btn-secondary btn-small';
      b.textContent = 'Перейти';
      b.onclick = () => go(steps.indexOf(issue.sid));
      div.querySelector('.head').appendChild(b);
    }
    box.appendChild(div);
  });
}

/* ---------------- чернетка тексту ---------------- */

function asText() {
  const out = [tpl.doc_title.toUpperCase(), ''];
  out.push('Засудженого ' + titleLine());
  const [a, b] = period();
  out.push(`на період з ${a || '___'} по ${b || '___'}`, '');
  out.push(((tpl.need_field || {}).label || 'Криміногенна потреба').toUpperCase());
  out.push(state.need.trim() || '(не заповнено)', '');
  [['during', 'НАМІРИ ТА ПЛАНИ ПІД ЧАС ВІДБУВАННЯ ПОКАРАННЯ'],
   ['after', 'НАМІРИ ТА ПЛАНИ ПІСЛЯ ЗВІЛЬНЕННЯ']].forEach(([group, caption]) => {
    const specs = tpl.sections.filter((s) => s.group === group);
    if (!specs.length) return;
    out.push('='.repeat(70), caption, '='.repeat(70), '');
    specs.forEach((spec) => {
      const d = state.sections[spec.id];
      if (d.skipped && !d.goals.trim()) return;
      out.push(`${spec.number}. ${spec.title}`);
      out.push('   Проміжні цілі: ' + (d.goals.trim() || '(порожньо)'));
      out.push('   Термін: ' + (d.term.trim() || '(порожньо)'));
      out.push('   Перепони: ' + (d.obstacles.trim() || '(порожньо)'), '');
    });
  });
  return out.join('\n');
}

function renderPreview(el) {
  el.innerHTML = `<h1>Чернетка</h1>
    <p>Це весь текст майбутнього документа. Прочитайте вголос — так найкраще видно
       незграбні місця.</p>
    <div class="preview">${esc(asText())}</div>`;
}

/* ---------------- сам документ ---------------- */

function titleLine() {
  const pib = (state.header.pib || '').trim();
  const birth = (state.header.birth || '').trim();
  if (pib && birth) return `${pib}, ${birth} року народження`;
  return pib || '___________________________';
}

function period() {
  return [(state.header.date_from || '').trim(), (state.header.date_to || '').trim()];
}

function safeName() {
  const pib = (state.header.pib || 'Без імені').trim();
  return pib.split(/\s+/).slice(0, 3).join(' ').replace(/[<>:"/\\|?*]/g, '') || 'План';
}

function docHtml() {
  const [from, to] = period();
  const needLabel = (tpl.need_field || {}).label || 'Криміногенна потреба';
  const rows = [];

  const band = (text) => rows.push(`<tr><td class="band" colspan="5">${esc(text)}</td></tr>`);
  const block = (g, t, o) => {
    rows.push(`<tr><td></td><td>Проміжні цілі</td><td>${nl2br(g)}</td>`
      + `<td class="term">${nl2br(t)}</td><td></td></tr>`);
    rows.push('<tr><td></td><td></td><td></td><td></td><td></td></tr>');
    rows.push(`<tr><td></td><td>Перепони та їх можливе вирішення</td><td>${nl2br(o)}</td>`
      + '<td></td><td></td></tr>');
    rows.push('<tr><td></td><td></td><td></td><td></td><td></td></tr>');
  };

  [['during', 'Наміри та плани засудженого під час відбування кримінального покарання'],
   ['after', 'Наміри та плани засудженого після звільнення']].forEach(([group, caption]) => {
    const specs = tpl.sections.filter((s) => s.group === group);
    if (!specs.length) return;
    band(caption);
    specs.forEach((spec) => {
      const d = state.sections[spec.id];
      if (d.skipped && !d.goals.trim()) return;
      band(`${spec.number}. ${spec.title}`);
      block(d.goals.trim(), d.term.trim(), d.obstacles.trim());
    });
  });

  const signLine = '______________________________________________   ____ ____________ 20___ р.';

  return `<div class="doc">
    <h1>${esc(tpl.doc_title)}</h1>
    <p class="center"><b>Засудженого</b> <u>${esc(titleLine())}</u></p>
    <p class="tiny">(прізвище, власне ім'я, по батькові (за наявності))</p>
    <p class="center"><b>на період з</b> <u>${esc(from) || '______________'}</u>
       <b>по</b> <u>${esc(to) || '______________'}</u></p>

    <table>
      <tr><th>${esc(needLabel)}</th></tr>
      <tr><td>${nl2br(state.need.trim())}</td></tr>
    </table>

    <table>
      <tr>
        <th style="width:8%">Мета/цілі</th>
        <th style="width:14%">Цілі</th>
        <th style="width:50%">Поступові заходи, здійснення яких дадуть змогу зменшити/усунути актуальні фактори ризику</th>
        <th style="width:14%">Термін виконання</th>
        <th style="width:14%">Отриманий результат (виконано, внесено зміни)</th>
      </tr>
      ${rows.join('\n')}
    </table>

    <div class="sign">
      <p>План розробив ${signLine}</p>
      <p class="tiny">(підпис, власне ім'я та прізвище начальника відділення СПС)</p>
      <p>План розробив ${signLine}</p>
      <p class="tiny">(підпис, власне ім'я та прізвище засудженого)</p>
    </div>

    <table style="margin-top:10pt">
      <tr><th>Висновки щодо результатів реалізації індивідуального плану виправлення та ресоціалізації</th></tr>
      <tr><td><br><br><br></td></tr>
    </table>

    <div class="sign">
      <p>Начальник відділення СПС ______________________________   ____ ____________ 20___ р.</p>
      <p class="tiny">(підпис, власне ім'я та прізвище)</p>
      <p>Ознайомлений ___________________________________________   ____ ____________ 20___ р.</p>
      <p class="tiny">(підпис, власне ім'я та прізвище засудженого)</p>
    </div>
  </div>`;
}

function doPrint() {
  $('printArea').innerHTML = docHtml();
  window.print();
}

function downloadDoc() {
  const css = `
    body{font-family:"Times New Roman",serif;font-size:11pt}
    h1{text-align:center;font-size:13pt;margin:0 0 8pt}
    .center{text-align:center}.tiny{font-size:8pt;text-align:center}
    table{border-collapse:collapse;width:100%;margin-bottom:6pt}
    td,th{border:1px solid #000;padding:2pt 3pt;font-size:10pt;vertical-align:top}
    th{text-align:center}
    td.band{font-weight:bold;text-align:left;background:#F0F0F0}
    td.term{text-align:center}`;
  const html = '<html xmlns:o="urn:schemas-microsoft-com:office:office" '
    + 'xmlns:w="urn:schemas-microsoft-com:office:word" xmlns="http://www.w3.org/TR/REC-html40">'
    + '<head><meta charset="utf-8"><title>' + esc(tpl.doc_title) + '</title>'
    + '<style>@page{size:21cm 29.7cm;margin:1.5cm 1cm}' + css + '</style></head><body>'
    + docHtml() + '</body></html>';

  const blob = new Blob(['﻿', html], { type: 'application/msword' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = safeName() + ' — індивідуальний план.doc';
  document.body.appendChild(a);
  a.click();
  setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 2000);
}

function renderExport(el) {
  el.innerHTML = `<h1>Готово</h1>
    <p>Оберіть, у якому вигляді забрати документ.</p>
    <div class="card">
      <div class="btn-row">
        <button type="button" class="btn btn-primary" id="btnPrint">Друк або збереження в PDF</button>
        <button type="button" class="btn btn-secondary" id="btnWord">Завантажити файл для Word</button>
      </div>
      <p class="sub">У вікні друку оберіть принтер або «Зберегти як PDF».</p>
      <div class="status" id="exportStatus"></div>
    </div>
    <div class="hint">
      <span class="label">Що далі</span>
      Роздрукуйте документ і підпишіть його від руки. Другий підпис ставить начальник
      відділення СПС. Рамку «Висновки щодо результатів реалізації» заповнюють у кінці
      періоду — вона має лишитися порожньою.
    </div>
    ${downloadBlock(false)}`;

  $('btnPrint').onclick = () => {
    doPrint();
    $('exportStatus').textContent = 'Відкрито вікно друку.';
  };
  $('btnWord').onclick = () => {
    downloadDoc();
    $('exportStatus').textContent = 'Файл для Word завантажено.';
  };
}
