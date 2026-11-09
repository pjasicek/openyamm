(() => {
  'use strict';

  const catalog = window.SPRITE_REVIEW_CATALOG || window.DECORATION_CATALOG;
  const changesetReview = catalog && catalog.schema === 'openyamm.sprite_changeset_browser.v1';
  const remainingReview = catalog && catalog.schema === 'openyamm.sprite_review_browser.v1';
  const groups = catalog ? (catalog.groups || catalog.decorations) : [];
  const noun = changesetReview ? 'candidates' : remainingReview ? 'sprites' : 'decorations';
  const categories = [
    ['not_authentic', 'Not authentic'],
    ['pixelated', 'Pixelated'],
    ['proportions', 'Wrong proportions'],
    ['anchor', 'Floating / anchor'],
    ['alpha', 'Alpha / edges'],
    ['animation', 'Animation'],
    ['color', 'Color / lighting'],
    ['other', 'Other'],
  ];
  const storageKey = changesetReview ? 'openyamm-sprite-changeset-flags-v3'
    : remainingReview ? 'openyamm-remaining-sprite-review-flags-v1' : 'openyamm-decoration-review-flags-v1';
  const batchSize = 24;
  const cardsElement = document.getElementById('cards');
  const sentinel = document.getElementById('load-more');
  const search = document.getElementById('search');
  const filter = document.getElementById('filter');
  const categoryFilter = document.getElementById('category-filter');
  const background = document.getElementById('background');
  const playAll = document.getElementById('play-all');
  const rotateViews = document.getElementById('rotate-views');
  const progress = document.getElementById('progress');
  const empty = document.getElementById('empty');
  const flagCount = document.getElementById('flag-count');
  const exportDialog = document.getElementById('export-dialog');
  const exportText = document.getElementById('export-json');
  const copyStatus = document.getElementById('copy-status');
  let flags = loadFlags();
  let filtered = [];
  let cursor = 0;
  let searchTimer = 0;
  const activeCards = new Set();

  if (!catalog || !['openyamm.decoration_browser.v1', 'openyamm.sprite_review_browser.v1',
    'openyamm.sprite_changeset_browser.v1'].includes(catalog.schema)) {
    empty.hidden = false;
    empty.textContent = 'Catalog missing or outdated. Run the catalog builder listed in README.md.';
    return;
  }

  const cardObserver = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      const card = entry.target.reviewCard;
      if (!card) continue;
      card.visible = entry.isIntersecting;
      if (card.visible) {
        card.lastTick = 0;
        activeCards.add(card);
        updateCanvasSize(card);
        drawCard(card);
      } else {
        activeCards.delete(card);
        card.cache.clear();
        for (const canvas of [card.nativeCanvas, card.restoredCanvas]) {
          canvas.width = 1;
          canvas.height = 1;
        }
      }
    }
  }, {rootMargin: '250px 0px'});
  const batchObserver = new IntersectionObserver((entries) => {
    if (entries.some((entry) => entry.isIntersecting)) appendBatch();
  }, {rootMargin: '900px 0px'});
  batchObserver.observe(sentinel);

  function loadFlags() {
    try {
      const value = JSON.parse(localStorage.getItem(storageKey) || '{}');
      return value && typeof value === 'object' && !Array.isArray(value) ? value : {};
    } catch (_) {
      return {};
    }
  }

  function saveFlags() {
    try { localStorage.setItem(storageKey, JSON.stringify(flags)); } catch (_) { /* Export remains available. */ }
    flagCount.textContent = String(Object.keys(flags).length);
  }

  function isAnimated(group) {
    return group.tracks.length > 1 || group.tracks.some((track) => track.frames.length > 1);
  }

  function applyFilters() {
    const term = search.value.trim().toLowerCase();
    filtered = groups.filter((group) => {
      if (filter.value === 'animated' && !isAnimated(group)) return false;
      if (filter.value === 'revised' && group.revision_round !== 2) return false;
      if (filter.value === 'round3' && group.revision_round !== 3) return false;
      if (filter.value === 'kept' && group.review_decision !== 'keep_current') return false;
      if (filter.value === 'flagged' && !flags[group.sprite_id]) return false;
      if (categoryFilter && categoryFilter.value !== 'all' && categoryFilter.value !== group.category) return false;
      if (!term) return true;
      return group.label.toLowerCase().includes(term)
        || group.name.toLowerCase().includes(term)
        || String(group.sprite_id).includes(term)
        || group.tracks.some((track) => track.frames.some((frame) => frame.image.toLowerCase().includes(term)));
    });
    cardObserver.disconnect();
    for (const article of cardsElement.children) {
      article.reviewCard.visible = false;
      article.reviewCard.cache.clear();
    }
    activeCards.clear();
    cardsElement.replaceChildren();
    cursor = 0;
    empty.hidden = filtered.length > 0;
    appendBatch();
  }

  function appendBatch() {
    if (cursor >= filtered.length) return;
    const end = Math.min(cursor + batchSize, filtered.length);
    const fragment = document.createDocumentFragment();
    for (; cursor < end; cursor++) fragment.appendChild(createCard(filtered[cursor]));
    cardsElement.appendChild(fragment);
    for (const child of cardsElement.children) {
      if (!child.reviewObserved) {
        child.reviewObserved = true;
        cardObserver.observe(child);
        const rect = child.getBoundingClientRect();
        if (rect.top < window.innerHeight + 250 && rect.bottom > -250) {
          child.reviewCard.visible = true;
          activeCards.add(child.reviewCard);
          updateCanvasSize(child.reviewCard);
          drawCard(child.reviewCard);
        }
      }
    }
    progress.textContent = `${cursor} of ${filtered.length} shown · ${groups.length} total`;
  }

  function createCard(group) {
    const article = document.createElement('article');
    article.className = 'card';
    article.innerHTML = `
      <div class="card-header"><div><h2></h2><div class="card-meta"></div></div>
        <div class="header-actions"><button class="small-button expand" type="button">Expand</button></div></div>
      <p class="missing" hidden></p>
      <div class="previews">
        <div class="preview"><span>${changesetReview ? 'Current accepted · 2×' : 'Original · nearest 2×'}</span><div class="canvas-wrap dark"><canvas class="native" aria-label="Current sprite"></canvas></div></div>
        <div class="preview"><span>${changesetReview && group.review_decision === 'keep_current' ? 'Keep current accepted · 2×' : changesetReview ? 'Proposed revision · 2×' : 'Restored · 2×'}</span><div class="canvas-wrap dark"><canvas class="restored" aria-label="Proposed sprite"></canvas></div></div>
      </div>
      <div class="playback">
        <button class="small-button play" type="button">Pause</button>
        <button class="small-button previous" type="button" title="Previous frame">◀</button>
        <button class="small-button next" type="button" title="Next frame">▶</button>
        <select class="view" aria-label="View"></select>
        <button class="small-button auto-view" type="button" title="Resume automatic view rotation">Auto views</button>
        <span class="frame-label"></span>
      </div>
      <div class="flag-controls">
        <div class="flag-heading"><strong>Flag for revisit</strong>
          <select class="scope" aria-label="Flag target">
            <option value="group">Whole sprite</option>
            <option value="view">This view</option>
            <option value="frame">Current frame</option>
          </select><span class="scope-hint">Choose a reason; changes save automatically.</span></div>
        <div class="chips"></div>
        <textarea class="note" placeholder="Optional detail: what looks wrong, and where?" aria-label="Flag note"></textarea>
      </div>`;

    const card = {
      group, element: article, trackIndex: 0, frameIndex: 0, elapsed: 0, viewElapsed: 0,
      lastTick: 0, visible: false, playing: playAll.checked, manualView: false, cache: new Map(),
      nativeCanvas: article.querySelector('canvas.native'),
      restoredCanvas: article.querySelector('canvas.restored'),
      viewSelect: article.querySelector('select.view'),
      scopeSelect: article.querySelector('select.scope'),
      playButton: article.querySelector('button.play'),
      frameLabel: article.querySelector('.frame-label'),
      note: article.querySelector('.note'),
    };
    article.reviewCard = card;
    article.querySelector('h2').textContent = group.label;
    article.querySelector('.card-meta').textContent = `Sprite ${group.sprite_id} · `
      + `${group.category ? group.category.replaceAll('_', ' ') + ' · ' : ''}${group.profile} · `
      + `${changesetReview ? group.revision_method + ' · ' : ''}`
      + `${group.tracks.length} view${group.tracks.length === 1 ? '' : 's'} · `
      + `${Math.max(...group.tracks.map((track) => track.frames.length))} frame(s)`;
    article.classList.toggle('flagged', Boolean(flags[group.sprite_id]));
    const missing = article.querySelector('.missing');
    if (group.missing_images.length || (changesetReview && group.candidate_warnings.length)) {
      missing.hidden = false;
      missing.textContent = [
        ...(group.missing_images.length ? [`Native registry also refers to missing image names: ${group.missing_images.join(', ')}`] : []),
        ...(changesetReview ? group.candidate_warnings : []),
      ].join(' ');
    }
    for (let i = 0; i < group.tracks.length; i++) {
      const option = document.createElement('option');
      option.value = String(i);
      option.textContent = `View ${group.tracks[i].octants.join(', ')}`;
      card.viewSelect.appendChild(option);
    }
    card.viewSelect.hidden = group.tracks.length === 1;
    article.querySelector('.auto-view').hidden = group.tracks.length === 1;
    const saved = flags[group.sprite_id];
    if (saved) {
      card.scopeSelect.value = saved.scope || 'group';
      card.note.value = saved.note || '';
      if (Number.isInteger(saved.track_index) && group.tracks[saved.track_index]) {
        card.trackIndex = saved.track_index;
        card.manualView = saved.scope !== 'group';
      }
      if (saved.scope === 'frame' && Number.isInteger(saved.frame_index)
          && group.tracks[card.trackIndex].frames[saved.frame_index]) {
        card.frameIndex = saved.frame_index;
        card.playing = false;
      }
    }
    card.viewSelect.value = String(card.trackIndex);
    for (const [key, label] of categories) {
      const chip = document.createElement('button');
      chip.className = 'chip';
      chip.type = 'button';
      chip.textContent = label;
      chip.dataset.category = key;
      chip.setAttribute('aria-pressed', String(Boolean(saved && saved.categories && saved.categories.includes(key))));
      chip.addEventListener('click', () => {
        chip.setAttribute('aria-pressed', String(chip.getAttribute('aria-pressed') !== 'true'));
        writeFlag(card);
      });
      article.querySelector('.chips').appendChild(chip);
    }
    card.note.addEventListener('input', () => writeFlag(card));
    card.scopeSelect.addEventListener('change', () => {
      if (card.scopeSelect.value !== 'group') card.manualView = true;
      if (card.scopeSelect.value === 'frame') card.playing = false;
      updateControls(card);
      writeFlag(card);
    });
    card.viewSelect.addEventListener('change', () => {
      card.manualView = true;
      setTrack(card, Number(card.viewSelect.value));
      if (card.scopeSelect.value !== 'group') writeFlag(card);
    });
    article.querySelector('.auto-view').addEventListener('click', () => { card.manualView = false; });
    card.playButton.addEventListener('click', () => {
      card.playing = !card.playing;
      card.lastTick = 0;
      updateControls(card);
    });
    article.querySelector('.previous').addEventListener('click', () => stepFrame(card, -1));
    article.querySelector('.next').addEventListener('click', () => stepFrame(card, 1));
    article.querySelector('.expand').addEventListener('click', (event) => {
      const expanded = article.classList.toggle('expanded');
      event.currentTarget.textContent = expanded ? 'Compact' : 'Expand';
    });
    for (const wrap of article.querySelectorAll('.canvas-wrap')) wrap.className = `canvas-wrap ${background.value}`;
    card.nativeCanvas.width = 1;
    card.nativeCanvas.height = 1;
    card.restoredCanvas.width = 1;
    card.restoredCanvas.height = 1;
    updateControls(card);
    return article;
  }

  function updateCanvasSize(card) {
    const frames = card.group.tracks[card.trackIndex].frames;
    const width = Math.max(...frames.map((frame) => frame.native_size[0])) * 2;
    const height = Math.max(...frames.map((frame) => frame.native_size[1])) * 2;
    for (const canvas of [card.nativeCanvas, card.restoredCanvas]) {
      canvas.width = width;
      canvas.height = height;
    }
  }

  function updateControls(card) {
    const frameCount = card.group.tracks[card.trackIndex].frames.length;
    card.playButton.textContent = card.playing ? 'Pause' : 'Play';
    card.playButton.disabled = card.scopeSelect.value === 'frame' || !isAnimated(card.group);
    card.element.querySelector('.previous').disabled = frameCount < 2;
    card.element.querySelector('.next').disabled = frameCount < 2;
    card.viewSelect.value = String(card.trackIndex);
    const frame = card.group.tracks[card.trackIndex].frames[card.frameIndex];
    card.frameLabel.textContent = `Frame ${card.frameIndex + 1}/${frameCount} · ${frame.image}`;
  }

  function setTrack(card, index) {
    card.trackIndex = index;
    card.frameIndex = 0;
    card.elapsed = 0;
    card.viewElapsed = 0;
    updateCanvasSize(card);
    updateControls(card);
    drawCard(card);
  }

  function stepFrame(card, direction) {
    const frames = card.group.tracks[card.trackIndex].frames;
    card.playing = false;
    card.frameIndex = (card.frameIndex + direction + frames.length) % frames.length;
    card.elapsed = 0;
    updateControls(card);
    drawCard(card);
    if (card.scopeSelect.value === 'frame') writeFlag(card);
  }

  function loadImage(url) {
    return new Promise((resolve, reject) => {
      const image = new Image();
      image.onload = () => resolve(image);
      image.onerror = () => reject(new Error(`Could not load ${url}`));
      image.src = url;
    });
  }

  function drawCard(card) {
    if (!card.visible) return;
    const frame = card.group.tracks[card.trackIndex].frames[card.frameIndex];
    updateControls(card);
    let cached = card.cache.get(frame.asset);
    if (!cached) {
      cached = {ready: false};
      card.cache.set(frame.asset, cached);
      Promise.all([loadImage(frame.native), loadImage(frame.restored)]).then(([native, restored]) => {
        cached.native = native;
        cached.restored = restored;
        cached.ready = true;
        if (card.visible && card.cache.get(frame.asset) === cached) drawCard(card);
      }).catch((error) => {
        card.frameLabel.textContent = error.message;
      });
      return;
    }
    if (!cached.ready) return;
    for (const [canvas, image, isNative] of [
      [card.nativeCanvas, cached.native, true],
      [card.restoredCanvas, cached.restored, false],
    ]) {
      const context = canvas.getContext('2d');
      context.clearRect(0, 0, canvas.width, canvas.height);
      context.save();
      if (frame.mirrored) {
        context.translate(canvas.width, 0);
        context.scale(-1, 1);
      }
      context.imageSmoothingEnabled = changesetReview || !isNative;
      const width = frame.native_size[0] * 2;
      const height = frame.native_size[1] * 2;
      const x = Math.floor((canvas.width - width) / 2);
      const y = canvas.height - height;
      context.drawImage(image, x, y, width, height);
      context.restore();
    }
  }

  function writeFlag(card) {
    let selected = [...card.element.querySelectorAll('.chip[aria-pressed="true"]')]
      .map((chip) => chip.dataset.category);
    const note = card.note.value.trim();
    if (!selected.length && note) {
      selected = ['other'];
      card.element.querySelector('.chip[data-category="other"]').setAttribute('aria-pressed', 'true');
    }
    const key = card.group.sprite_id;
    if (!selected.length) {
      delete flags[key];
    } else {
      const scope = card.scopeSelect.value;
      flags[key] = {
        scope,
        track_index: scope === 'group' ? null : card.trackIndex,
        frame_index: scope === 'frame' ? card.frameIndex : null,
        categories: selected,
        note,
      };
    }
    card.element.classList.toggle('flagged', Boolean(flags[key]));
    saveFlags();
  }

  function tick(now) {
    if (document.visibilityState === 'visible') {
      for (const card of activeCards) {
        const delta = card.lastTick ? Math.min(now - card.lastTick, 250) : 0;
        card.lastTick = now;
        if (!card.playing || !delta) continue;
        const tracks = card.group.tracks;
        if (rotateViews.checked && !card.manualView && tracks.length > 1) {
          card.viewElapsed += delta;
          if (card.viewElapsed >= 2200) {
            setTrack(card, (card.trackIndex + 1) % tracks.length);
            continue;
          }
        }
        const frames = tracks[card.trackIndex].frames;
        if (frames.length < 2) continue;
        card.elapsed += delta;
        let changed = false;
        for (let i = 0; i < frames.length && card.elapsed >= frames[card.frameIndex].duration_ms; i++) {
          card.elapsed -= frames[card.frameIndex].duration_ms;
          card.frameIndex = (card.frameIndex + 1) % frames.length;
          changed = true;
        }
        if (changed) drawCard(card);
      }
    } else {
      for (const card of activeCards) card.lastTick = 0;
    }
    requestAnimationFrame(tick);
  }

  function exportPayload() {
    const groupById = new Map(groups.map((group) => [String(group.sprite_id), group]));
    const entries = Object.entries(flags).map(([id, flag]) => {
      const group = groupById.get(id);
      if (!group || !flag || !Array.isArray(flag.categories) || !flag.categories.length) return null;
      const track = Number.isInteger(flag.track_index) ? group.tracks[flag.track_index] : null;
      const frame = track && Number.isInteger(flag.frame_index) ? track.frames[flag.frame_index] : null;
      return {
        sprite_id: group.sprite_id,
        ...(group.category ? {category: group.category} : {}),
        name: group.name,
        label: group.label,
        scope: flag.scope,
        view_octants: track ? track.octants : null,
        frame_index: frame ? frame.index : null,
        image: frame ? frame.image : null,
        asset: frame ? frame.asset : null,
        categories: flag.categories,
        note: flag.note || '',
      };
    }).filter(Boolean).sort((a, b) => a.sprite_id - b.sprite_id);
    return JSON.stringify({
      schema: changesetReview ? 'openyamm.sprite_changeset_review.v1'
        : remainingReview ? 'openyamm.remaining_sprite_review.v1' : 'openyamm.decoration_review_flags.v1',
      catalog_source_sha256: catalog.source_sha256,
      exported_utc: new Date().toISOString(),
      ...(changesetReview ? {review_scope: 'flagged_sprite_revisions', catalog_groups: groups.length,
        approve_unflagged: Boolean(document.getElementById('approve-unflagged')?.checked)} : {}),
      ...(remainingReview ? {review_scope: 'all_exported_non_decoration_sprites',
        catalog_groups: groups.length} : {}),
      flags: entries,
    }, null, 2);
  }

  search.addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(applyFilters, 120);
  });
  filter.addEventListener('change', applyFilters);
  if (categoryFilter) categoryFilter.addEventListener('change', applyFilters);
  background.addEventListener('change', () => {
    for (const wrap of cardsElement.querySelectorAll('.canvas-wrap')) {
      wrap.className = `canvas-wrap ${background.value}`;
    }
  });
  playAll.addEventListener('change', () => {
    for (const article of cardsElement.children) {
      const card = article.reviewCard;
      if (card.scopeSelect.value === 'frame') continue;
      card.playing = playAll.checked;
      card.lastTick = 0;
      updateControls(card);
    }
  });
  document.getElementById('export-button').addEventListener('click', () => {
    exportText.value = exportPayload();
    copyStatus.textContent = `${JSON.parse(exportText.value).flags.length} flagged ${noun}`;
    exportDialog.showModal();
  });
  document.getElementById('approve-unflagged')?.addEventListener('change', () => {
    exportText.value = exportPayload();
  });
  document.getElementById('close-export').addEventListener('click', () => exportDialog.close());
  document.getElementById('copy-json').addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(exportText.value);
      copyStatus.textContent = 'Copied to clipboard';
    } catch (_) {
      exportText.focus();
      exportText.select();
      copyStatus.textContent = document.execCommand('copy') ? 'Copied to clipboard' : 'Select and copy the JSON above';
    }
  });
  document.getElementById('download-json').addEventListener('click', () => {
    const url = URL.createObjectURL(new Blob([exportText.value], {type: 'application/json'}));
    const link = document.createElement('a');
    link.href = url;
    link.download = changesetReview ? 'sprite-changeset-review.json'
      : remainingReview ? 'remaining-sprite-review.json' : 'decoration-review-flags.json';
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === '/' && !event.target.matches('input, textarea')) {
      event.preventDefault();
      search.focus();
    }
  });

  saveFlags();
  applyFilters();
  requestAnimationFrame(tick);
})();
