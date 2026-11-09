(() => {
  'use strict';
  const catalog = window.REMAINING_ART_CATALOG;
  const baseline = window.REMAINING_USER_REVIEW?.decisions || {};
  const keptEffects = window.KEPT_EFFECT_ACCEPTANCE?.decisions || {};
  const accepted = { ...(window.REMAINING_ART_ACCEPTANCE?.decisions || {}), ...keptEffects };
  const effectIds = new Set(window.REMAINING_ART_ACCEPTANCE?.pending_effect_ids || []);
  const effectOnly = new URLSearchParams(location.search).get('effects') === '1';
  const storageKey = 'openyamm-remaining-ui-art-review-v5';
  let earlierBrowser = {};
  try { earlierBrowser = JSON.parse(localStorage.getItem('openyamm-remaining-ui-art-review-v1') || '{}'); }
  catch (_) { earlierBrowser = {}; }
  let secondBrowser = {};
  try { secondBrowser = JSON.parse(localStorage.getItem('openyamm-remaining-ui-art-review-v2') || '{}'); }
  catch (_) { secondBrowser = {}; }
  let thirdBrowser = {};
  try { thirdBrowser = JSON.parse(localStorage.getItem('openyamm-remaining-ui-art-review-v3') || '{}'); }
  catch (_) { thirdBrowser = {}; }
  let fourthBrowser = {};
  try { fourthBrowser = JSON.parse(localStorage.getItem('openyamm-remaining-ui-art-review-v4') || '{}'); }
  catch (_) { fourthBrowser = {}; }
  const history = { ...baseline, ...earlierBrowser, ...secondBrowser, ...thirdBrowser, ...fourthBrowser };
  const earlier = { ...history, ...accepted };
  const reasons = ['identity', 'detail / pixels', 'crop / placement', 'color', 'alpha / edge',
    'state / animation', 'needs extraction', 'other'];
  const pageSize = 36;
  const $ = selector => document.querySelector(selector);
  const escape = value => String(value ?? '').replace(/[&<>"']/g, character => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[character]));
  let review = {};
  try { review = JSON.parse(localStorage.getItem(storageKey) || '{}'); } catch (_) { review = {}; }
  let matches = [];
  let page = 1;
  const byId = new Map(catalog.items.map(item => [item.id, item]));

  function save() {
    try { localStorage.setItem(storageKey, JSON.stringify(review)); } catch (_) { /* Export remains available. */ }
  }
  function record(item) {
    if (review[item.id]) return review[item.id];
    const prior = earlier[item.id];
    const first = item.candidates[0];
    if (!prior || prior.source_sha256 !== item.source_sha256)
      return { decision: 'unreviewed', reasons: [], note: '', candidate_index: 0,
        candidate_sha256: first?.sha256 || null };
    if (prior.candidate_sha256 !== first?.sha256)
      return { decision: 'unreviewed', reasons: [], note: prior.decision === 'unreviewed' ? prior.note : '',
        candidate_index: 0, candidate_sha256: first?.sha256 || null };
    return prior;
  }
  function selectedCandidate(item) {
    const row = record(item);
    return item.candidates.find(candidate => candidate.sha256 === row.candidate_sha256)
      || item.candidates[row.candidate_index || 0] || item.candidates[0] || null;
  }
  function effectiveDecision(item) {
    const row = record(item);
    if (row.source_sha256 && row.source_sha256 !== item.source_sha256) return 'unreviewed';
    const candidate = selectedCandidate(item);
    if (row.candidate_sha256 && row.candidate_sha256 !== candidate?.sha256) return 'unreviewed';
    if (row.decision === 'approve' && (!candidate || row.candidate_sha256 !== candidate.sha256)) return 'unreviewed';
    return row.decision || 'unreviewed';
  }
  function fillCategories() {
    $('#category').innerHTML = '<option value="">All six categories</option>' + Object.entries(
      catalog.summary.by_category).map(([name, count]) =>
      `<option value="${escape(name)}">${escape(name)} (${count})</option>`).join('');
  }
  function fillFamilies() {
    const category = $('#category').value;
    const previous = $('#family').value;
    const counts = new Map();
    for (const item of catalog.items) {
      if (category && item.category !== category) continue;
      counts.set(item.family, (counts.get(item.family) || 0) + 1);
    }
    $('#family').innerHTML = '<option value="">All families</option>' + [...counts].sort((a, b) =>
      a[0].localeCompare(b[0], undefined, { numeric: true })).map(([family, count]) =>
      `<option value="${escape(family)}">${escape(family)} (${count})</option>`).join('');
    if (counts.has(previous)) $('#family').value = previous;
  }
  function filter(reset = true) {
    const search = $('#search').value.toLowerCase().trim();
    const category = $('#category').value;
    const family = $('#family').value;
    const artwork = $('#artwork').value;
    const duplicates = $('#duplicates').value;
    const decision = $('#decision').value;
    matches = catalog.items.filter(item => {
      if (effectOnly && !effectIds.has(item.id)) return false;
      if (category && item.category !== category) return false;
      if (family && item.family !== family) return false;
      const candidate = selectedCandidate(item);
      if (artwork === 'sheet' && !['Measured retained-sheet extraction', 'Measured extraction']
        .includes(candidate?.origin)) return false;
      if (artwork === 'imagegen' && !item.imagegen_slice) return false;
      if (artwork === 'review' && !item.review_repair) return false;
      if (artwork === 'sequence' && !item.sequence_repair) return false;
      if (artwork === 'world' && !(item.world_master?.source_rgb_correlation >= 0.9)) return false;
      if (artwork === 'repair' && !['Transparent hourglass master', 'Cleaned UI control cutout',
        'Cleaned cyan-backed indicator', 'Transparent small-hourglass restoration',
        'Edited hourglass animation repair'].includes(candidate?.origin)) return false;
      if (artwork === 'earlier' && candidate?.origin !== 'Second-pass selection') return false;
      if (artwork === 'reuse' && !['accepted_duplicate', 'pending_duplicate'].includes(candidate?.kind)) return false;
      if (duplicates === 'unique' && item.duplicate_group_id !== item.id) return false;
      if (duplicates === 'accepted' && !item.accepted_duplicate) return false;
      if (duplicates === 'pending' && !item.review_siblings.length) return false;
      if (decision && effectiveDecision(item) !== decision) return false;
      if (search && ![item.id, item.name, item.family, item.category, item.namespace].join(' ')
        .toLowerCase().includes(search)) return false;
      return true;
    });
    if (reset) page = 1;
    page = Math.max(1, Math.min(page, Math.max(1, Math.ceil(matches.length / pageSize))));
    render();
  }
  function card(item) {
    const row = record(item);
    const candidate = selectedCandidate(item);
    const decision = effectiveDecision(item);
    const selectedIndex = item.candidates.indexOf(candidate);
    const fit = $('#zoom').value === 'fit';
    const zoom = fit ? 1 : Number($('#zoom').value);
    const width = Math.round(item.x2_size[0] * zoom);
    const height = Math.round(item.x2_size[1] * zoom);
    const fitClass = fit ? ' fit' : '';
    const status = candidate?.kind === 'approved_world_master'
      ? '<span class="badge ready">Approved ground master · fitted inventory art</span>'
      : candidate?.kind === 'accepted_duplicate'
      ? '<span class="badge ready">Approved copy · reuse review</span>'
      : candidate?.kind === 'pending_duplicate'
        ? '<span class="badge ready">Exact original · shared candidate</span>'
      : candidate ? '<span class="badge ready">Fitted 2× candidate</span>'
      : item.raw ? '<span class="badge raw">Raw sheet only</span>'
        : '<span class="badge missing">No direct return</span>';
    const duplicateBadges = item.review_siblings.length
      ? `<span class="badge">Exact original ×${item.review_siblings.length + 1}</span>` : '';
    const variants = item.candidates.length > 1 ? `<div class="variant">Candidate
      <select data-role="variant">${item.candidates.map((entry, index) =>
      `<option value="${index}" ${index === selectedIndex ? 'selected' : ''}>${escape(entry.origin)} · ${escape(entry.status)} · ${entry.sha256.slice(0, 8)}</option>`).join('')}
      </select></div>` : '';
    const candidateView = candidate
      ? `<img class="${fitClass}" loading="lazy" src="${escape(candidate.path)}" width="${width}" height="${height}" alt="2× candidate for ${escape(item.name)}">`
      : item.raw?.preview
        ? `<img class="raw-image" loading="lazy" src="${escape(item.raw.preview)}" alt="Unfitted raw sheet locator for ${escape(item.name)}">`
      : '<span class="pending">No individual 2× restoration is ready for visual acceptance.</span>';
    const rightTitle = candidate ? 'Restoration candidate' : item.raw ? 'Unfitted raw master locator' : 'Restoration pending';
    const rightSize = candidate ? 'actual 2× PNG' : item.raw
      ? item.raw.projected ? 'approximate slot' : 'full raw sheet' : 'no return';
    const rawLink = item.raw ? ` · <a href="${escape(item.raw.master)}" target="_blank" rel="noopener">Full raw master</a>` : '';
    const candidateLink = candidate ? ` · <a href="${escape(candidate.path)}" target="_blank" rel="noopener">2× PNG</a>` : '';
    const existing = item.existing_note ? `<details class="existing-note"><summary>Earlier technical note · ${escape(item.existing_status || 'review')}</summary>${escape(item.existing_note)}</details>` : '';
    const prior = history[item.id];
    const priorFlag = prior?.decision === 'flag' && prior.candidate_sha256 !== candidate?.sha256
      ? `<details class="existing-note"><summary>Earlier flag on previous candidate</summary>
          ${escape((prior.reasons || []).join(', ') || 'flagged')}${prior.note ? ` · ${escape(prior.note)}` : ''}
          ${prior.candidate_sha256 ? ` · ${escape(prior.candidate_sha256.slice(0, 12))}` : ''}</details>` : '';
    const acceptedDuplicate = item.accepted_duplicate
      ? `<div class="duplicate-note">Native pixels also belong to approved ${escape(item.accepted_duplicate.donor_id)}
      (${escape(item.accepted_duplicate.approval)}). Its 2× art is offered above for separate review of this target.</div>` : '';
    const siblings = item.review_siblings.length
      ? `<div class="duplicate-note">Same native original in this review: ${item.review_siblings.map(id =>
        `<a href="?item=${encodeURIComponent(id)}">${escape(byId.get(id)?.name || id)}</a>`).join(', ')}.</div>` : '';
    const world = item.world_master;
    const worldMaster = world ? `<div class="world-master">
      ${world.world_path ? `<a href="${escape(world.world_path)}" target="_blank" rel="noopener">
        <img loading="lazy" src="${escape(world.world_path)}" alt="Approved ground sprite ${escape(world.sprite_name)}"></a>` : ''}
      <div>Ground sprite <strong>${escape(world.sprite_name)}</strong> · ${escape(world.reuse_status)}.
      ${world.candidate_sha256 ? 'Its approved 2× pixels are available in the candidate selector.' : ''}
      <br>Native drawing correlation ${escape(world.source_rgb_correlation)}.
      ${world.world_path ? `<a href="${escape(world.world_path)}" target="_blank" rel="noopener">Open approved ground PNG</a>` : ''}</div>
      </div>` : '';
    return `<article class="card" data-id="${escape(item.id)}" data-decision="${decision}">
      <div class="card-head"><div><h2>${escape(item.name)}</h2><div class="badges">
      <span class="badge">${escape(item.category)}</span><span class="badge">${escape(item.namespace)}</span>
      <span class="badge">${escape(item.family)}</span>${status}${duplicateBadges}</div></div>
      <div class="dimensions">${item.native_size.join('×')} → ${item.x2_size.join('×')}</div></div>
      ${variants}<div class="pair"><div class="pane"><div class="pane-title"><span>Original · ${fit ? 'fit up to 2×' : `${zoom * 2}×`}</span><span>native</span></div>
      <div class="stage"><img class="original${fitClass}" loading="lazy" src="${escape(item.original)}" width="${width}" height="${height}" alt="Native original ${escape(item.name)}"></div></div>
      <div class="pane"><div class="pane-title"><span>${rightTitle}</span><span>${rightSize}</span></div>
      <div class="stage">${candidateView}</div></div></div>
      <div class="details">${escape(item.id)}<br><a href="${escape(item.source)}" target="_blank" rel="noopener">Native bitmap</a>${candidateLink}${rawLink}<br>
      Checkpoint: ${escape(item.pipeline_status)}${candidate ? ` · ${escape(candidate.origin)} · ${escape(candidate.status)}` : ''}
      ${worldMaster}${acceptedDuplicate}${siblings}${priorFlag}${candidate?.note ? `<details class="existing-note"><summary>Candidate note</summary>${escape(candidate.note)}</details>` : ''}${existing}</div>
      <div class="review"><div class="review-row"><button data-action="approve" class="${decision === 'approve' ? 'selected' : ''}" ${candidate ? '' : 'disabled'}>Accept 2×</button>
      <button data-action="flag" class="flag ${decision === 'flag' ? 'selected' : ''}">Flag</button>
      <button data-action="clear" class="clear">Clear</button><small>${decision === 'unreviewed' ? 'Pending your review' : decision === 'approve' ? 'Accepted' : 'Flagged in this browser'}</small></div>
      <div class="reasons">${reasons.map(reason => `<label><input type="checkbox" data-reason="${escape(reason)}" ${row.reasons?.includes(reason) ? 'checked' : ''}>${escape(reason)}</label>`).join('')}</div>
      <textarea class="note" placeholder="What should change or be checked?">${escape(row.note || '')}</textarea></div></article>`;
  }
  function updateSummary() {
    let approved = 0;
    let flagged = 0;
    for (const item of catalog.items) {
      const decision = effectiveDecision(item);
      if (decision === 'approve') approved++;
      if (decision === 'flag') flagged++;
    }
    $('#summary').textContent = `${matches.length} match filters · ${catalog.summary.total} targets · ${catalog.summary.with_candidate} with fitted 2× art · ${catalog.summary.imagegen_slice_candidates} new imagegen-slice candidates · ${catalog.summary.pending_reuse_candidates} shared pending candidates · ${catalog.summary.accepted_reuse_candidates} approved copies offered · ${catalog.summary.raw_only + catalog.summary.no_return} still without candidate · ${approved} accepted · ${flagged} flagged here`;
  }
  function render() {
    $('#cards').innerHTML = matches.slice((page - 1) * pageSize, page * pageSize).map(card).join('');
    const count = Math.max(1, Math.ceil(matches.length / pageSize));
    $('#page').value = page;
    $('#page').max = count;
    $('#page-count').textContent = `of ${count}`;
    $('#previous').disabled = page <= 1;
    $('#next').disabled = page >= count;
    updateSummary();
  }
  function update(item, changes) {
    review[item.id] = { ...record(item), ...changes, source_sha256: item.source_sha256 };
    save();
    const cardElement = [...document.querySelectorAll('.card')].find(element => element.dataset.id === item.id);
    if (cardElement) cardElement.outerHTML = card(item);
    updateSummary();
  }
  function exportData() {
    const decisions = {};
    for (const item of catalog.items) {
      const row = record(item);
      if (row.decision === 'unreviewed' && !row.note && !(row.reasons || []).length) continue;
      const candidate = selectedCandidate(item);
      decisions[item.id] = {
        decision: effectiveDecision(item), reasons: row.reasons || [], note: row.note || '',
        candidate_index: row.candidate_index ?? item.candidates.indexOf(candidate),
        candidate_sha256: row.candidate_sha256 || null,
        source_sha256: row.source_sha256 || item.source_sha256,
        ...(effectiveDecision(item) !== row.decision ? { previous_decision: row.decision } : {}),
      };
    }
    return JSON.stringify({ schema: 1, scope: 'remaining_ui_art', catalog_total: catalog.summary.total,
      exported_at: new Date().toISOString(), decisions }, null, 2);
  }
  function download() {
    const blob = new Blob([exportData()], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'openyamm-remaining-ui-art-review.json';
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  async function copy() {
    try { await navigator.clipboard.writeText(exportData()); $('#copy').textContent = 'Copied'; }
    catch (_) { download(); $('#copy').textContent = 'Downloaded'; }
    setTimeout(() => { $('#copy').textContent = 'Copy review'; }, 2200);
  }
  function large(item) {
    const candidate = selectedCandidate(item);
    const width = item.x2_size[0] * 2;
    const alternate = candidate
      ? `<div><h2>Individual 2× candidate</h2><img src="${escape(candidate.path)}" width="${width}" alt="2× candidate"></div>`
      : item.raw?.preview
        ? `<div><h2>Unfitted raw sheet locator</h2><img class="raw-image" src="${escape(item.raw.preview)}" alt="Raw sheet locator"></div>`
        : '<div><h2>Restoration pending</h2></div>';
    const world = item.world_master?.world_path
      ? `<div><h2>Approved ground sprite · ${escape(item.world_master.sprite_name)}</h2>
          <img src="${escape(item.world_master.world_path)}" alt="Approved ground sprite"></div>` : '';
    $('#large-content').innerHTML = `<div><h2>Original · ${escape(item.name)}</h2><img class="original" src="${escape(item.original)}" width="${width}" alt="Native original"></div>${alternate}${world}`;
    $('#large').showModal();
  }

  fillCategories();
  fillFamilies();
  for (const selector of ['#search', '#family', '#artwork', '#duplicates', '#decision']) $(selector).addEventListener('input', () => filter());
  $('#category').addEventListener('input', () => { fillFamilies(); filter(); });
  for (const selector of ['#zoom', '#backdrop']) $(selector).addEventListener('input', () => {
    document.body.dataset.backdrop = $('#backdrop').value;
    render();
  });
  $('#previous').addEventListener('click', () => { page--; render(); window.scrollTo(0, 0); });
  $('#next').addEventListener('click', () => { page++; render(); window.scrollTo(0, 0); });
  $('#page').addEventListener('change', () => { page = Number($('#page').value) || 1; filter(false); window.scrollTo(0, 0); });
  $('#download').addEventListener('click', download);
  $('#copy').addEventListener('click', copy);
  $('#close-large').addEventListener('click', () => $('#large').close());
  $('#import').addEventListener('change', async event => {
    const file = event.target.files[0];
    if (!file) return;
    try {
      const imported = JSON.parse(await file.text());
      if (imported.schema !== 1 || imported.scope !== 'remaining_ui_art' || !imported.decisions)
        throw new Error('Unsupported review file');
      for (const [id, row] of Object.entries(imported.decisions)) {
        const item = byId.get(id);
        if (!item || row.source_sha256 !== item.source_sha256) continue;
        const matched = item.candidates.findIndex(candidate => candidate.sha256 === row.candidate_sha256);
        const index = matched >= 0 ? matched : Number(row.candidate_index ?? -1);
        review[id] = { decision: row.decision, reasons: row.reasons || [], note: row.note || '',
          candidate_index: index, candidate_sha256: row.candidate_sha256 || null,
          source_sha256: item.source_sha256 };
      }
      save(); filter();
    } catch (error) { alert(`Could not import review: ${error.message}`); }
    event.target.value = '';
  });
  $('#cards').addEventListener('click', event => {
    const cardElement = event.target.closest('.card');
    if (!cardElement) return;
    const item = byId.get(cardElement.dataset.id);
    if (!item) return;
    if (event.target.closest('.stage img')) { large(item); return; }
    const button = event.target.closest('button[data-action]');
    if (!button) return;
    const action = button.dataset.action;
    if (action === 'clear') {
      update(item, { decision: 'unreviewed', reasons: [], note: '', candidate_sha256: null });
      return;
    }
    const candidate = selectedCandidate(item);
    if (action === 'approve' && !candidate) return;
    update(item, { decision: action, candidate_sha256: candidate?.sha256 || null });
  });
  $('#cards').addEventListener('change', event => {
    const cardElement = event.target.closest('.card');
    if (!cardElement) return;
    const item = byId.get(cardElement.dataset.id);
    if (!item) return;
    if (event.target.dataset.role === 'variant') {
      const index = Number(event.target.value);
      update(item, { candidate_index: index, candidate_sha256: item.candidates[index]?.sha256 || null,
        decision: 'unreviewed' });
    } else if (event.target.dataset.reason) {
      const values = [...cardElement.querySelectorAll('[data-reason]:checked')].map(input => input.dataset.reason);
      update(item, { reasons: values, decision: values.length ? 'flag' : record(item).decision,
        candidate_sha256: selectedCandidate(item)?.sha256 || null });
    }
  });
  $('#cards').addEventListener('input', event => {
    if (!event.target.classList.contains('note')) return;
    const item = byId.get(event.target.closest('.card')?.dataset.id);
    if (!item) return;
    review[item.id] = { ...record(item), note: event.target.value, source_sha256: item.source_sha256 };
    save();
  });
  document.body.dataset.backdrop = 'dark';
  const requestedId = new URLSearchParams(location.search).get('item');
  if (new URLSearchParams(location.search).get('repairs') === '1') {
    $('#artwork').value = 'review';
    $('#duplicates').value = '';
  }
  if (new URLSearchParams(location.search).get('sequences') === '1') {
    $('#artwork').value = 'sequence';
    $('#duplicates').value = '';
  }
  if (new URLSearchParams(location.search).get('world') === '1') {
    $('#artwork').value = 'world';
    $('#duplicates').value = '';
  }
  if (effectOnly) {
    $('#duplicates').value = '';
  }
  if (requestedId && byId.has(requestedId)) $('#search').value = requestedId;
  filter();
})();
