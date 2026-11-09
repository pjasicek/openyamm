(() => {
  'use strict';
  const data = window.REVIEW_CATALOG;
  const key = 'openyamm-mm8-art-review-v1';
  const reasons = ['identity', 'detail / pixels', 'placement', 'color', 'alpha / edge', 'state / animation', 'page seam', 'other'];
  const $ = selector => document.querySelector(selector);
  const escape = value => String(value ?? '').replace(/[&<>"']/g, character => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[character]));
  let review = {};
  try { review = JSON.parse(localStorage.getItem(key) || '{}'); } catch (_) { review = {}; }
  let matches = [];
  let visible = 48;
  const byId = new Map(data.items.map(item => [item.id, item]));

  function save() {
    try { localStorage.setItem(key, JSON.stringify(review)); } catch (_) { /* Export still works. */ }
  }
  function record(item) {
    const approval = item.review_approval;
    const local = review[item.id];
    if (local && (!approval || local.approval_revision === approval.revision)) return local;
    if (approval) return { decision: 'approve', reasons: [], note: '',
      candidate_index: item.candidates.findIndex(candidate => candidate.sha256 === approval.candidate_sha256),
      candidate_sha256: approval.candidate_sha256, source_sha256: item.source_sha256,
      approval_revision: approval.revision };
    return local || { decision: 'unreviewed', reasons: [], note: '', candidate_index: 0 };
  }
  function selectedCandidate(item) {
    const row = record(item);
    if (item.council_reference && row.decision === 'flag' && !row.variant_explicit
        && row.candidate_sha256 !== item.candidates[0]?.sha256) return item.candidates[0];
    return item.candidates.find(candidate => candidate.sha256 === row.candidate_sha256)
      || item.candidates[row.candidate_index || 0] || item.candidates[0] || null;
  }
  function effectiveDecision(item) {
    const row = record(item);
    const candidate = selectedCandidate(item);
    if (row.source_sha256 && row.source_sha256 !== item.source_sha256) return 'unreviewed';
    if (row.candidate_sha256 && row.candidate_sha256 !== candidate?.sha256) return 'unreviewed';
    if (row.decision === 'approve' && (!candidate || row.candidate_sha256 !== candidate.sha256)) return 'unreviewed';
    return row.decision || 'unreviewed';
  }
  function fillFilters() {
    const categories = [...new Set(data.items.map(item => item.category))].sort();
    const worlds = [...new Set(data.items.map(item => item.namespace))].sort();
    $('#category').innerHTML = '<option value="">All categories</option>' + categories.map(
      value => `<option value="${escape(value)}">${escape(value)} (${data.summary.by_category[value]})</option>`).join('');
    $('#world').innerHTML = '<option value="">All worlds</option>' + worlds.map(
      value => `<option value="${escape(value)}">${escape(value)}</option>`).join('');
  }
  function filter() {
    const search = $('#search').value.toLowerCase().trim();
    const category = $('#category').value;
    const world = $('#world').value;
    const artwork = $('#artwork').value;
    const decision = $('#decision').value;
    matches = data.items.filter(item => {
      if (category && item.category !== category) return false;
      if (world && item.namespace !== world) return false;
      if (artwork === 'candidate' && !item.candidates.length) return false;
      if (artwork === 'missing' && item.candidates.length) return false;
      if (artwork === 'pipeline' && item.pipeline_status !== 'accepted') return false;
      if (artwork === 'edge' && !item.quality_flags?.length) return false;
      if (artwork === 'council' && !item.council_reference) return false;
      if (decision && effectiveDecision(item) !== decision) return false;
      if (search && ![item.id, item.name, item.category, item.namespace, ...item.usage].join(' ').toLowerCase().includes(search)) return false;
      return true;
    });
    visible = 48;
    render();
  }
  function card(item) {
    const row = record(item);
    const candidate = selectedCandidate(item);
    const reference = item.council_reference && byId.get(item.council_reference.id);
    const referenceCandidate = reference?.candidates.find(
      entry => entry.sha256 === item.council_reference.candidate_sha256);
    const selectedIndex = item.candidates.indexOf(candidate);
    const decision = effectiveDecision(item);
    const fit = $('#zoom').value === 'fit';
    const zoom = fit ? 1 : Number($('#zoom').value);
    const width = Math.round(item.x2_size[0] * zoom);
    const height = Math.round(item.x2_size[1] * zoom);
    const fitClass = fit ? ' fit' : '';
    const badge = candidate ? (candidate.status === 'pipeline accepted'
      ? '<span class="badge accepted">Pipeline accepted</span>'
      : decision === 'approve' && item.review_approval?.candidate_sha256 === candidate.sha256
        ? '<span class="badge accepted">Art review approved</span>'
      : candidate.status === 'unverified mechanical edge cleanup'
        ? '<span class="badge ready">Edge cleaned · review needed</span>'
      : candidate.status === 'unverified council identity repair'
        ? '<span class="badge ready">Council identity repair · review needed</span>'
      : candidate.status.startsWith('unverified')
        ? '<span class="badge missing">Provisional 2× extraction</span>'
        : '<span class="badge ready">2× candidate · review needed</span>')
      : '<span class="badge missing">2× candidate pending</span>';
    const variants = item.candidates.length > 1 ? `<div class="variant">Candidate
      <select data-role="variant">${item.candidates.map((entry, index) =>
      `<option value="${index}" ${index === selectedIndex ? 'selected' : ''}>${escape(entry.source)} · ${escape(
        item.review_approval?.candidate_sha256 === entry.sha256 ? 'art review approved' : entry.status
      )}</option>`).join('')}</select></div>` : '';
    const source = `<a href="${escape(item.source)}" target="_blank" rel="noopener">Native bitmap</a>`;
    const candidateLink = candidate ? ` · <a href="${escape(candidate.path)}" target="_blank" rel="noopener">2× PNG</a>` : '';
    const rawPath = candidate?.raw || item.raw_master;
    const raw = rawPath ? ` · <a href="${escape(rawPath)}" target="_blank" rel="noopener">Raw master sheet</a>` : '';
    const referencePane = referenceCandidate ? `<div class="pane"><div class="pane-title"><span>Matching avatar</span><span>${escape(reference.name)}</span></div>
      <div class="stage"><img class="${fitClass}" loading="lazy" src="${escape(referenceCandidate.path)}"
      width="${Math.round(reference.x2_size[0] * zoom)}" height="${Math.round(reference.x2_size[1] * zoom)}"
      alt="Matching avatar ${escape(reference.name)}"></div></div>` : '';
    return `<article class="card" data-id="${escape(item.id)}" data-category="${escape(item.category)}" data-decision="${decision}">
      <div class="card-head"><div><h2>${escape(item.name)}</h2><div class="badges">
      <span class="badge">${escape(item.category)}</span><span class="badge">${escape(item.namespace)}</span>${badge}
      ${(item.quality_flags || []).map(flag => `<span class="badge missing">${escape(flag)}</span>`).join('')}</div></div>
      <div class="dimensions">${item.native_size.join('×')} → ${item.x2_size.join('×')}</div></div>
      ${variants}<div class="pair${referencePane ? ' council' : ''}"><div class="pane"><div class="pane-title"><span>Original · ${fit ? 'fit up to 2×' : `${zoom * 2}×`}</span><span>native</span></div>
      <div class="stage"><img class="original${fitClass}" loading="lazy" src="${escape(item.original)}" width="${width}" height="${height}" alt="Original ${escape(item.name)}"></div></div>
      <div class="pane"><div class="pane-title"><span>Restoration candidate</span><span>${candidate ? 'actual 2× PNG' : 'pending'}</span></div>
      <div class="stage">${candidate ? `<img class="${fitClass}" loading="lazy" src="${escape(candidate.path)}" width="${width}" height="${height}" alt="Restored ${escape(item.name)}">`
        : '<span class="pending">No individual 2× candidate is ready. Use the original and raw master link to flag this asset.</span>'}</div></div>${referencePane}</div>
      <div class="details">${escape(item.id)}<br>${source}${candidateLink}${raw}<br>
      ${escape(item.usage_status)} · restoration checkpoint: ${escape(item.pipeline_status)}${candidate ? ` · ${escape(candidate.source)} · ${escape(candidate.status)}` : ''}</div>
      <div class="review"><div class="review-row"><button data-action="approve" class="${decision === 'approve' ? 'selected' : ''}" ${candidate ? '' : 'disabled'}>Approve</button>
      <button data-action="flag" class="flag ${decision === 'flag' ? 'selected' : ''}">Flag</button>
      <button data-action="clear" class="clear">Clear</button><small>${decision === 'unreviewed' ? 'Not reviewed' : decision === 'approve'
        ? item.review_approval?.candidate_sha256 === candidate?.sha256 ? 'Art review approved' : 'Approved in browser'
        : 'Flagged in browser'}</small></div>
      <div class="reasons">${reasons.map(reason => `<label><input type="checkbox" data-reason="${escape(reason)}" ${row.reasons?.includes(reason) ? 'checked' : ''}>${escape(reason)}</label>`).join('')}</div>
      <textarea class="note" placeholder="What should change or be checked?">${escape(row.note || '')}</textarea></div></article>`;
  }
  function updateSummary() {
    const counts = { approve: 0, flag: 0 };
    data.items.forEach(item => { const decision = effectiveDecision(item); if (counts[decision] !== undefined) counts[decision]++; });
    $('#summary').textContent = `${matches.length} shown by filters · ${data.summary.total} total · ${data.summary.with_candidate} with individual 2× candidates · ${data.summary.without_candidate} awaiting candidates · ${counts.approve} approved here · ${counts.flag} flagged here`;
  }
  function render() {
    $('#cards').innerHTML = matches.slice(0, visible).map(card).join('');
    $('#more').hidden = visible >= matches.length;
    updateSummary();
  }
  function update(item, changes) {
    review[item.id] = { ...record(item), ...changes, source_sha256: item.source_sha256,
      approval_revision: item.review_approval?.revision || null };
    save();
    const cardElement = [...document.querySelectorAll('.card')].find(element => element.dataset.id === item.id);
    if (cardElement) cardElement.outerHTML = card(item);
    updateSummary();
  }
  function exportData() {
    const decisions = {};
    data.items.forEach(item => {
      const row = record(item);
      if (row.decision === 'unreviewed' && !row.note && !(row.reasons || []).length) return;
      const candidate = selectedCandidate(item);
      decisions[item.id] = {
        decision: effectiveDecision(item), reasons: row.reasons || [], note: row.note || '',
        candidate_index: item.candidates.indexOf(candidate),
        candidate_sha256: candidate?.sha256 || null,
        source_sha256: item.source_sha256,
        approval_revision: row.approval_revision || null,
      };
    });
    return JSON.stringify({ schema: 1, catalog_total: data.summary.total,
      exported_at: new Date().toISOString(), decisions }, null, 2);
  }
  function download() {
    const blob = new Blob([exportData()], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url; link.download = 'openyamm-mm8-art-review.json'; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  async function copy() {
    try { await navigator.clipboard.writeText(exportData()); $('#copy').textContent = 'Copied'; }
    catch (_) { download(); $('#copy').textContent = 'Downloaded'; }
    setTimeout(() => { $('#copy').textContent = 'Copy review'; }, 2200);
  }
  function large(item) {
    const candidate = selectedCandidate(item);
    const reference = item.council_reference && byId.get(item.council_reference.id);
    const referenceCandidate = reference?.candidates.find(
      entry => entry.sha256 === item.council_reference.candidate_sha256);
    const width = item.x2_size[0] * 2;
    $('#large-content').innerHTML = `<div><h2>Original · ${escape(item.name)}</h2><img class="original" src="${escape(item.original)}" width="${width}"></div>`
      + (candidate ? `<div><h2>2× candidate · ${escape(candidate.source)}</h2><img src="${escape(candidate.path)}" width="${width}"></div>` : '<div><h2>2× candidate pending</h2></div>')
      + (referenceCandidate ? `<div><h2>Matching avatar · ${escape(reference.name)}</h2><img src="${escape(referenceCandidate.path)}" width="${reference.x2_size[0] * 2}"></div>` : '');
    $('#large').showModal();
  }
  fillFilters();
  for (const selector of ['#search', '#category', '#world', '#artwork', '#decision']) $(selector).addEventListener('input', filter);
  for (const selector of ['#zoom', '#backdrop']) $(selector).addEventListener('input', () => {
    document.body.dataset.backdrop = $('#backdrop').value; render();
  });
  $('#more').addEventListener('click', () => { visible += 48; render(); });
  $('#download').addEventListener('click', download);
  $('#copy').addEventListener('click', copy);
  $('#close-large').addEventListener('click', () => $('#large').close());
  $('#import').addEventListener('change', async event => {
    const file = event.target.files[0]; if (!file) return;
    try {
      const imported = JSON.parse(await file.text());
      if (imported.schema !== 1 || typeof imported.decisions !== 'object') throw new Error('Unsupported review file');
      for (const [id, row] of Object.entries(imported.decisions)) {
        const item = byId.get(id);
        if (!item || row.source_sha256 !== item.source_sha256) continue;
        const matched = item.candidates.findIndex(candidate => candidate.sha256 === row.candidate_sha256);
        const index = matched >= 0 ? matched : Number(row.candidate_index || 0);
        const candidate = item.candidates[index] || null;
        if (row.decision === 'approve' && row.candidate_sha256 !== candidate?.sha256) continue;
        review[id] = { decision: row.decision, reasons: row.reasons || [], note: row.note || '',
          candidate_index: index, candidate_sha256: candidate?.sha256 || null,
          source_sha256: item.source_sha256, approval_revision: row.approval_revision || null };
      }
      save(); filter();
    } catch (error) { alert(`Could not import review: ${error.message}`); }
    event.target.value = '';
  });
  $('#cards').addEventListener('click', event => {
    const cardElement = event.target.closest('.card'); if (!cardElement) return;
    const item = byId.get(cardElement.dataset.id); if (!item) return;
    if (event.target.closest('.stage img')) { large(item); return; }
    const button = event.target.closest('button[data-action]'); if (!button) return;
    const action = button.dataset.action;
    if (action === 'clear') { update(item, { decision: 'unreviewed', reasons: [], note: '', candidate_sha256: null }); return; }
    const candidate = selectedCandidate(item);
    const previousCandidate = record(item).candidate_sha256;
    update(item, { decision: action, candidate_sha256: candidate?.sha256 || null,
      ...(action === 'approve' && previousCandidate && previousCandidate !== candidate?.sha256
        ? { reasons: [], note: '' } : {}) });
  });
  $('#cards').addEventListener('change', event => {
    const cardElement = event.target.closest('.card'); if (!cardElement) return;
    const item = byId.get(cardElement.dataset.id); if (!item) return;
    if (event.target.dataset.role === 'variant') {
      const index = Number(event.target.value);
      update(item, { candidate_index: index, decision: 'unreviewed', reasons: [],
        candidate_sha256: item.candidates[index]?.sha256 || null, variant_explicit: true });
    } else if (event.target.dataset.reason) {
      const values = [...cardElement.querySelectorAll('[data-reason]:checked')].map(input => input.dataset.reason);
      update(item, { reasons: values, decision: values.length ? 'flag' : record(item).decision });
    }
  });
  $('#cards').addEventListener('input', event => {
    if (!event.target.classList.contains('note')) return;
    const item = byId.get(event.target.closest('.card')?.dataset.id); if (!item) return;
    review[item.id] = { ...record(item), note: event.target.value,
      source_sha256: item.source_sha256,
      approval_revision: item.review_approval?.revision || null }; save();
  });
  document.body.dataset.backdrop = 'dark';
  if (new URLSearchParams(location.search).get('artwork') === 'council') $('#artwork').value = 'council';
  filter();
})();
