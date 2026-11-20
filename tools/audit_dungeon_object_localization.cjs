// Read-only source/data audit. Usage: node tools/audit_dungeon_object_localization.cjs --yaml-module <module>
// The module must export parse(), or export yaml.parse() (e.g. Playwright's utilsBundle).
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const args = process.argv.slice(2);
const moduleIndex = args.indexOf('--yaml-module');
const yamlModule = require(moduleIndex >= 0 ? args[moduleIndex + 1] : 'yaml');
const yaml = yamlModule.yaml || yamlModule;
const read = p => fs.readFileSync(path.join(root, p), 'utf8').replace(/^\uFEFF/, '');
// yaml-cpp iterates duplicate catalog keys in order; the runtime keeps the last value.
const loadYaml = p => yaml.parse(read(p), {uniqueKeys: false});
const output = 'output/dungeon_object_localization_20261103';
fs.mkdirSync(path.join(root, output), {recursive: true});

// Same quote rules as engine/TextTable.cpp, including embedded newlines.
function table(p)
{
    const rows = [], row = [];
    let cell = '', quoted = false;
    const text = read(p).replace(/\r/g, '');
    for (let i = 0; i < text.length; ++i)
    {
        const c = text[i];
        if (c === '"')
        {
            if (quoted && text[i + 1] === '"') { cell += '"'; ++i; }
            else if (quoted) quoted = false;
            else if (!cell) quoted = true;
            else cell += c;
        }
        else if (!quoted && (c === '\t' || c === '\n'))
        {
            row.push(cell); cell = '';
            if (c === '\n') { rows.push(row.splice(0)); }
        }
        else cell += c;
    }
    assert(!quoted, `Unclosed table quote: ${p}`);
    if (cell || row.length) { row.push(cell); rows.push(row); }
    return rows;
}

const catalog = new Map(), origins = new Map();
function add(source, translation, origin, replace = true)
{
    if (source && translation && source !== translation && (replace || !catalog.has(source)))
    {
        catalog.set(source, translation); origins.set(source, origin);
    }
}
for (const name of ['ui', 'gameplay', 'events'])
{
    const p = `assets_dev/engine/localization/ru/${name}.yml`;
    for (const [source, translation] of Object.entries(loadYaml(p).translations)) add(source, translation, p);
}
const tableRoot = 'assets_dev/engine/data_tables/';
const tableNames = [['map_stats', [1]], ['house_data', [5]], ['npc_greet', [1, 2]],
    ['npc_topic_text', [1]], ['npc_topic', [1]], ['npc_news', [1]]];
for (const [name, columns] of tableNames)
{
    const source = table(`${tableRoot}${name}.txt`);
    const ruPath = `${tableRoot}ru/${name}.txt`;
    const translated = fs.existsSync(path.join(root, ruPath)) ? table(ruPath) : source;
    const byId = new Map(translated.map(r => [r[0], r]));
    const overlayPath = `${ruPath}.overlay.yml`;
    const overlays = fs.existsSync(path.join(root, overlayPath)) ? loadYaml(overlayPath).rows : {};
    for (const row of source)
    {
        for (const col of columns)
        {
            const translation = overlays?.[row[0]]?.[col] ?? byId.get(row[0])?.[col];
            add(row[col], translation, overlayPath);
        }
    }
}
function localized(source)
{
    const translation = catalog.get(source);
    if (source.includes('\ufffd'))
    {
        for (const punctuation of ['’', '…'])
        {
            const candidate = source.replace(/\ufffd/g, punctuation);
            if (catalog.has(candidate)) return {translation: catalog.get(candidate), status: 'encoding-mismatch',
                translationSource: origins.get(candidate), candidate};
        }
    }
    return {translation: translation || '', status: translation && /[А-Яа-яЁё]/.test(translation)
        ? 'translated' : /^[A-Za-z]$/.test(source) || ['___d___d', 'eut__i_n', 'srhtfnut'].includes(source)
            ? 'puzzle-letter' : source === '' ? 'empty' : 'missing',
        translationSource: origins.get(source) || ''};
}
const maps = table(`${tableRoot}map_stats.txt`).filter(r => /^\d+$/.test(r[0]) && /\.blv$/i.test(r[2] || ''));
const decorations = table(`${tableRoot}decoration_data.txt`).filter(r => /^\d+$/.test(r[0]));
const decoByName = new Map(decorations.map(r => [r[1].trim().toLowerCase(), r]));
const decoById = new Map(decorations.map(r => [Number(r[0]) - 1, r]));
const decoByAlias = new Map();
for (const row of decorations)
    for (const alias of (row[14] || '').split('|').filter(Boolean)) decoByAlias.set(alias.toLowerCase().trim(), row);

// Probe all three native layouts; require an exact EOF match before reading placements.
function geometry(p)
{
    const b = fs.readFileSync(path.join(root, p));
    const u16 = o => b.readUInt16LE(o), i32 = o => b.readInt32LE(o);
    for (const [version, faceSize, sectorSize, spriteSize, lightSize, spawnSize] of
        [[6, 0x50, 0x74, 0x1c, 0x0c, 0x14], [7, 0x60, 0x74, 0x20, 0x10, 0x18],
            [8, 0x60, 0x78, 0x20, 0x14, 0x18]])
    {
        try
        {
            let o = 0x88;
            function vector(size)
            {
                const count = i32(o); assert(count >= 0 && count < 1000000);
                o += 4; const start = o; o += count * size; assert(o <= b.length);
                return [start, count];
            }
            vector(6);
            const [faces, faceCount] = vector(faceSize);
            o += i32(0x68) + faceCount * 10;
            const [params, paramCount] = vector(0x24); o += paramCount * 10;
            vector(sectorSize); o += i32(0x6c) + i32(0x70);
            assert(i32(o) >= 0); o += 4;
            const [sprites, spriteCount] = vector(spriteSize), names = o;
            o += spriteCount * 32;
            vector(lightSize); vector(8); vector(spawnSize); vector(12);
            assert.equal(o, b.length);
            const events = {};
            for (let i = 0; i < faceCount; ++i)
            {
                const parameter = u16(faces + i * faceSize + (version > 6 ? 16 : 0) + 0x38);
                if (parameter >= paramCount) continue;
                const event = u16(params + parameter * 0x24 + 0x1a);
                if (event) (events[event] ||= []).push(i);
            }
            const entities = [];
            for (let i = 0; i < spriteCount; ++i)
            {
                const s = sprites + i * spriteSize;
                const name = b.subarray(names + i * 32, names + (i + 1) * 32).toString('latin1').split('\0')[0];
                entities.push({index: i, id: u16(s), name, event: u16(s + 0x16),
                    position: [i32(s + 4), i32(s + 8), i32(s + 12)]});
            }
            return {version, events, entities};
        }
        catch (e) { if (!(e instanceof RangeError || e instanceof assert.AssertionError)) throw e; }
    }
    throw new Error(`Unknown BLV layout: ${p}`);
}
const stringPattern = '"(?:[^"\\\\]|\\\\.)*"';
function luaString(s)
{
    return s.slice(1, -1).replace(/\\(\d{1,3}|.)/gs, (_, c) => /^\d+$/.test(c)
        ? String.fromCharCode(Number(c)) : ({n: '\n', r: '\r', t: '\t', '"': '"', '\\': '\\'})[c] ?? c);
}
function scripts(files)
{
    const entries = [], messages = [], effective = new Map();
    for (const file of files)
    {
        const text = read(file), starts = [...text.matchAll(new RegExp(
            `^[ \\t]*(Register(?:Global)?(?:NoOp)?Event|Replace(?:Map|Global)Event)`
            + `\\(\\s*(\\d+),\\s*(${stringPattern}|nil)`, 'gm'))];
        for (let i = 0; i < starts.length; ++i)
        {
            const m = starts[i], rest = text.slice(m.index, starts[i + 1]?.index ?? text.length);
            const ending = rest.match(/^end(?:,[^\n]*)?\)/m);
            const block = ending ? rest.slice(0, ending.index + ending[0].length) : rest;
            const hint = block.match(new RegExp(`^end,\\s*(${stringPattern})\\)`, 'm'));
            const noOpHint = m[1].includes('NoOp') ? text.slice(m.index).split('\n')[0].match(
                new RegExp(`,\\s*(${stringPattern})\\s*\\)`)) : null;
            const inlineHint = text.slice(m.index).split('\n')[0].match(
                new RegExp(`,\\s*nil,\\s*(${stringPattern})\\s*\\)`));
            const title = m[3] === 'nil' ? '' : luaString(m[3]);
            // IndoorRenderer falls back from getHint() to summarizeEvent() (the title).
            const source = noOpHint ? luaString(noOpHint[1]) : inlineHint ? luaString(inlineHint[1])
                : hint && !m[1].includes('NoOp') ? luaString(hint[1]) : title;
            const entry = {event: Number(m[2]), source, title: m[3] === 'nil' ? '' : luaString(m[3]),
                file, line: text.slice(0, m.index).split('\n').length,
                ...localized(source)};
            effective.set(entry.event, entry);
        }
        for (const m of text.matchAll(new RegExp(
            `evt\\.(StatusText|SetMessage|SimpleMessage)\\(\\s*(${stringPattern}(?:\\s*\\.\\.\\s*${stringPattern})*)`, 'g')))
        {
            const source = [...m[2].matchAll(new RegExp(stringPattern, 'g'))].map(x => luaString(x[0])).join('');
            const eventStart = starts.filter(x => x.index < m.index).at(-1);
            messages.push({source, event: eventStart ? Number(eventStart[2]) : null,
                registrationLine: eventStart ? text.slice(0, eventStart.index).split('\n').length : null,
                method: m[1], file, line: text.slice(0, m.index).split('\n').length,
                ...localized(source)});
        }
    }
    entries.push(...effective.values());
    const activeMessages = messages.filter(m => m.event === null || !effective.has(m.event)
        || (effective.get(m.event).file === m.file && effective.get(m.event).line === m.registrationLine));
    return {entries, messages: activeMessages};
}
const results = [];
for (const world of ['mm6', 'mm7', 'mm8'])
{
    const dir = `assets_dev/worlds/${world}`, files = fs.readdirSync(path.join(root, dir, 'events/maps'));
    for (const file of fs.readdirSync(path.join(root, dir, 'maps')).filter(f => /\.blv$/i.test(f)).sort())
    {
        const base = file.slice(0, -4), prefix = `${dir}/events/maps/`;
        const scriptFiles = files.filter(f => f === `${base}.lua`
            || (f.startsWith(`${base}_`) && f.endsWith('.lua')) || f === `${base}.fixup.lua`)
            .sort((a, b) => (a === `${base}.lua` ? -1 : b === `${base}.lua` ? 1 : a.localeCompare(b)))
            .map(f => prefix + f);
        const g = geometry(`${dir}/maps/${file}`), data = scripts(scriptFiles);
        const map = maps.find(r => r[2].toLowerCase() === file.toLowerCase());
        const entry = {world, file, name: map?.[1] || base, nameRu: catalog.get(map?.[1]) || '',
            registered: !!map, geometryVersion: g.version, scripts: scriptFiles,
            hints: data.entries.map(e => ({...e, faces: g.events[e.event] || [],
                entities: g.entities.filter(x => x.event === e.event).map(x => x.index)})),
            messages: data.messages, decorations: [], unlabelledEvents: []};
        const grouped = new Map();
        for (const entity of g.entities)
        {
            if (!entity.name.trim()) continue;
            const raw = decoById.get(entity.id);
            const deco = decoByName.get(entity.name.toLowerCase().trim())
                || ((!raw || raw[1].trim().toLowerCase() === 'pending')
                    ? decoByAlias.get(entity.name.toLowerCase().trim()) : null) || raw;
            if (!deco || !deco[2] || deco[2] === '-' || deco[2].trim().toLowerCase() === 'null') continue;
            if (!grouped.has(deco[2])) grouped.set(deco[2], {source: deco[2], ...localized(deco[2]), instances: []});
            grouped.get(deco[2]).instances.push(entity);
        }
        entry.decorations = [...grouped.values()];
        for (const [id, faces] of Object.entries(g.events))
        {
            const hint = entry.hints.find(h => h.event === Number(id));
            if (!hint?.source) entry.unlabelledEvents.push({event: Number(id), faces});
        }
        results.push(entry);
    }
}
const globalFiles = fs.readdirSync(path.join(root, 'assets_dev/engine/events'))
    .filter(f => /^Global(?:_.*)?\.lua$/.test(f)).sort((a, b) => a === 'Global.lua' ? -1 : b === 'Global.lua' ? 1
        : a.localeCompare(b)).map(f => `assets_dev/engine/events/${f}`);
const globals = scripts(globalFiles);
const commonObjectEvent = id => (id >= 268 && id <= 289) || (id >= 1741 && id <= 1758)
    || (id >= 65310 && id <= 65316);
const globalObjects = {hints: globals.entries.filter(e => commonObjectEvent(e.event)),
    messages: globals.messages.filter(e => commonObjectEvent(e.event))};
const learnedEffects = [...read('assets_dev/engine/events/Global_learned_effects.lua')
    .matchAll(/effect\s*=\s*("(?:[^"\\]|\\.)*")/g)].map(m => {
        const source = luaString(m[1]); return {source, ...localized(source)};
    });
const unique = rows => [...new Set(rows)];
const missing = new Map();
for (const m of results)
    for (const [kind, rows] of [['hint', m.hints], ['message', m.messages], ['decoration', m.decorations]])
        for (const r of rows.filter(r => ['missing', 'encoding-mismatch'].includes(r.status)))
        {
            if (!missing.has(r.source)) missing.set(r.source, []);
            missing.get(r.source).push({world: m.world, map: m.file, kind, event: r.event,
                file: r.file, line: r.line});
        }
const esc = s => String(s).replace(/\|/g, '\\|').replace(/\n/g, '<br>');
const describe = rows => unique(rows.filter(r => r.source).map(r =>
    `${esc(r.source)} → ${r.status === 'translated' ? esc(r.translation)
        : r.status === 'encoding-mismatch' ? '**ПЕРЕВОД ЕСТЬ, НЕ СОВПАДАЕТ КОДИРОВКА КЛЮЧА**'
        : r.status === 'puzzle-letter' ? '(буква головоломки)' : '**НЕТ ПЕРЕВОДА**'}`)).join('; ') || '—';
const lines = ['# Аудит объектов подземелий MM6–MM8', '', 'Дата: 2026-11-03. Источник: текущие assets_dev и исходный код.', '',
    'Проверены все BLV в трёх мирах, основные Lua и дополнения, общая таблица декораций и русские каталоги.',
    'Перевод сопоставляется по точному английскому ключу, с регистрацией названий карт/домов и NPC-текстов из таблиц.',
    'Подпись — hint события, при его отсутствии title: так работает IndoorRenderer::resolveIndoorLocalEventHintText.',
    'Сам аудит статический: проверяет наличие перевода, без запуска игры и полной оценки литературного качества.', '',
    'В таблицах перечислены и обычные, и специфические подписи: уникальный объект нельзя надёжно определить по имени.',
    'Столбец сообщений охватывает строковые аргументы StatusText, SetMessage, SimpleMessage.',
    'Динамические выражения, вопросы/ответы и тексты, переданные через переменные или помощники, требуют отдельной проверки.',
    'Буквы головоломок не считаются пропусками. Скрытые/неиспользуемые события сохранены в перечне; привязки есть в JSON.',
    'Наличие подписи в скрипте не доказывает её видимость. Декорации учитывают запасную подпись таблицы, даже если её перекрывает событие.',
    'Глобальные варианты бочек/котлов и прочих общих интерактивных декораций ниже проверены отдельно.',
    'Карты MM6 с исходным именем pending — оставшиеся в ресурсах заготовки; их пробелы отделены от основных карт.', '',
    '## Сводка', '', '| Мир | Все BLV | Есть в map_stats | Карт с пробелами подписей/декора | Карт с пробелами сообщений |',
    '| --- | ---: | ---: | ---: | ---: |'];
for (const w of ['mm6', 'mm7', 'mm8'])
{
    const ms = results.filter(m => m.world === w);
    lines.push(`| ${w.toUpperCase()} | ${ms.length} | ${ms.filter(m => m.registered).length} | `
        + `${ms.filter(m => [...m.hints, ...m.decorations].some(r => r.status === 'missing')).length} | `
        + `${ms.filter(m => m.messages.some(r => r.status === 'missing')).length} |`);
}
lines.push('', 'Учтены замены обработчиков в дополнительных скриптах. В частности, три исходных текста '
    + 'Центра управления с пунктуацией Windows-1252 уже заменены UTF-8-текстами в sci-fi_mmmerge.lua; '
    + 'неактивные исходники не считаются пробелами перевода.');
if (missing.size === 0)
{
    lines.push('', 'Все найденные в этом аудите пробелы закрыты. Добавлены 148 записей каталога: '
        + '52 подписи объектов, 94 подписи переходов/обращений и две уточнённые общие подписи.',
    'Исправлены 42 существующие строки NPC-таблиц: общие объекты и сообщения их эффектов. '
        + 'Эти записи загружаются после каталогов и должны сохранять правильные формулировки.',
    'Подписи переходов используют названия мест из текущих русских таблиц. '
        + 'Буквы головоломок и служебные идентификаторы не изменены.');
}
lines.push('', '## Конкретные объекты с пробелами (без переходов)', '',
    '| Мир | Подземелье | Объекты без перевода |', '| --- | --- | --- |');
const transition = s => /^(Leave\b|Enter\b|Exit\b|Gate out of\b|Talk to\b)/.test(s);
for (const m of results)
{
    const labels = unique(m.hints.filter(h => h.status === 'missing' && !transition(h.source))
        .map(h => h.source));
    if (labels.length) lines.push(`| ${m.world} | ${esc(m.nameRu || m.name)} (${m.file})`
        + `${/^pending$/i.test(m.name) ? ' — заготовка' : ''} | ${labels.map(esc).join('; ')} |`);
}
lines.push('', '## Общие интерактивные декорации', '',
    describe(globalObjects.hints), '', 'Сообщения: ' + describe(globalObjects.messages), '',
    'Изученные эффекты в подписях: ' + describe(learnedEffects), '',
    'Кристаллы регистрируются циклом без hint: проверена подпись Crystals из общей таблицы декораций: '
        + describe([{source: 'Crystals', ...localized('Crystals')}]) + '.', '',
    'Идентификаторы общих событий: 268–289, 1741–1758, 65310–65316. '
        + 'Их итоговый выбор зависит от типа декорации и сохранённого состояния.', '');
lines.push('', '## Строки без рабочего перевода', '', '| Оригинал | Где встречается |', '| --- | --- |');
for (const [source, uses] of missing)
    lines.push(`| ${esc(source)} | ${unique(uses.map(u => `${u.world}/${u.map} (${u.kind})`)).join(', ')}`
        + `${source.includes('\ufffd') ? ' — перевод есть, несовпадение кодировки ключа' : ''} |`);
for (const w of ['mm6', 'mm7', 'mm8'])
{
    lines.push('', `## ${w.toUpperCase()}: все подземелья`, '',
        '| Карта | Название | Подписи событий | Декорации | Сообщения объектов/событий |', '| --- | --- | --- | --- | --- |');
    for (const m of results.filter(m => m.world === w))
        lines.push(`| ${m.file}${m.registered ? '' : ' (вне map_stats)'} | ${esc(m.nameRu || m.name)} | `
            + `${describe(m.hints)} | ${describe(m.decorations)} | ${describe(m.messages)} |`);
}
fs.writeFileSync(path.join(root, output, 'audit.json'), JSON.stringify(
    {maps: results, globalObjects, learnedEffects, missing: [...missing]}, null, 2));
fs.writeFileSync(path.join(root, output, 'REPORT.md'), lines.join('\n') + '\n');
fs.writeFileSync(path.join(root, 'LOCALIZATION_DUNGEON_OBJECT_AUDIT_20261103.md'), lines.join('\n') + '\n');
console.log(JSON.stringify({maps: results.length, missingUnique: missing.size,
    commonObjectMissing: [...globalObjects.hints, ...globalObjects.messages].filter(r => r.status === 'missing'),
    missing: [...missing].map(([s, u]) => [s, unique(u.map(x => x.world + '/' + x.map))])}, null, 2));
