package org.openyamm.android;

import android.app.Activity;
import android.app.ActivityManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageInstaller;
import android.graphics.Color;
import android.net.ConnectivityManager;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.Process;
import android.util.Log;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicLong;

/**
 * Downloads the content of the newest release (the first start, or an update the main menu offered) and installs
 * its APK. Runs in its own process (":update"), so the game is never running while its content changes.
 */
public class OpenYammUpdateActivity extends Activity {
    static final String EXTRA_URL = "org.openyamm.android.UPDATE_URL";
    private static final String TAG = "OpenYAMM";
    private static final String ACTION_INSTALL_RESULT = "org.openyamm.android.INSTALL_RESULT";
    private static final int PARALLEL_DOWNLOADS = 3;

    private final Handler handler = new Handler(Looper.getMainLooper());
    private final AtomicBoolean cancel = new AtomicBoolean();
    private final AtomicLong doneBytes = new AtomicLong();
    private TextView title;
    private TextView message;
    private ProgressBar progress;
    private Button primary;
    private Button secondary;
    private String baseUrl;
    private OpenYammUpdater.Manifest manifest;
    private long totalBytes;
    private boolean working;
    // The first download started by itself (on Wi-Fi): the game starts by itself when it is done.
    private boolean playWhenReady;
    // Opened by the main menu's Update button, whose question already showed the release notes.
    private boolean updateConfirmed;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        stopGameProcess();
        OpenYammUpdater.loadNative();
        baseUrl = getIntent().getStringExtra(EXTRA_URL);
        updateConfirmed = baseUrl != null;
        if (baseUrl == null) {
            baseUrl = OpenYammUpdater.configuredUrl(this);
        }
        buildLayout();
        check();
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        if (ACTION_INSTALL_RESULT.equals(intent.getAction())) {
            onInstallResult(intent);
        }
    }

    @Override
    public void onBackPressed() {
        if (!working) {
            super.onBackPressed();
        }
    }

    private void buildLayout() {
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setGravity(Gravity.CENTER);
        layout.setBackgroundColor(Color.rgb(16, 20, 24));
        int padding = dp(32);
        layout.setPadding(padding, padding, padding, padding);
        title = text(22, Color.rgb(234, 223, 198));
        message = text(16, Color.rgb(196, 204, 210));
        progress = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progress.setMax(1000);
        primary = new Button(this);
        secondary = new Button(this);
        LinearLayout buttons = new LinearLayout(this);
        buttons.setGravity(Gravity.CENTER);
        buttons.addView(secondary);
        buttons.addView(primary);
        layout.addView(title);
        layout.addView(message);
        layout.addView(progress, new LinearLayout.LayoutParams(dp(420), dp(24)));
        layout.addView(buttons);
        setContentView(layout);
    }

    private TextView text(int size, int color) {
        TextView view = new TextView(this);
        view.setTextSize(TypedValue.COMPLEX_UNIT_SP, size);
        view.setTextColor(color);
        view.setGravity(Gravity.CENTER);
        view.setPadding(0, dp(8), 0, dp(8));
        return view;
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    private void show(String titleText, String messageText, String primaryText, Runnable primaryAction,
            String secondaryText, Runnable secondaryAction, boolean showProgress) {
        title.setText(titleText);
        message.setText(messageText);
        progress.setVisibility(showProgress ? View.VISIBLE : View.INVISIBLE);
        button(primary, primaryText, primaryAction);
        button(secondary, secondaryText, secondaryAction);
    }

    private static void button(Button view, String label, Runnable action) {
        view.setVisibility(label != null ? View.VISIBLE : View.GONE);
        view.setText(label);
        view.setOnClickListener(action != null ? v -> action.run() : null);
    }

    private static String megabytes(long bytes) {
        return ((bytes + 999999) / 1000000) + " MB";
    }

    private void check() {
        working = true;
        show("OpenYAMM", "Checking for updates...", null, null, null, null, false);
        new Thread(() -> {
            try {
                OpenYammUpdater.Manifest found = OpenYammUpdater.fetchManifest(baseUrl);
                handler.post(() -> onChecked(found));
            } catch (IOException exception) {
                handler.post(() -> onFailed(exception.getMessage()));
            }
        }, "OpenYAMM update check").start();
    }

    private void onChecked(OpenYammUpdater.Manifest found) {
        working = false;
        manifest = found;
        String installed = OpenYammUpdater.installedRelease(this);
        boolean contentReady = OpenYammUpdater.contentReady(this);
        Integer comparison = OpenYammUpdater.compareReleases(found.release, installed);
        if (contentReady && comparison != null && !OpenYammUpdater.offersUpdate(this, found, installed)) {
            show("OpenYAMM " + installed, "OpenYAMM is up to date.", "Play", this::play, null, null, false);
            return;
        }
        if (found.appVersionCode < OpenYammUpdater.installedVersionCode(this)) {
            onFailed("This app is newer than OpenYAMM " + found.release + " on the update server.");
            return;
        }
        totalBytes = OpenYammUpdater.downloadSize(this, found);
        String size = megabytes(totalBytes);
        if (!contentReady && installed.isEmpty()) {
            show("Welcome to OpenYAMM", "The game data (" + size + ") downloads once. Wi-Fi is recommended.",
                    "Download", this::download, null, null, false);
            ConnectivityManager connectivity = (ConnectivityManager) getSystemService(Context.CONNECTIVITY_SERVICE);
            if (connectivity != null && !connectivity.isActiveNetworkMetered()) {
                playWhenReady = true;
                download();
            }
            return;
        }
        if (updateConfirmed && contentReady) {
            download();
            return;
        }
        show("OpenYAMM " + found.release, "This update downloads " + size
                + ". Your saves and settings stay as they are.", "Update", this::download,
                contentReady ? "Later" : null, contentReady ? this::play : null, false);
    }

    private void onFailed(String text) {
        working = false;
        boolean contentReady = OpenYammUpdater.contentReady(this);
        show("OpenYAMM", text == null ? "The update server is unreachable; try again later." : text,
                "Try Again", this::check, contentReady ? "Play" : null, contentReady ? this::play : null, false);
    }

    private void download() {
        final OpenYammUpdater.Manifest release = manifest;
        working = true;
        cancel.set(false);
        doneBytes.set(0);
        show("OpenYAMM " + release.release, "Downloading...", null, null, "Cancel", () -> cancel.set(true), true);
        updateProgress();
        new Thread(() -> {
            try {
                installContent(release);
            } catch (IOException exception) {
                Log.e(TAG, "Update failed", exception);
                String reason = cancel.get() ? "The download was cancelled; it continues where it stopped."
                        : "The download failed: " + exception.getMessage();
                handler.post(() -> onFailed(reason));
            }
        }, "OpenYAMM update download").start();
    }

    private void updateProgress() {
        if (!working) {
            return;
        }
        long done = Math.min(doneBytes.get(), totalBytes);
        progress.setProgress(totalBytes > 0 ? (int) (done * 1000 / totalBytes) : 0);
        message.setText("Downloading " + megabytes(done) + " of " + megabytes(totalBytes));
        handler.postDelayed(this::updateProgress, 250);
    }

    private void installContent(OpenYammUpdater.Manifest release) throws IOException {
        File packs = OpenYammUpdater.packDirectory(this);
        if (!packs.isDirectory() && !packs.mkdirs()) {
            throw new IOException("Cannot create " + packs);
        }
        List<OpenYammUpdater.Pack> missing = OpenYammUpdater.missingPacks(this, release);
        ExecutorService pool = Executors.newFixedThreadPool(PARALLEL_DOWNLOADS);
        try {
            java.util.ArrayList<Future<?>> jobs = new java.util.ArrayList<>();
            for (OpenYammUpdater.Pack pack : missing) {
                jobs.add(pool.submit(() -> {
                    OpenYammUpdater.download(OpenYammUpdater.resolveUrl(baseUrl, pack.url), new File(packs, pack.file), pack.size, pack.sha256,
                            cancel, doneBytes::addAndGet);
                    return null;
                }));
            }
            for (Future<?> job : jobs) {
                try {
                    job.get();
                } catch (java.util.concurrent.ExecutionException exception) {
                    cancel.set(true);
                    Throwable cause = exception.getCause();
                    throw cause instanceof IOException ? (IOException) cause : new IOException(cause);
                } catch (InterruptedException exception) {
                    throw new IOException("interrupted");
                }
            }
        } finally {
            pool.shutdownNow();
            try {
                pool.awaitTermination(10, TimeUnit.SECONDS);
            } catch (InterruptedException ignored) {
                Thread.currentThread().interrupt();
            }
        }

        File content = OpenYammUpdater.contentDirectory(this);
        if (!OpenYammUpdater.needsApp(this, release)) {
            OpenYammUpdater.writeIndex(new File(content, "index.json"), release,
                    OpenYammUpdater.installedVersionCode(this));
            new File(content, "next.json").delete();
            OpenYammUpdater.removeUnreferencedPacks(this);
            handler.post(() -> {
                working = false;
                show("OpenYAMM " + release.release, "OpenYAMM is ready.", "Play", this::play, null, null, false);
                if (playWhenReady) {
                    play();
                }
            });
            return;
        }

        // The packs wait as next.json until the new app runs; the app downloads last.
        OpenYammUpdater.writeIndex(new File(content, "next.json"), release, release.appVersionCode);
        File apk = new File(content, "update.apk");
        OpenYammUpdater.download(OpenYammUpdater.resolveUrl(baseUrl, release.appUrl), apk, release.appSize, release.appSha256, cancel,
                doneBytes::addAndGet);
        handler.post(() -> {
            working = false;
            show("OpenYAMM " + release.release, "Install the new app to finish the update. Android asks you to "
                    + "allow it once.", "Install", () -> installApp(apk), null, null, false);
        });
    }

    private void installApp(File apk) {
        try {
            PackageInstaller installer = getPackageManager().getPackageInstaller();
            PackageInstaller.SessionParams params =
                    new PackageInstaller.SessionParams(PackageInstaller.SessionParams.MODE_FULL_INSTALL);
            params.setAppPackageName(getPackageName());
            int sessionId = installer.createSession(params);
            try (PackageInstaller.Session session = installer.openSession(sessionId)) {
                try (InputStream input = new FileInputStream(apk);
                        OutputStream output = session.openWrite("openyamm.apk", 0, apk.length())) {
                    byte[] buffer = new byte[1 << 20];
                    for (int read = input.read(buffer); read >= 0; read = input.read(buffer)) {
                        output.write(buffer, 0, read);
                    }
                    session.fsync(output);
                }
                Intent intent = new Intent(this, OpenYammUpdateActivity.class).setAction(ACTION_INSTALL_RESULT);
                int flags = PendingIntent.FLAG_UPDATE_CURRENT
                        | (Build.VERSION.SDK_INT >= 31 ? PendingIntent.FLAG_MUTABLE : 0);
                PendingIntent result = PendingIntent.getActivity(this, 0, intent, flags);
                session.commit(result.getIntentSender());
            }
            show("OpenYAMM " + manifest.release, "Installing...", null, null, null, null, false);
        } catch (IOException | RuntimeException exception) {
            Log.e(TAG, "APK installation failed", exception);
            onFailed("The installation failed: " + exception.getMessage());
        }
    }

    private void onInstallResult(Intent intent) {
        int status = intent.getIntExtra(PackageInstaller.EXTRA_STATUS, PackageInstaller.STATUS_FAILURE);
        if (status == PackageInstaller.STATUS_PENDING_USER_ACTION) {
            Intent confirmation = intent.getParcelableExtra(Intent.EXTRA_INTENT);
            if (confirmation != null) {
                startActivity(confirmation);
            }
            return;
        }
        if (status == PackageInstaller.STATUS_SUCCESS) {
            show("OpenYAMM " + manifest.release, "The update is installed.", "Play", this::play, null, null, false);
            return;
        }
        String reason = intent.getStringExtra(PackageInstaller.EXTRA_STATUS_MESSAGE);
        File apk = new File(OpenYammUpdater.contentDirectory(this), "update.apk");
        show("OpenYAMM " + manifest.release, "The new app was not installed" + (reason != null ? ": " + reason : ".")
                + " Your current version keeps working.", "Try Again", () -> installApp(apk),
                OpenYammUpdater.contentReady(this) ? "Play" : null, this::play, false);
    }

    private void play() {
        startActivity(new Intent(this, OpenYammActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK
                | Intent.FLAG_ACTIVITY_CLEAR_TASK));
        finish();
    }

    /** The game (the app's main process) must not run while its packs and index change. */
    private void stopGameProcess() {
        ActivityManager manager = (ActivityManager) getSystemService(Context.ACTIVITY_SERVICE);
        List<ActivityManager.RunningAppProcessInfo> processes =
                manager != null ? manager.getRunningAppProcesses() : null;
        for (int i = 0; processes != null && i < processes.size(); ++i) {
            ActivityManager.RunningAppProcessInfo process = processes.get(i);
            if (process.pid != Process.myPid() && process.processName.equals(getPackageName())) {
                Process.killProcess(process.pid);
            }
        }
    }
}
