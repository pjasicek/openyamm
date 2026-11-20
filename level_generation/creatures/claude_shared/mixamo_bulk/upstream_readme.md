Downloads all the free Mixamo animations (and animation packs) in bulk.

This revision updates the script for the current Mixamo site UI. It uses resilient
selectors instead of fixed `nth-child` paths, dispatches pointer/mouse events for
better compatibility with Mixamo's React interface, re-queries cards after rerenders,
and adds localStorage checkpoint/resume, retry handling, and console controls.

Step 1
-----
Open https://www.mixamo.com/ and make sure you're logged in. Select the **Animations** tab,
set the catalog to **96 Per Page**, go to **page 1**, and clear the search field.

Step 2
-----
Configure your browser to allow multiple automatic downloads from Mixamo, and disable the
option that asks where to save every file ("Always ask where to save files"). It also helps
to prevent the computer from sleeping.

Step 3
-----
Open the browser developer console (press F12 and click the "Console" tab).

Step 4
-----
Paste in the contents of `DownloadMixamoByJakeCattrall.js` and press enter. It will work
through the catalog from the current page, downloading each animation and pack.

Tip: for a first run, set `maxItemsPerPage: 3` in the `SETTINGS` block at the top of the
script to confirm downloads work correctly, then change it back to `maxItemsPerPage: null`
to download everything.

Console controls
-----
```js
mixamoDownloader.status();        // current progress and settings
mixamoDownloader.stop();          // stop after the current operation
mixamoDownloader.listFailures();  // list items that failed all attempts
mixamoDownloader.inspectModal();  // dump the current download modal's controls
mixamoDownloader.clearProgress(); // clear saved localStorage progress
```

Notes
-----
Mixamo does not expose a browser event confirming a file has finished downloading, so the
script waits a configurable delay after clicking the final Download button. The Mixamo UI is
not a documented API and may change again; the selectors are intentionally defensive, but
future site changes may require further updates.

Thanks to the commenters who contributed fixes and the modernized rewrite for the current UI.