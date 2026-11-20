(() => {
  'use strict';
  const stage = window.SPELL_STAGE;
  const storageKey = stage.storage_key || 'openyamm-transparent-spell-stage-v1';
  const reasons = ['paper / matte', 'alpha / edge', 'glyph', 'identity', 'placement', 'paired state', 'detail', 'other'];
  const $ = selector => document.querySelector(selector);
  const escape = value => String(value ?? '').replace(/[&<>"']/g, character =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[character]);
  const items = new Map(stage.items.map(item => [item.id, item]));
  const pairs = new Map();
  stage.items.forEach(item => {
    if (!pairs.has(item.pair)) pairs.set(item.pair, []);
    pairs.get(item.pair).push(item);
  });
  const pairNames = [...pairs.keys()].sort();
  let review = {};
  try { review = JSON.parse(localStorage.getItem(storageKey) || '{}'); } catch (_) { review = {}; }
  let shown = 12;
  let matches = pairNames;

  function save() {
    try { localStorage.setItem(storageKey, JSON.stringify(review)); } catch (_) { /* Export still works. */ }
  }
  function reviewRow(item) {
    const row = review[item.id];
    if (row?.candidate_sha256 === item.candidate_sha256 && row?.source_sha256 === item.source_sha256
        && (!item.review_approval || row.approval_revision === item.review_approval.revision)) return row;
    if (item.review_approval) return { decision: 'approve', reasons: [], note: '',
      candidate_sha256: item.candidate_sha256, source_sha256: item.source_sha256,
      approval_revision: item.review_approval.revision };
    return null;
  }
  function decision(item) {
    return reviewRow(item)?.decision || 'unreviewed';
  }
  function school(pair) {
    return pair.replace(/[0-9].*$/, '');
  }
  function filters() {
    const prefixes = [...new Set(pairNames.map(school))].sort();
    $('#school').innerHTML = '<option value="">All schools</option>' + prefixes.map(prefix =>
      `<option value="${prefix}">${prefix.toUpperCase()} (${pairNames.filter(name => school(name) === prefix).length})</option>`).join('');
  }
  function record(item, changes) {
    review[item.id] = {
      ...reviewRow(item), ...changes, candidate_sha256: item.candidate_sha256,
      source_sha256: item.source_sha256, approval_revision: item.review_approval?.revision || null
    };
    save();
    render();
  }
  function stateCard(item) {
    const row = reviewRow(item) || {};
    const choice = decision(item);
    const zoom = $('#zoom').value;
    const width = item.x2_size[0] * (zoom === '2' ? 2 : 1);
    const stateName = item.state === 'a' ? 'Color / highlighted' : 'Sepia / normal';
    const stat = item.alpha;
    const panes = [
      ['Native original · shown at 2×', item.original],
      ['Prior 2× candidate', item.current],
      ['Transparent 2× stage', item.candidate]
    ].map(([label, path]) => `<div class="pane"><div class="pane-title">${escape(label)}</div>
      <div class="canvas"><img loading="lazy" src="${escape(path)}" width="${width}"
      data-image="${escape(item.id)}" alt="${escape(item.name)} ${escape(label)}"></div></div>`).join('');
    return `<section class="state" data-id="${escape(item.id)}">
      <div class="state-head"><h3>${escape(item.name)}</h3><span class="badge">${stateName}</span>
        <span class="badge">${escape(item.kind)}</span>
        ${item.review_approval && choice === 'approve' ? '<span class="badge">Art review approved</span>' : ''}
        <small>${item.native_size.join('×')} → ${item.x2_size.join('×')} · ${Math.round(stat.transparent_fraction * 100)}% fully transparent pixels</small></div>
      <div class="panes">${panes}</div>
      <div class="review"><button data-action="approve" class="${choice === 'approve' ? 'selected' : ''}">Approve</button>
        <button data-action="flag" class="flag ${choice === 'flag' ? 'selected' : ''}">Flag</button>
        <button data-action="clear">Clear</button>
        ${reasons.map(reason => `<label><input type="checkbox" data-reason="${escape(reason)}"
          ${row.reasons?.includes(reason) && choice !== 'unreviewed' ? 'checked' : ''}>${escape(reason)}</label>`).join('')}</div>
      <textarea class="note" placeholder="What should change or be checked?">${escape(choice === 'unreviewed' ? '' : row.note || '')}</textarea>
      <div class="links"><a href="${escape(item.candidate)}" target="_blank" rel="noopener">2× PNG</a>
        ${item.raw ? ` · <a href="${escape(item.raw)}" target="_blank" rel="noopener">raw edit sheet</a>` : ''}
        ${item.prompt ? ` · <a href="${escape(item.prompt)}" target="_blank" rel="noopener">edit prompt</a>` : ''}
        · candidate SHA-256 ${escape(item.candidate_sha256)}</div></section>`;
  }
  function pairCard(name) {
    const states = pairs.get(name);
    return `<article class="pair"><div class="pair-head"><h2>${escape(name)}</h2>
      <span class="badge">${escape(school(name).toUpperCase())}</span><span class="badge">paired states</span></div>
      ${states.map(stateCard).join('')}</article>`;
  }
  function updateSummary() {
    const counts = { approve: 0, flag: 0 };
    stage.items.forEach(item => { const choice = decision(item); if (choice in counts) counts[choice]++; });
    $('#summary').textContent = `${matches.length} pairs shown · ${stage.summary.pairs} pairs / ${stage.summary.states} states staged · `
      + `${stage.summary.new_sheet_edits} new transparent edits · ${stage.summary.accepted_air_ink} Air ink · `
      + `${stage.summary.retained} retained · ${counts.approve} approved here · ${counts.flag} flagged here`;
  }
  function render() {
    $('#pairs').classList.toggle('fit', $('#zoom').value === 'fit');
    $('#pairs').innerHTML = matches.slice(0, shown).map(pairCard).join('');
    $('#more').hidden = shown >= matches.length;
    updateSummary();
  }
  function filter() {
    const query = $('#search').value.toLowerCase().trim();
    const prefix = $('#school').value;
    const source = $('#source').value;
    const choice = $('#decision').value;
    matches = pairNames.filter(name => {
      const states = pairs.get(name);
      return (!query || name.includes(query) || states.some(item => item.id.toLowerCase().includes(query)))
        && (!prefix || school(name) === prefix)
        && (!source || states.some(item => item.kind === source))
        && (!choice || states.some(item => decision(item) === choice));
    });
    shown = 12;
    render();
  }
  function exportData() {
    const decisions = {};
    stage.items.forEach(item => {
      const row = reviewRow(item);
      if (!row || (!row.note && !row.reasons?.length && decision(item) === 'unreviewed')) return;
      decisions[item.id] = { decision: decision(item), reasons: row.reasons || [], note: row.note || '',
        candidate_sha256: item.candidate_sha256, source_sha256: item.source_sha256 };
    });
    return JSON.stringify({ schema: 1, stage: stage.stage, catalog_total: stage.summary.states,
      exported_at: new Date().toISOString(), decisions }, null, 2);
  }
  function download() {
    const url = URL.createObjectURL(new Blob([exportData()], { type: 'application/json' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = 'openyamm-transparent-spell-review.json';
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  function large(item) {
    const panes = [['Native original', item.original], ['Prior 2×', item.current], ['Transparent stage', item.candidate]];
    $('#large-content').innerHTML = panes.map(([label, path]) =>
      `<div><h2>${escape(label)} · ${escape(item.name)}</h2><img src="${escape(path)}"
      width="${item.x2_size[0] * 2}" alt="${escape(label)}"></div>`).join('');
    $('#large').showModal();
  }

  filters();
  const query = new URLSearchParams(location.search);
  if (query.has('search')) $('#search').value = query.get('search');
  if (query.has('school')) $('#school').value = query.get('school');
  if (query.get('source') === 'new') $('#source').value = 'new transparent sheet edit';
  ['#search', '#school', '#source', '#decision', '#zoom'].forEach(selector => $(selector).addEventListener('input', filter));
  $('#backdrop').addEventListener('input', () => { document.body.dataset.backdrop = $('#backdrop').value; });
  $('#more').addEventListener('click', () => { shown += 12; render(); });
  $('#download').addEventListener('click', download);
  $('#copy').addEventListener('click', async () => {
    try { await navigator.clipboard.writeText(exportData()); $('#copy').textContent = 'Copied'; }
    catch (_) { download(); $('#copy').textContent = 'Downloaded'; }
    setTimeout(() => { $('#copy').textContent = 'Copy review'; }, 2000);
  });
  $('#close-large').addEventListener('click', () => $('#large').close());
  $('#import').addEventListener('change', async event => {
    const file = event.target.files[0];
    if (!file) return;
    try {
      const data = JSON.parse(await file.text());
      if (data.schema !== 1 || data.stage !== stage.stage || !data.decisions) throw Error('Wrong review stage');
      Object.entries(data.decisions).forEach(([id, row]) => {
        const item = items.get(id);
        if (item && row.candidate_sha256 === item.candidate_sha256 && row.source_sha256 === item.source_sha256) {
          review[id] = { ...row, approval_revision: item.review_approval?.revision || null };
        }
      });
      save(); filter();
    } catch (error) { alert(`Could not import review: ${error.message}`); }
    event.target.value = '';
  });
  $('#pairs').addEventListener('click', event => {
    const section = event.target.closest('.state');
    if (!section) return;
    const item = items.get(section.dataset.id);
    if (event.target.matches('img[data-image]')) { large(item); return; }
    const button = event.target.closest('button[data-action]');
    if (!button) return;
    if (button.dataset.action === 'clear') {
      delete review[item.id]; save(); render(); return;
    }
    record(item, { decision: button.dataset.action, reasons: reviewRow(item)?.reasons || [],
      note: section.querySelector('.note').value });
  });
  $('#pairs').addEventListener('change', event => {
    const section = event.target.closest('.state');
    if (!section) return;
    const item = items.get(section.dataset.id);
    if (event.target.matches('input[data-reason]')) {
      const selected = [...section.querySelectorAll('input[data-reason]:checked')].map(input => input.dataset.reason);
      record(item, { decision: selected.length ? 'flag' : decision(item), reasons: selected,
        note: section.querySelector('.note').value });
    } else if (event.target.matches('.note')) {
      record(item, { decision: decision(item), reasons: reviewRow(item)?.reasons || [], note: event.target.value });
    }
  });
  filter();
})();
