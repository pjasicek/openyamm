// Offline (S5_BROWSER_EDITOR.md 2.14): the hosted page registers its service worker (sw.js beside the page, written
// by the staging script with this release's file list), which keeps the release's files, so after the first visit the
// page and the core open without a network. The person's assets were never on the network.
export function registerOffline(version: string): void
{
    if (version === 'dev' || !('serviceWorker' in navigator))
    {
        return;
    }
    navigator.serviceWorker.register(new URL('./sw.js', location.href), { scope: './' }).catch(() => undefined);
}
