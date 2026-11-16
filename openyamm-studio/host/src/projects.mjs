// The path jail (S5_BROWSER_EDITOR.md 2.12): a browser names a project only by its key, the folder's path relative
// to the repository (devdocs/map_studio/briefs/mm6_cd2/L4), or `root<n>/<path>` for a configured root outside the
// repository. The host maps a key to a folder that must lie, after resolving links, under one of the roots and hold a
// project.yml; anything else is refused before the core sees it.
import { existsSync, readdirSync, readFileSync, realpathSync } from 'node:fs';
import path from 'node:path';

const SKIP = new Set(['build', '.oymap', 'node_modules', '.git', 'review']);
const MAX_DEPTH = 4;

export class ProjectJail {
  constructor(repo, roots) {
    this.repo = path.resolve(repo);
    this.roots = roots.map((root) => path.resolve(root)).filter((root) => existsSync(root));
    this.realRoots = this.roots.map((root) => realpathSync(root));
  }

  keyOf(folder) {
    const relative = path.relative(this.repo, folder);
    if (!relative.startsWith('..') && !path.isAbsolute(relative)) return relative.split(path.sep).join('/');
    const index = this.roots.findIndex((root) => folder === root || folder.startsWith(root + path.sep));
    return `root${index}/${path.relative(this.roots[index], folder).split(path.sep).join('/')}`;
  }

  // The absolute folder of a key, or null when the key is not a project inside the roots.
  resolve(key) {
    if (typeof key !== 'string' || key.length === 0 || key.length > 1024 || key.includes('\0')) return null;
    if (key.startsWith('/') || key.includes('\\') || /^[A-Za-z]:/.test(key)) return null;
    const parts = key.split('/');
    if (parts.some((part) => part === '..' || part === '.' || part === '')) return null;
    let folder;
    const rooted = /^root(\d+)$/.exec(parts[0]);
    if (rooted) {
      const root = this.roots[Number(rooted[1])];
      if (!root) return null;
      folder = path.join(root, ...parts.slice(1));
    } else {
      folder = path.join(this.repo, ...parts);
    }
    let real;
    try {
      real = realpathSync(folder);
    } catch {
      return null;
    }
    const inside = this.realRoots.some((root) => real === root || real.startsWith(root + path.sep));
    return inside && existsSync(path.join(real, 'project.yml')) ? real : null;
  }

  // The folder a new project goes into (project.new): a key whose last part is a plain folder name, whose parent
  // is a root or a folder under one, and which holds no project yet. The folder itself may not exist (the core
  // makes it). Null otherwise.
  resolveNew(key) {
    if (typeof key !== 'string' || key.length === 0 || key.length > 1024 || key.includes('\0')) return null;
    if (key.startsWith('/') || key.includes('\\') || /^[A-Za-z]:/.test(key)) return null;
    const parts = key.split('/');
    const name = parts.at(-1);
    if (parts.some((part) => part === '..' || part === '.' || part === '') || !/^[a-z0-9][a-z0-9_-]{0,63}$/.test(name)) return null;
    let parent;
    const rooted = /^root(\d+)$/.exec(parts[0]);
    if (rooted) {
      const root = this.roots[Number(rooted[1])];
      if (!root || parts.length < 2) return null;
      parent = path.join(root, ...parts.slice(1, -1));
    } else {
      parent = path.join(this.repo, ...parts.slice(0, -1));
    }
    let real;
    try {
      real = realpathSync(parent);
    } catch {
      return null;
    }
    const inside = this.realRoots.some((root) => real === root || real.startsWith(root + path.sep));
    const folder = path.join(real, name);
    return inside && !existsSync(path.join(folder, 'project.yml')) ? folder : null;
  }

  // Each root's key: what the keys of the projects in it start with (a new project's folder goes under one).
  rootKeys() {
    return this.roots.map((root) => this.keyOf(root).replace(/\/$/, ''));
  }

  // Every project folder under the roots: {key, name, id, kind, world, root}, sorted by key.
  list() {
    const found = new Map();
    const visit = (folder, depth, rootIndex) => {
      if (existsSync(path.join(folder, 'project.yml'))) {
        const key = this.keyOf(folder);
        if (!found.has(key)) found.set(key, { key, ...readCard(path.join(folder, 'project.yml')), root: rootIndex });
      }
      if (depth >= MAX_DEPTH) return;
      let entries;
      try {
        entries = readdirSync(folder, { withFileTypes: true });
      } catch {
        return;
      }
      for (const entry of entries) {
        if (entry.isDirectory() && !SKIP.has(entry.name) && !entry.name.startsWith('.')) {
          visit(path.join(folder, entry.name), depth + 1, rootIndex);
        }
      }
    };
    this.roots.forEach((root, index) => visit(root, 0, index));
    return [...found.values()].sort((a, b) => (a.key < b.key ? -1 : a.key > b.key ? 1 : 0));
  }
}

// The map card's top-level `id`, `name`, `kind` and `world`, read line by line (no YAML library in the host).
export function readCard(file) {
  const card = { name: '', id: '', kind: '', world: '' };
  let text = '';
  try {
    text = readFileSync(file, 'utf8');
  } catch {
    return card;
  }
  for (const line of text.split('\n')) {
    const match = /^(id|name|kind|world):\s*(.*?)\s*$/.exec(line);
    if (!match) continue;
    let value = match[2];
    if (/^".*"$/.test(value)) {
      try {
        value = JSON.parse(value);
      } catch {
        value = value.slice(1, -1);
      }
    } else if (/^'.*'$/.test(value)) {
      value = value.slice(1, -1).replaceAll("''", "'");
    }
    card[match[1]] = value;
  }
  return card;
}

// What a project is measured against (S5a5's scorecard): its map card's `map_stats.reference` (a rebuild's
// original) and `base` (an overlay's shipped map), read line by line like readCard. Empty strings when absent.
export function readOriginal(file) {
  const found = { reference: '', base: '' };
  let text = '';
  try {
    text = readFileSync(file, 'utf8');
  } catch {
    return found;
  }
  let inStats = false;
  for (const line of text.split('\n')) {
    if (/^\S/.test(line)) inStats = /^map_stats:\s*$/.test(line);
    const unquote = (value) => value.replace(/^(["'])(.*)\1$/, '$2');
    const base = /^base:\s*(\S.*?)\s*$/.exec(line);
    if (base) found.base = unquote(base[1]);
    const reference = inStats ? /^\s+reference:\s*(\S.*?)\s*$/.exec(line) : null;
    if (reference) found.reference = unquote(reference[1]);
  }
  return found;
}
