// The schema lint from a shell (S5_BROWSER_EDITOR.md 3.8):
//   node scripts/lint-schemas.ts           check the schemas against the allow list (exit 1 on a new issue or a
//                                           stale entry: the list may only shrink)
//   node scripts/lint-schemas.ts --counts  issues by rule and file
//   node scripts/lint-schemas.ts --write   write today's issues as the allow list (only when first landing it, or
//                                           after removing fixed entries by hand: never to let a new issue in)
import { readFileSync, writeFileSync } from 'node:fs';
import { checkAllowList, issueKey, lintSchemas } from '../src/lint/lint.ts';
import { allowPath, loadSchemas } from '../src/lint/load.ts';

const start = performance.now();
const issues = lintSchemas(loadSchemas());
const ms = Math.round(performance.now() - start);
const mode = process.argv[2];
if (mode === '--write')
{
    writeFileSync(allowPath, JSON.stringify(issues.map(issueKey).sort(), null, 0).replace(/","/g, '",\n"') + '\n');
    console.log(`wrote ${issues.length} entries to ${allowPath}`);
    process.exit(0);
}
if (mode === '--counts')
{
    const byRule: Record<string, number> = {};
    const byFile: Record<string, number> = {};
    for (const issue of issues)
    {
        byRule[issue.rule] = (byRule[issue.rule] ?? 0) + 1;
        const file = issue.where.split('#')[0];
        byFile[file] = (byFile[file] ?? 0) + 1;
    }
    console.log(`${issues.length} issues in ${ms} ms`);
    console.log('by rule', JSON.stringify(byRule));
    console.log('by file', JSON.stringify(byFile));
    process.exit(0);
}
const allow: string[] = JSON.parse(readFileSync(allowPath, 'utf8'));
const { fresh, stale } = checkAllowList(issues, allow);
fresh.forEach((i) => console.log(`NEW   ${i.rule} ${i.where}: ${i.message}`));
stale.forEach((s) => console.log(`FIXED ${s} (remove it from src/lint/allow.json)`));
console.log(`${issues.length} issues, ${allow.length} allowed, ${fresh.length} new, ${stale.length} stale; ${ms} ms`);
process.exit(fresh.length + stale.length > 0 ? 1 : 0);
