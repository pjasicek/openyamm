// The project schemas as one set, with $ref resolution across files.
// A property written as {description, $ref, x-...} resolves to the target merged with the property's own keys, so
// annotations and descriptions written beside a $ref win over the target's.

export type Json = null | boolean | number | string | Json[] | { [key: string]: Json };
export type Schema = { [key: string]: any };

export interface Located
{
    node: Schema;
    file: string;
    ptr: string;
}

export class Registry
{
    files: Record<string, Schema>;

    constructor(files: Record<string, Schema>)
    {
        this.files = files;
    }

    root(file: string): Located
    {
        return { node: this.files[file], file, ptr: '#' };
    }

    at(file: string, ptr: string): Located
    {
        let node: any = this.files[file];
        for (const segment of ptr.replace(/^#\/?/, '').split('/').filter((s) => s.length > 0))
        {
            node = node?.[segment.replace(/~1/g, '/').replace(/~0/g, '~')];
        }
        if (node === undefined)
        {
            throw new Error(`no schema at ${file}${ptr}`);
        }
        return { node, file, ptr };
    }

    // Follows $ref until a node without one. The outer node's own keys (description, x-...) are kept.
    resolve(loc: Located): Located
    {
        let current = loc;
        let merged: Schema = {};
        for (let guard = 0; guard < 16; ++guard)
        {
            const ref = current.node.$ref;
            const { $ref, ...own } = current.node;
            merged = { ...own, ...merged };
            if (typeof ref !== 'string')
            {
                return { node: merged, file: current.file, ptr: current.ptr };
            }
            const hash = ref.indexOf('#');
            const file = hash > 0 ? ref.slice(0, hash) : hash === 0 ? current.file : ref;
            const ptr = hash >= 0 ? ref.slice(hash) : '#';
            current = this.at(file, ptr);
        }
        throw new Error(`$ref cycle at ${loc.file}${loc.ptr}`);
    }

    // The target name of a $ref chain's last hop ("id", "point2", ...), or undefined.
    refName(loc: Located): string | undefined
    {
        let current = loc;
        let name: string | undefined;
        for (let guard = 0; guard < 16; ++guard)
        {
            const ref = current.node.$ref;
            if (typeof ref !== 'string')
            {
                return name;
            }
            name = ref.split('/').pop();
            const hash = ref.indexOf('#');
            const file = hash > 0 ? ref.slice(0, hash) : hash === 0 ? current.file : ref;
            current = this.at(file, hash >= 0 ? ref.slice(hash) : '#');
        }
        return name;
    }

    child(loc: Located, ...segments: (string | number)[]): Located
    {
        let node: any = loc.node;
        let ptr = loc.ptr;
        for (const segment of segments)
        {
            node = node[segment];
            ptr += '/' + String(segment).replace(/~/g, '~0').replace(/\//g, '~1');
        }
        return { node, file: loc.file, ptr };
    }
}
