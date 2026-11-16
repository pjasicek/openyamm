/// <reference types="vitest/config" />
import { defineConfig } from 'vite';
import type { Plugin } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'node:path';

// The web app of Map Studio (S5_BROWSER_EDITOR.md 4.9): built into dist/, served by the host. In development the
// Vite server runs on localhost:5173 (in the host's Origin allow list) and passes the host's routes through.
const host = process.env.OYMAP_HOST ?? 'http://127.0.0.1:8765';

// The content security policy of the built app (S5_BROWSER_EDITOR.md 2.12): scripts from its own origin only, wasm
// allowed for the core's worker later, no remote origin at all. Not in development: Vite's dev server injects
// inline scripts.
// The hosted page (S5c, hosted.html) may connect to a paired local studio on 127.0.0.1 and nowhere else.
const hostedConnect = "connect-src 'self' http://127.0.0.1:* ws://127.0.0.1:* http://localhost:* ws://localhost:*";
const contentSecurityPolicy: Plugin = {
    name: 'oymap-csp',
    apply: 'build',
    transformIndexHtml: (html, context) => html.replace('<head>', `<head>\n    <meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; ${context.path.endsWith('hosted.html') ? hostedConnect : "connect-src 'self'"}; worker-src 'self' blob:; object-src 'none'; base-uri 'none'">`),
};

// Library chunks named by what they hold, so their sizes can be read off the build.
function chunkOf(id: string): string | undefined
{
    for (const [name, pattern] of [['three', '/node_modules/three/'], ['codemirror', '/node_modules/@codemirror/'], ['codemirror', '/node_modules/@lezer/'],
        ['react', '/node_modules/react'], ['react', '/node_modules/scheduler/'], ['baseui', '/node_modules/@base-ui/'], ['baseui', '/node_modules/@floating-ui/'],
        ['yaml', '/node_modules/yaml/']] as const)
    {
        if (id.includes(pattern))
        {
            return name;
        }
    }
    return undefined;
}

export default defineConfig({
    plugins: [react(), contentSecurityPolicy],
    base: './',
    server: {
        port: 5173,
        strictPort: true,
        // The project schemas and the generated request list live beside web/ (openyamm-studio/schema).
        fs: { allow: ['..'] },
        proxy: {
            '/rpc': { target: host.replace(/^http/, 'ws'), ws: true },
            '/tex': host,
            '/mesh': host,
            '/picture': host,
            '/walk': host,
            '/core': host,
        },
    },
    build: {
        outDir: 'dist',
        emptyOutDir: true,
        reportCompressedSize: true,
        chunkSizeWarningLimit: 2000,
        rollupOptions: {
            output: { manualChunks: chunkOf },
            input: {
                index: resolve(import.meta.dirname, 'index.html'),
                gallery: resolve(import.meta.dirname, 'gallery.html'),
                hosted: resolve(import.meta.dirname, 'hosted.html'),
            },
        },
    },
    test: {
        include: ['src/**/*.test.ts'],
        environment: 'node',
    },
});
