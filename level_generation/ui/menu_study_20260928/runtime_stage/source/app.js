/* Interactive design study. No filesystem, engine, or save-game writes. */
'use strict';
(() => {
  const D = window.MENU_DATA;
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const esc = value => String(value).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const clone = value => structuredClone(value);
  const params = new URLSearchParams(location.search);
  const defaults = Object.fromEntries(D.settings.map(setting => [setting.id, setting.value]));
  function bindingDefaults(scheme = 'modern') {
    const values = Object.fromEntries(D.bindings.map(binding => [binding.id, binding.code]));
    if (scheme === 'classic') Object.assign(values, {forward:'ArrowUp', backward:'ArrowDown', left:'ArrowLeft',
      right:'ArrowRight', attack:'KeyA', use:'MouseLeft'});
    return values;
  }
  const screens = [ ['main','Main menu'], ['pause','Pause menu'], ['load','Load game'], ['save','Save game'],
    ['worlds','New game · continent'], ['creation','New game · party'],
    ['gameplay','Settings · Gameplay'], ['video','Settings · Video'], ['audio','Settings · Audio'],
    ['controls','Settings · Mouse & Controls'], ['keyboard','Settings · Keyboard'], ['credits','Credits'] ];
  const S = {
    screen:'main', context:'main', section:'gameplay', saved:clone(defaults), draft:clone(defaults),
    savedBindings:bindingDefaults(), bindings:bindingDefaults(), saves:clone(D.saves), selectedSave:'manual1',
    saveName:'', bindingGroup:'All actions', bindingSearch:'', world:'enroth',
    heroes:[], hero:0, original:false, empty:false, font:'fondamento', background:'dusk', modal:null, toastTimer:null,
  };
  function freshHero(index = 0) {
    return {name:['Kareth','Lysandra','Tavian','Mira','Corwin'][index], className:'Knight', portrait:3 + index,
      voice:1, stats:D.stats.map(() => 11), skills:[]};
  }
  S.heroes = [freshHero()];
  const stage = $('#stage'), content = $('#screen'), modalRoot = $('#modal-root');
  const seal = '<svg class="seal" viewBox="0 0 100 100" aria-hidden="true"><circle cx="50" cy="50" r="34"/><circle cx="50" cy="50" r="29" stroke-opacity=".4"/><ellipse cx="50" cy="50" rx="45" ry="16" transform="rotate(-28 50 50)"/><path d="M50 5 56 40 73 27 60 44 95 50 60 56 73 73 56 60 50 95 44 60 27 73 40 56 5 50 40 44 27 27 44 40Z" fill="#a9935b33"/><path d="m50 38 12 12-12 12-12-12z" fill="#deca9266"/><circle cx="81" cy="27" r="3" fill="#c5ab72"/></svg>';
  const ornament = '<div class="ornament" aria-hidden="true"><span></span></div>';
  function button(label, action, extra = '', classes = '') {
    return `<button class="button ${classes}" type="button" data-action="${action}" ${extra}><span>${esc(label)}</span></button>`;
  }
  function brand(classes = '') {
    return `<div class="brand ${classes}">${seal}<div><div class="brand-name">OpenYAMM</div><div class="brand-subtitle">Universe of Might and Magic</div></div></div>`;
  }
  function frame(title, eyebrow, body, footer, extra = '') {
    const full = S.screen === 'creation';
    return `${full ? '' : brand('top-brand')}<section class="frame stone${full ? ' creation-frame' : ''}"><header class="frame-head"><div>${eyebrow ? `<p class="eyebrow">${eyebrow}</p>` : ''}<h1 tabindex="-1">${title}</h1></div>${extra}</header><div class="frame-body">${body}</div><footer class="frame-footer">${footer}</footer></section>`;
  }
  const footerBack = (label = 'Back') => button(label, 'back', '', 'quiet');
  const world = id => D.worlds.find(item => item.id === id);
  function toast(message) {
    const element = $('#toast'); clearTimeout(S.toastTimer); element.textContent = message;
    element.classList.add('visible'); S.toastTimer = setTimeout(() => element.classList.remove('visible'), 4500);
  }
  function resize() {
    const wrapper = $('#stage-wrap');
    const scale = Math.min(wrapper.clientWidth / 1600, wrapper.clientHeight / 900);
    stage.style.transform = document.fullscreenElement ? `translate(-50%, -50%) scale(${scale})` : `scale(${scale})`;
  }
  new ResizeObserver(resize).observe($('#stage-wrap'));
  document.addEventListener('fullscreenchange', resize);
  function dirtyCount() {
    return D.settings.filter(setting => S.draft[setting.id] !== S.saved[setting.id]).length
      + D.bindings.filter(binding => S.bindings[binding.id] !== S.savedBindings[binding.id]).length;
  }
  function syncUrl() {
    const query = new URLSearchParams(location.search);
    query.set('screen', S.screen === 'settings' ? S.section : S.screen);
    if (S.context === 'pause' && S.screen !== 'main') query.set('context','pause'); else query.delete('context');
    if (S.font !== 'fondamento') query.set('font', S.font); else query.delete('font');
    if (S.empty) query.set('saves','empty'); else query.delete('saves');
    if (S.background !== 'dusk') query.set('background',S.background); else query.delete('background');
    try { history.replaceState(null, '', `${location.pathname}?${query}`); } catch { /* file:// review can still run */ }
  }
  function changeScreen(screen, context = S.context) {
    closeModal(); S.original = false; S.context = context;
    if (D.sections.some(section => section.id === screen) || screen === 'settings') {
      S.section = screen === 'settings' ? 'gameplay' : screen; S.screen = 'settings';
    } else S.screen = screen;
    if (screen === 'main') S.context = 'main';
    if (screen === 'pause' || screen === 'save') S.context = 'pause';
    if (screen === 'save') { S.selectedSave = 'new'; S.saveName = 'New Sorpigal'; }
    if (screen === 'load' && S.selectedSave === 'new') S.selectedSave = S.saves[0]?.id || '';
    render(true); syncUrl();
  }
  function mainScreen() {
    const hasSave = !S.empty && S.saves.length > 0;
    return `<div class="scene-vignette"></div>${brand('title-brand')}<nav class="title-actions stone" aria-label="Main menu">
      ${button('Continue', 'continue', hasSave ? '' : 'disabled', 'primary')}
      <p class="continue-info">${hasSave ? `${esc(S.saves[0].place)} · ${esc(world(S.saves[0].world).name)}` : 'Your adventure begins here'}</p>
      ${button('New Game','new-game')}${button('Load Game','load',hasSave ? '' : 'disabled')}
      ${button('Settings','settings')}<div class="secondary-actions">${button('Credits','credits','','quiet')}${button('Quit','quit','','quiet')}</div>
      </nav><div class="title-footer"><span>Enroth · Antagarich · Jadame</span><span>OpenYAMM</span></div>`;
  }
  function pauseScreen() {
    return `<section class="pause-panel stone"><h1>New Sorpigal</h1>
      <p class="fineprint" style="margin:0 0 21px">Enroth · Monday, 1 January 1168</p>
      ${button('Resume Adventure','resume','','primary')}${button('Save Game','save')}${button('Load Game','load')}
      ${button('Settings','settings')}${button('New Game','new-game')}${ornament}
      ${button('Main Menu','main-menu','','quiet')}${button('Quit to Desktop','quit','','quiet danger')}</section>`;
  }
  function visibleSaves() {
    if (S.empty) return [];
    return S.saves.filter(save => S.screen !== 'save' || save.kind === 'Manual');
  }
  function saveRows() {
    const saves = visibleSaves();
    const newRow = S.screen === 'save' ? `<button type="button" class="save-row" data-save="new" aria-pressed="${S.selectedSave === 'new'}"><span class="slot-symbol">+</span><span><strong>Create a new save</strong><small>Keep your existing adventures</small></span></button>` : '';
    return newRow + (saves.map((save, index) => `<button type="button" class="save-row" data-save="${save.id}" aria-pressed="${S.selectedSave === save.id}"><span class="slot-symbol">${String(index+1).padStart(2,'0')}</span><span><strong>${esc(save.name)}</strong><small>${esc(save.place)} · ${esc(world(save.world).name)}</small></span>${save.kind !== 'Manual' ? `<span class="tag">${save.kind}</span>` : ''}</button>`).join('') ||
      `<div class="empty">${seal}<h3>No saved games</h3><p>${S.screen === 'save' ? 'Choose “Create a new save” above.' : 'Start a new game from the main menu.'}</p></div>`);
  }
  function selectedSave() { return visibleSaves().find(save => save.id === S.selectedSave); }
  function saveDetail() {
    const save = S.screen === 'save' && S.selectedSave === 'new'
      ? {name:'A new chapter', world:'enroth', place:'New Sorpigal', kind:'New save', date:'1 January 1168', time:'Monday · 9:42 AM', preview:true}
      : selectedSave();
    if (!save) return `<div class="empty">${seal}<h2>Choose an adventure</h2><p>Select a save to see its location and game date.</p></div>`;
    let preview = `<div class="save-preview no-preview"><img src="assets/${save.world}.png" alt=""><span>No screenshot available</span></div>`;
    if (save.preview) preview = '<div class="save-preview"><img src="assets/gameplay.png" alt="New Sorpigal preview"></div>';
    if (save.reference) preview = `<div class="save-preview"><div class="reference-crop ref-${save.reference}" role="img" aria-label="Original ${esc(save.place)} save preview"></div></div>`;
    return `<p class="eyebrow">${esc(world(save.world).name)} · ${save.kind}</p><h2>${esc(save.place)}</h2>${preview}
      <dl class="save-meta"><div><dt>Game date</dt><dd>${esc(save.date)}</dd></div><div><dt>Game time</dt><dd>${esc(save.time)}</dd></div></dl>
      ${S.screen === 'save' ? `<label class="save-name" for="save-name">Save name<input id="save-name" type="text" maxlength="40" value="${esc(S.saveName)}" placeholder="Name this adventure" autocomplete="off"></label>` : `<p class="fineprint">${esc(save.name)}<br>Saved ${esc(save.modified)} · ${save.kind} save</p>`}`;
  }
  function saveScreen() {
    const saving = S.screen === 'save';
    const body = `<div class="save-layout"><div class="save-left"><div class="save-list" id="save-list" aria-label="Saved games">${saveRows()}</div></div><div class="save-detail" id="save-detail">${saveDetail()}</div></div>`;
    return frame(saving ? 'Save Game' : 'Load Game', '', body,
      `${footerBack('Cancel')}<div id="save-action">${saveAction()}</div>`);
  }
  function saveAction() {
    const disabled = S.screen === 'save' ? !S.saveName.trim() || (S.selectedSave !== 'new' && !selectedSave()) : !selectedSave();
    return button(S.screen === 'save' ? 'Save Adventure' : 'Load Adventure', S.screen === 'save' ? 'commit-save' : 'commit-load', disabled ? 'disabled' : '', 'primary');
  }
  function updateSaveContent() {
    if (S.selectedSave !== 'new' && !selectedSave()) {
      S.selectedSave = S.screen === 'save' ? 'new' : visibleSaves()[0]?.id || '';
      if (S.screen === 'save') S.saveName = 'New Sorpigal';
    }
    $('#save-list').innerHTML = saveRows(); $('#save-detail').innerHTML = saveDetail(); $('#save-action').innerHTML = saveAction();
  }
  function settingRow(setting) {
    const value = S.draft[setting.id];
    const disabled = setting.depends && !S.draft[setting.depends] || setting.id === 'resolution' && S.draft.window_mode === 'windowed_fullscreen';
    let control;
    if (setting.type === 'toggle') control = `<button type="button" class="toggle" role="switch" aria-checked="${value}" aria-labelledby="label-${setting.id}" data-setting="${setting.id}" ${disabled ? 'disabled' : ''}><span>${value ? 'On' : 'Off'}</span></button>`;
    if (setting.type === 'select') control = `<select id="setting-${setting.id}" data-setting="${setting.id}" aria-labelledby="label-${setting.id}" ${disabled ? 'disabled' : ''}>${setting.options.map(([id,label]) => `<option value="${id}" ${value === id ? 'selected' : ''}>${label}</option>`).join('')}</select>`;
    if (setting.type === 'range') control = `<div class="slider-wrap"><input type="range" id="setting-${setting.id}" data-setting="${setting.id}" min="${setting.min}" max="${setting.max}" step="1" value="${value}" aria-labelledby="label-${setting.id}" ${disabled ? 'disabled' : ''}><output for="setting-${setting.id}" id="output-${setting.id}">${value}${setting.unit}</output></div>`;
    return `<div class="setting ${disabled ? 'dependent-off' : ''}" id="row-${setting.id}"><div><span class="setting-name" id="label-${setting.id}">${setting.name}</span><span class="setting-desc">${setting.desc}</span></div><div class="setting-control">${control}</div></div>`;
  }
  function settingRows() {
    let lastGroup = '';
    return D.settings.filter(setting => setting.section === S.section).map(setting => {
      let heading = '';
      if (setting.group !== lastGroup) { heading = `<h3 class="group-title">${setting.group}</h3>`; lastGroup = setting.group; }
      return heading + settingRow(setting);
    }).join('') + (S.section === 'controls' ? `<div class="setting-inline-note">Choose a preset for a familiar starting point, then customise individual actions in Keyboard.</div>${button('Configure Keyboard','keyboard','','small')}` : '');
  }
  function keyName(code) {
    if (!code) return 'Unbound';
    const names = {MouseLeft:'Left mouse',MouseRight:'Right mouse',MouseMiddle:'Middle mouse',MouseBack:'Mouse 4',MouseForward:'Mouse 5',
      ArrowUp:'↑',ArrowDown:'↓',ArrowLeft:'←',ArrowRight:'→',NumpadAdd:'Num +',NumpadSubtract:'Num −',PageDown:'Page Down',PageUp:'Page Up',Space:'Space',Backquote:'`'};
    return names[code] || code.replace(/^Key|^Digit/,'');
  }
  function bindingRows() {
    const groups = [...new Set(D.bindings.map(binding => binding.group))];
    const rows = D.bindings.filter(binding => (S.bindingGroup === 'All actions' || binding.group === S.bindingGroup)
      && `${binding.name} ${binding.group} ${keyName(S.bindings[binding.id])}`.toLowerCase().includes(S.bindingSearch.toLowerCase()))
      .sort((a, b) => groups.indexOf(a.group) - groups.indexOf(b.group));
    let html = rows.map(binding => `<div class="binding-row"><span class="binding-name">${binding.name}<small>${binding.group}</small></span><button class="key" data-binding="${binding.id}" type="button" aria-label="Rebind ${binding.name}, currently ${esc(keyName(S.bindings[binding.id]))}">${esc(keyName(S.bindings[binding.id]))}</button></div>`).join('');
    const fixed = D.fixedBindings.filter(binding => `${binding.label} ${binding.key}`.toLowerCase().includes(S.bindingSearch.toLowerCase()));
    if (['All actions','System'].includes(S.bindingGroup) && fixed.length) html += '<h3 class="group-title">Fixed shortcuts</h3>' + fixed.map(binding => `<div class="binding-row"><span class="binding-name">${binding.label}<small>Fixed shortcut</small></span><span class="key fixed">${binding.key}</span></div>`).join('');
    return html || '<div class="empty"><h3>No matching actions</h3><p>Try another name or choose All actions.</p></div>';
  }
  function keyboardContent() {
    return `<div class="bindings-filter"><input type="search" id="binding-search" placeholder="Search actions or keys…" aria-label="Search keyboard actions" value="${esc(S.bindingSearch)}"><select id="binding-group" aria-label="Action group">${['All actions',...new Set(D.bindings.map(binding => binding.group))].map(group => `<option ${S.bindingGroup === group ? 'selected' : ''}>${group}</option>`).join('')}</select></div><div class="binding-head"><span>Action</span><span>Assigned key</span><span>Action</span><span>Assigned key</span></div><div class="setting-scroll" id="binding-list">${bindingRows()}</div>`;
  }
  function settingsFooter() {
    const count = dirtyCount();
    return `${footerBack()}<p class="footer-note ${count ? 'dirty' : ''}" role="status">${count ? `${count} unapplied change${count === 1 ? '' : 's'}` : 'Your settings are up to date.'}</p><div class="footer-actions">${button('Revert','revert',count ? '' : 'disabled','quiet')}${button('Apply Changes','apply',count ? '' : 'disabled','primary')}</div>`;
  }
  function settingsScreen() {
    const section = D.sections.find(item => item.id === S.section);
    const body = `<div class="settings-layout"><nav class="settings-nav" aria-label="Settings categories">${D.sections.map(item => `<button class="nav-tab" type="button" data-section="${item.id}" ${item.id === S.section ? 'aria-current="page"' : ''}>${item.name}</button>`).join('')}</nav><section class="settings-content" aria-label="${section.title}"><div class="content-title"><h2>${section.title}</h2><p>${section.subtitle}</p></div>${S.section === 'keyboard' ? keyboardContent() : `<div class="setting-scroll">${settingRows()}</div>`}</section></div>`;
    return frame('Settings', '', body, settingsFooter(), button('Restore Defaults','defaults','','small quiet'));
  }
  function updateSettingsFooter() { $('.frame-footer').innerHTML = settingsFooter(); }
  function worldsScreen() {
    const body = `<div class="worlds">${D.worlds.map(item => `<button class="world-card" type="button" data-world="${item.id}" aria-pressed="${S.world === item.id}">${S.world === item.id ? '<span class="world-selected">Selected</span>' : ''}<img src="assets/${item.image}" alt=""><p class="eyebrow">${item.game}</p><h2>${item.name}</h2><span class="tag">Begin in ${item.home}</span></button>`).join('')}</div>`;
    return frame('Choose Starting Continent', 'New game', body, `${footerBack('Cancel')}${button('Create Your Party','create-party','','primary')}`, '<p class="step-note">01 · Continent &nbsp; / &nbsp; 02 · Party</p>');
  }
  const skillName = name => name.replace(/([a-z])([A-Z])/g, '$1 $2');
  const heroPool = hero => 15 - hero.stats.reduce((sum, value) => sum + value - 11, 0);
  const heroReady = hero => hero.name.trim() && heroPool(hero) === 0 && hero.skills.length === 2;
  function allowedClasses() {
    return S.world === 'jadame' ? ['Knight','Priest','Necromancer'] : S.world === 'antagarich'
      ? ['Knight','Cleric','Sorcerer','Archer','Paladin','Druid','Monk','Ranger','Thief']
      : ['Knight','Cleric','Sorcerer','Archer','Paladin','Druid'];
  }
  function dollPreview(hero) {
    const doll = D.dolls[hero.portrait];
    return `<aside class="appearance"><h3>Appearance</h3><div class="doll" role="img" aria-label="${esc(hero.name)} paperdoll"><img class="doll-background" src="assets/${doll.background}" alt="">${doll.layers.map(layer => `<img src="assets/${layer.file}" alt="" style="left:${layer.x/doll.width*100}%;top:${layer.y/doll.height*100}%;width:${layer.width/doll.width*100}%">`).join('')}</div></aside>`;
  }
  function creationScreen() {
    const hero = S.heroes[S.hero], pool = heroPool(hero), classInfo = D.classes[hero.className];
    const roster = `<div class="party-roster" aria-label="Your party">${S.heroes.map((item,index) => `<button class="party-slot" type="button" data-hero="${index}" aria-label="Edit ${esc(item.name)}, ${heroReady(item) ? 'ready' : 'incomplete'}" aria-pressed="${S.hero === index}"><img src="assets/pc${String(item.portrait).padStart(2,'0')}-01.png" alt=""></button>`).join('')}${S.heroes.length < 5 ? '<button class="party-slot add" type="button" data-action="add-hero" aria-label="Add party member">+</button>' : ''}<span class="party-summary">${S.heroes.length} / 5 adventurers<br>${S.heroes.filter(heroReady).length} ready</span></div>`;
    const body = `<div class="creation-layout"><div class="identity-column"><div class="portrait-controls">${button('‹','portrait-prev','aria-label="Previous portrait"','square')}<img class="identity-portrait" src="assets/pc${String(hero.portrait).padStart(2,'0')}-01.png" alt="${esc(hero.name)}">${button('›','portrait-next','aria-label="Next portrait"','square')}</div><label class="field">Name<input type="text" id="hero-name" maxlength="15" value="${esc(hero.name)}" autocomplete="off"></label><label class="field">Class<select id="hero-class">${allowedClasses().map(name => `<option ${hero.className === name ? 'selected' : ''}>${name}</option>`).join('')}</select></label><div class="voice-row">${button('‹','voice-prev','aria-label="Previous voice"','square')}<span>Voice ${hero.voice} · Human</span>${button('›','voice-next','aria-label="Next voice"','square')}</div><div class="footer-actions">${button('Default','hero-default','','small quiet')}${button('Remove','remove-hero',S.heroes.length === 1 ? 'disabled' : '','small quiet')}</div></div>
      <div class="stats-column"><div class="attribute-head"><h2>Attributes</h2><span class="pool">${pool} points left</span></div>${D.stats.map((name,index) => `<div class="stat-row"><span>${name}</span>${button('−','stat',`data-stat="${index}" data-delta="-1" aria-label="Decrease ${name}" ${hero.stats[index] <= 11 ? 'disabled' : ''}`,'square')}<b>${hero.stats[index]}</b>${button('+','stat',`data-stat="${index}" data-delta="1" aria-label="Increase ${name}" ${pool <= 0 ? 'disabled' : ''}`,'square')}</div>`).join('')}<p class="fineprint">Spend all 15 bonus points before beginning.</p></div>
      <div class="skills-column"><div class="skills-title"><h2>Starting skills</h2></div><ul class="learned" aria-label="Assigned starting skills">${classInfo.fixed.map(name => `<li class="assigned-skill">${skillName(name)}</li>`).join('')}</ul><div class="skills-title"><h3>Choose two more</h3><span>${hero.skills.length} / 2</span></div><div class="skills-grid">${classInfo.optional.map(name => `<button type="button" class="skill-choice" data-skill="${name}" aria-pressed="${hero.skills.includes(name)}" ${hero.skills.length === 2 && !hero.skills.includes(name) ? 'disabled' : ''}><span>${skillName(name)}</span><span>${hero.skills.includes(name) ? '✓' : '+'}</span></button>`).join('')}</div></div>${dollPreview(hero)}</div>${roster}`;
    return frame('Create Your Party', '', body,
      `${footerBack('Cancel')}<p class="footer-note" id="creation-note">${creationNote()}</p>${button('Begin Adventure','begin',S.heroes.every(heroReady) ? '' : 'disabled','primary')}`, `<p class="step-note">${world(S.world).name} · ${world(S.world).home}</p>`);
  }
  function creationNote() {
    const incomplete = S.heroes.filter(hero => !heroReady(hero)).length;
    return incomplete ? `${incomplete} adventurer${incomplete === 1 ? ' needs' : 's need'} a name, all points spent, and two extra skills.` : 'Your party is ready to begin.';
  }
  function creditsScreen() {
    return frame('Credits', '', `<div class="credits">
      <section><h2>New World Computing</h2><p>For creating Might and Magic and the worlds that started it all.</p></section>
      <section><h2>OpenEnroth</h2><p>For inspiring the engine’s development.</p></section>
      <section><h2>Rodril &amp; the MMMerge contributors</h2><p>For bringing the worlds of Might and Magic together.</p></section>
      <section><h2>OpenYAMM</h2><p><strong>pjasicek</strong> · Main developer<br>With thanks to everyone testing OpenYAMM and helping make it better.</p>
      <a href="https://github.com/pjasicek/openyamm" target="_blank" rel="noopener">OpenYAMM on GitHub ↗</a></section>
      </div>`, footerBack());
  }
  function originalId() {
    if (S.screen === 'main') return 2077;
    if (S.screen === 'pause') return 2070;
    if (S.screen === 'save') return 2071;
    if (S.screen === 'load') return 2072;
    if (S.screen === 'creation') return 2076;
    if (S.screen === 'settings') return S.section === 'keyboard' ? 2074 : S.section === 'video' ? 2075 : 2073;
    return null;
  }
  function render(focusHeading = false) {
    const focused = document.activeElement;
    let focusSelector = focused?.id ? `#${focused.id}` : null;
    if (!focusSelector && focused?.dataset) {
      const attributes = ['action','stat','delta','section','binding','world','hero','skill','save'];
      const parts = attributes.filter(name => focused.dataset[name] !== undefined)
        .map(name => `[data-${name}="${CSS.escape(focused.dataset[name])}"]`);
      if (parts.length) focusSelector = parts.join('');
    }
    stage.dataset.screen = S.screen; stage.dataset.context = S.context;
    stage.dataset.background = S.background;
    const renderers = {main:mainScreen,pause:pauseScreen,load:saveScreen,save:saveScreen,settings:settingsScreen,
      worlds:worldsScreen,creation:creationScreen,credits:creditsScreen,game:() => ''};
    content.innerHTML = renderers[S.screen]();
    $('#review-screen').value = S.screen === 'settings' ? S.section : S.screen;
    const compare = $('#compare-original'); compare.disabled = !originalId(); compare.textContent = S.original ? 'Show design' : 'Compare original';
    if (S.original && originalId()) {
      [...content.children].forEach(element => element.inert = true);
      content.insertAdjacentHTML('beforeend', `<div class="original-overlay"><img src="assets/original-${originalId()}.png" alt="Original game screen ${originalId()}"></div>`);
    }
    if (focusHeading) ($('h1',content) || $('button',content))?.focus({preventScroll:true});
    else if (focusSelector) $(focusSelector)?.focus({preventScroll:true});
  }
  function openModal({title, body, actions, cancel, capture = null, timer = null}) {
    const focusBefore = S.modal?.focusBefore || document.activeElement;
    closeModal(); S.modal = {actions,cancel,capture,timer:null,focusBefore}; content.inert = true;
    modalRoot.innerHTML = `<div class="modal-veil"><section class="modal stone" role="dialog" aria-modal="true" aria-labelledby="dialog-title">${seal}<h2 id="dialog-title">${title}</h2><div>${body}</div><div class="footer-actions">${actions.map((action,index) => button(action.label,'modal',`data-modal="${index}"`,action.style || '')).join('')}</div></section></div>`;
    ($('[data-modal="0"]',modalRoot) || $('.modal',modalRoot))?.focus();
    if (timer) S.modal.timer = timer();
  }
  function closeModal() {
    if (!S.modal) return;
    clearInterval(S.modal.timer); const previous = S.modal.focusBefore; S.modal = null;
    modalRoot.innerHTML = ''; content.inert = false;
    if (previous?.isConnected) previous.focus({preventScroll:true});
  }
  function ask(title, message, label, confirm, danger = false) {
    openModal({title,body:`<p>${message}</p>`,cancel:closeModal,actions:[
      {label:'Cancel',style:'quiet',run:closeModal},
      {label,style:danger ? 'danger' : 'primary',run:() => {closeModal();confirm();}},
    ]});
  }
  function back() {
    if (S.original) {S.original = false;render();return;}
    if (S.screen === 'settings' && dirtyCount()) {
      openModal({title:'Leave without applying?',body:'<p>Your changes have not been applied.</p>',cancel:closeModal,actions:[
        {label:'Keep Editing',style:'primary',run:closeModal},
        {label:'Discard Changes',style:'quiet',run:() => {S.draft=clone(S.saved);S.bindings=clone(S.savedBindings);changeScreen(S.context);}},
      ]});return;
    }
    if (S.screen === 'settings' || ['load','save','credits','worlds'].includes(S.screen)) changeScreen(S.context);
    else if (S.screen === 'creation') changeScreen('main');
    else if (S.screen === 'pause') changeScreen('game','pause');
    else if (S.screen === 'game') changeScreen('pause','pause');
  }
  function commitSettings() {
    S.saved = clone(S.draft); S.savedBindings = clone(S.bindings); closeModal(); render(); toast('Settings applied to this preview.');
  }
  function applySettings() {
    if (S.draft.window_mode === S.saved.window_mode && S.draft.resolution === S.saved.resolution) {commitSettings();return;}
    let seconds = 15;
    const revertDisplay = () => {S.draft.window_mode = S.saved.window_mode;S.draft.resolution = S.saved.resolution;closeModal();render();toast('Previous display settings restored. Other changes are still waiting.');};
    openModal({title:'Keep these display settings?',body:`<p>${esc(D.settings.find(setting => setting.id === 'window_mode').options.find(([id]) => id === S.draft.window_mode)[1])} · ${S.draft.window_mode === 'windowed_fullscreen' ? 'Desktop resolution' : esc(S.draft.resolution.replace('x',' × '))}</p><p class="fineprint">Reverting in <strong id="display-countdown">15</strong> seconds.</p>`,cancel:revertDisplay,
      actions:[{label:'Revert Display',style:'quiet',run:revertDisplay},{label:'Keep Changes',style:'primary',run:commitSettings}],
      timer:() => setInterval(() => {seconds--;const count=$('#display-countdown');if(count)count.textContent=seconds;if(seconds <= 0)revertDisplay();},1000)});
  }
  function restoreDefaults() {
    const label = D.sections.find(section => section.id === S.section).name;
    ask(`Restore ${label} defaults?`, S.section === 'keyboard' ? 'All custom bindings will return to your selected control preset. Apply Changes saves the result.' : 'Only this section will be reset. Apply Changes saves the result.', 'Restore Defaults', () => {
      if (S.section === 'keyboard') S.bindings = bindingDefaults(S.draft.control_scheme);
      else for (const setting of D.settings.filter(item => item.section === S.section)) S.draft[setting.id] = setting.value;
      if (S.section === 'controls') S.bindings = bindingDefaults(S.draft.control_scheme);
      render();
    });
  }
  function startBinding(id) {
    const binding = D.bindings.find(item => item.id === id);
    openModal({title:`Bind ${esc(binding.name)}`,body:'<p>Press a key or a mouse button.</p><div class="capture-key">Listening…</div><p class="fineprint" id="capture-note">Escape cancels. Fixed shortcuts are reserved.</p>',capture:id,cancel:closeModal,
      actions:[{label:'Cancel',style:'quiet',run:closeModal},{label:'Clear Binding',style:'quiet',run:() => {S.bindings[id]='';closeModal();render();}}]});
  }
  function captureBinding(code, event) {
    if (!S.modal?.capture) return;
    const id = S.modal.capture;
    if (code === 'Escape') {closeModal();return;}
    if (['F9','F10','Digit1','Digit2','Digit3','Digit4','Digit5','Backquote'].includes(code)
      || event?.metaKey || event?.altKey || event?.ctrlKey || /^(Meta|Control|Alt)/.test(code)) {
      $('#capture-note').textContent = 'That shortcut is reserved. Choose a single different key.';return;
    }
    const conflict = D.bindings.find(item => item.id !== id && S.bindings[item.id] === code);
    if (conflict) {
      const target = D.bindings.find(item => item.id === id);
      const old = S.bindings[id];
      ask('This key is already assigned', `<strong>${esc(keyName(code))}</strong> belongs to ${esc(conflict.name)}. Swap it with ${esc(target.name)}${old ? ` (${esc(keyName(old))})` : ', leaving the previous action unbound'}?`, 'Swap Bindings', () => {
        S.bindings[conflict.id] = old;S.bindings[id] = code;render();toast('Bindings swapped. Apply Changes to keep them.');
      });
    } else {S.bindings[id]=code;closeModal();render();toast('Binding updated. Apply Changes to keep it.');}
  }
  function requestLoad(save) {
    if (!save) return;
    const perform = () => {changeScreen('game','pause');toast(`Preview: loaded “${save.name}”. Press Esc to open the menu.`);};
    if (S.context === 'pause') ask('Load this adventure?', `Unsaved progress will be lost. Load <strong>${esc(save.name)}</strong>?`, 'Load Adventure', perform);
    else perform();
  }
  function commitSave() {
    const name = S.saveName.trim(); if (!name) return;
    const target = S.saves.find(save => save.id === S.selectedSave || save.name.toLowerCase() === name.toLowerCase());
    if (target && target.kind !== 'Manual') {toast('Choose another name. Automatic and quick saves are reserved.');return;}
    const write = () => {
      const save = {id:target?.id || `manual-${Date.now()}`,name,world:'enroth',place:'New Sorpigal',kind:'Manual',
        date:'1 January 1168',time:'Monday · 9:42 AM',modified:'Just now',preview:true};
      S.saves = [save,...S.saves.filter(item => item.id !== save.id)]; S.empty = false;$('#review-saves').value='sample';
      changeScreen('pause','pause');toast(`“${name}” saved in the preview library.`);
    };
    if (target) ask('Replace this save?', `<strong>${esc(target.name)}</strong> will be replaced with your current adventure.`, 'Replace Save',write,true);
    else write();
  }
  function mutateHero(action, element) {
    const hero=S.heroes[S.hero];
    if (action === 'stat') {
      const stat=Number(element.dataset.stat),delta=Number(element.dataset.delta);
      if (delta > 0 && heroPool(hero) > 0 || delta < 0 && hero.stats[stat] > 11) hero.stats[stat] += delta;
    }
    if (action === 'portrait-prev' || action === 'portrait-next') hero.portrait=3+(hero.portrait-3+(action==='portrait-next'?1:4))%5;
    if (action === 'voice-prev' || action === 'voice-next') hero.voice=1+(hero.voice-1+(action==='voice-next'?1:2))%3;
    if (action === 'hero-default') {const fresh=freshHero(S.hero);fresh.className=hero.className;fresh.name=hero.name;S.heroes[S.hero]=fresh;}
    if (action === 'add-hero' && S.heroes.length < 5) {S.heroes.push(freshHero(S.heroes.length));S.hero=S.heroes.length-1;}
    if (action === 'remove-hero' && S.heroes.length > 1) {
      ask('Remove this adventurer?', `Remove ${esc(hero.name)} from the party?`, 'Remove', () => {S.heroes.splice(S.hero,1);S.hero=Math.min(S.hero,S.heroes.length-1);render();});return;
    }
    render();
  }
  content.addEventListener('click', event => {
    if (S.original) return;
    const section=event.target.closest('[data-section]');
    if (section) {S.section=section.dataset.section;render();syncUrl();return;}
    const save=event.target.closest('[data-save]');
    if (save) {S.selectedSave=save.dataset.save;S.saveName=S.saves.find(item=>item.id===S.selectedSave)?.name || 'New Sorpigal';updateSaveContent();return;}
    const setting=event.target.closest('button[data-setting]');
    if (setting) {
      const id=setting.dataset.setting;S.draft[id]=!S.draft[id];
      setting.setAttribute('aria-checked',String(S.draft[id]));setting.querySelector('span').textContent=S.draft[id]?'On':'Off';
      for (const dependent of D.settings.filter(item=>item.depends===id)) {const row=$(`#row-${dependent.id}`);if(row)row.outerHTML=settingRow(dependent);}
      updateSettingsFooter();return;
    }
    const binding=event.target.closest('[data-binding]');if(binding){startBinding(binding.dataset.binding);return;}
    const card=event.target.closest('[data-world]');if(card){S.world=card.dataset.world;render();return;}
    const hero=event.target.closest('[data-hero]');if(hero){S.hero=Number(hero.dataset.hero);render();return;}
    const skill=event.target.closest('[data-skill]');if(skill){const skills=S.heroes[S.hero].skills,id=skill.dataset.skill;S.heroes[S.hero].skills=skills.includes(id)?skills.filter(item=>item!==id):[...skills,id];render();return;}
    const element=event.target.closest('[data-action]');if(!element || element.disabled)return;
    const action=element.dataset.action;
    const routes={settings:'settings',load:'load',save:'save',credits:'credits',keyboard:'keyboard',worlds:'worlds',creation:'creation'};
    if(routes[action]){changeScreen(routes[action]);return;}
    if(action==='back'){back();return;}
    if(action==='resume'){changeScreen('game','pause');toast('Adventure preview. Press Esc to reopen the menu.');return;}
    if(action==='continue'){requestLoad(S.saves[0]);return;}
    if(action==='commit-load'){requestLoad(selectedSave());return;}
    if(action==='commit-save'){commitSave();return;}
    if(action==='new-game'){
      const start=()=>{S.heroes=[freshHero()];S.hero=0;changeScreen('worlds');};
      if(S.context==='pause')ask('Start a new adventure?','Unsaved progress in your current adventure will be lost.','New Game',start);else start();return;
    }
    if(action==='create-party'){
      for(const item of S.heroes)if(!allowedClasses().includes(item.className)){item.className='Knight';item.skills=[];}
      changeScreen('creation');return;
    }
    if(action==='begin'){if(!S.heroes.every(heroReady))return;changeScreen('game','pause');toast(`Preview complete: ${S.heroes.length} adventurer${S.heroes.length===1?'':'s'} ready for ${world(S.world).name}.`);return;}
    if(action==='main-menu'){ask('Return to the main menu?','Unsaved progress will be lost.','Main Menu',()=>changeScreen('main'));return;}
    if(action==='quit'){
      ask('Leave OpenYAMM?',S.context==='pause'?'Unsaved progress will be lost. Quit to desktop?':'Return to your desktop?', 'Quit',()=>{changeScreen('main');toast('Quit confirmed. This browser preview stays open.');},true);return;
    }
    if(action==='apply'){applySettings();return;}
    if(action==='revert'){S.draft=clone(S.saved);S.bindings=clone(S.savedBindings);render();return;}
    if(action==='defaults'){restoreDefaults();return;}
    mutateHero(action,element);
  });
  content.addEventListener('dblclick',event=>{const row=event.target.closest('[data-save]');if(S.screen==='load'&&row)requestLoad(selectedSave());});
  content.addEventListener('input',event=>{
    const element=event.target;
    if(element.id==='save-name'){S.saveName=element.value;$('#save-action').innerHTML=saveAction();}
    if(element.id==='binding-search'){S.bindingSearch=element.value;$('#binding-list').innerHTML=bindingRows();}
    if(element.id==='hero-name'){
      S.heroes[S.hero].name=element.value;$('#creation-note').textContent=creationNote();$('[data-action="begin"]').disabled=!S.heroes.every(heroReady);
    }
    if(element.matches('input[data-setting]')){
      const id=element.dataset.setting,setting=D.settings.find(item=>item.id===id);S.draft[id]=Number(element.value);
      $(`#output-${id}`).textContent=element.value+setting.unit;updateSettingsFooter();
    }
  });
  content.addEventListener('change',event=>{
    const element=event.target;
    if(element.id==='binding-group'){S.bindingGroup=element.value;$('#binding-list').innerHTML=bindingRows();}
    if(element.id==='hero-class'){S.heroes[S.hero].className=element.value;S.heroes[S.hero].skills=[];render();}
    if(element.matches('select[data-setting]')){
      const id=element.dataset.setting,value=element.value;
      if(id==='control_scheme'){
        const previous=S.draft.control_scheme;
        openModal({title:`Use ${value === 'classic' ? 'Classic' : 'Modern'} controls?`,body:'<p>This replaces all custom bindings with the selected preset. You can customise them again in Keyboard.</p>',cancel:()=>{closeModal();render();},actions:[
          {label:'Cancel',style:'quiet',run:()=>{S.draft.control_scheme=previous;closeModal();render();}},
          {label:'Use Preset',style:'primary',run:()=>{S.draft.control_scheme=value;S.bindings=bindingDefaults(value);closeModal();render();}},
        ]});return;
      }
      S.draft[id]=value;
      if(id==='window_mode')$('#row-resolution').outerHTML=settingRow(D.settings.find(item=>item.id==='resolution'));
      updateSettingsFooter();
    }
  });
  modalRoot.addEventListener('click',event=>{const element=event.target.closest('[data-modal]');if(element&&S.modal)S.modal.actions[Number(element.dataset.modal)].run();});
  document.addEventListener('keydown',event=>{
    if(S.modal?.capture){event.preventDefault();event.stopPropagation();if(!event.repeat)captureBinding(event.code,event);return;}
    if(S.modal){
      if(event.key==='Escape'){event.preventDefault();S.modal.cancel?.();return;}
      if(event.key==='Tab'){
        const focusable=$$('button:not(:disabled), input, select, a',modalRoot),first=focusable[0],last=focusable.at(-1);
        if(event.shiftKey&&document.activeElement===first){event.preventDefault();last?.focus();}
        else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first?.focus();}
      }
      return;
    }
    if(event.key==='Escape'){event.preventDefault();back();}
  },true);
  modalRoot.addEventListener('pointerdown',event=>{
    if(!S.modal?.capture||event.target.closest('[data-modal]'))return;
    event.preventDefault();captureBinding(['MouseLeft','MouseMiddle','MouseRight','MouseBack','MouseForward'][event.button],event);
  });
  modalRoot.addEventListener('contextmenu',event=>{if(S.modal)event.preventDefault();});
  function selectBackground(id) {
    const background = window.MENU_BACKGROUNDS.find(item => item.id === id);
    if (!background) return;
    S.background = id; stage.dataset.background = id; $('#review-background').value = id;
    $('#background-credit').innerHTML = `${esc(background.kind)} · <a href="${esc(background.source)}" target="_blank" rel="noopener">${esc(background.artist)} ↗</a>`;
    $$('[data-background-choice]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.backgroundChoice === id)));
    syncUrl();
  }
  $('#review-background').innerHTML = window.MENU_BACKGROUNDS.map(item => `<option value="${item.id}">${esc(item.name)}</option>`).join('');
  $('#background-choices').innerHTML = window.MENU_BACKGROUNDS.map(item => `<article class="background-choice">
    <button type="button" data-background-choice="${item.id}" aria-pressed="${item.id === S.background}" aria-label="Preview ${esc(item.name)}">
      <img src="${item.file}" alt="${esc(item.kind)}" loading="lazy"><span>${esc(item.name)}</span></button>
    <p>${esc(item.note)}</p><a href="${esc(item.source)}" target="_blank" rel="noopener">${esc(item.artist)} ↗</a></article>`).join('');
  $('#review-background').addEventListener('change', event => {
    changeScreen('main'); selectBackground(event.target.value);
  });
  $('#background-choices').addEventListener('click', event => {
    const choice = event.target.closest('[data-background-choice]');
    if (!choice) return;
    changeScreen('main'); selectBackground(choice.dataset.backgroundChoice);
    $('#stage-wrap').scrollIntoView({block:'start', behavior:'instant'});
  });
  $('#review-screen').innerHTML=screens.map(([id,label])=>`<option value="${id}">${label}</option>`).join('');
  $('#review-screen').addEventListener('change',event=>{
    changeScreen(event.target.value,['pause','save'].includes(event.target.value)?'pause':'main');
  });
  $('#review-font').addEventListener('change',event=>{S.font=event.target.value;stage.className=`font-${S.font}`;syncUrl();});
  $('#review-saves').addEventListener('change',event=>{S.empty=event.target.value==='empty';S.selectedSave=S.screen==='save'?'new':S.empty?'':S.saves[0]?.id;render();syncUrl();});
  const compare=document.createElement('button');compare.id='compare-original';compare.type='button';compare.textContent='Compare original';
  compare.addEventListener('click',()=>{S.original=!S.original;render();});$('.review-tools').insertBefore(compare,$('#fullscreen'));
  $('#fullscreen').addEventListener('click',()=>{if(document.fullscreenElement)document.exitFullscreen();else $('#stage-wrap').requestFullscreen().catch(()=>toast('Full screen is unavailable in this browser.'));});
  if(params.get('export')==='1')document.body.classList.add('export');
  if(params.get('saves')==='empty'){S.empty=true;$('#review-saves').value='empty';}
  if(params.get('font')==='almendra'){S.font='almendra';stage.className='font-almendra';$('#review-font').value='almendra';}
  const initial=params.get('screen')||'main';
  changeScreen(screens.some(([id])=>id===initial)?initial:'main',params.get('context')==='pause'?'pause':'main');
  selectBackground(params.get('background') || 'dusk');
  document.fonts.ready.then(()=>{document.body.dataset.ready='true';resize();});
})();
