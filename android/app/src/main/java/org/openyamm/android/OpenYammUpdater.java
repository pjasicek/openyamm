package org.openyamm.android;

import android.content.Context;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.os.Build;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.regex.Pattern;

/**
 * The Android updater (packaging/UPDATER_PLAN.md 9.3): the content packs live in app storage (files/content: index.json, the
 * staged next.json and packs/), and a signed manifest names the packs and the APK of the newest release. The manifest
 * signature is checked by the game library (the same Ed25519 code and keys as on Windows).
 */
final class OpenYammUpdater {
    static final String DEFAULT_URL = "https://jasicek.net/openyamm/updates/";
    static final String PLATFORM = "android-arm64";
    private static final Pattern HASH = Pattern.compile("[0-9a-f]{64}");
    private static final Pattern FILE_NAME = Pattern.compile("[A-Za-z0-9_.-]+\\.zip");
    private static boolean nativeLoaded;

    interface Progress {
        void advance(long bytes);
    }

    static final class Pack {
        String id;
        String packageName;
        String mount;
        String file;
        String url;
        String contentId;
        String sha256;
        long size;
        // A language's optional pack (fonts): the game mounts it only while that is the interface language.
        String language = "";
    }

    static final class Manifest {
        String release;
        String build;
        // Short release notes from the signed manifest ("" when there are none).
        String notes;
        int contentFormat;
        long appVersionCode;
        String appUrl;
        String appSha256;
        long appSize;
        final List<Pack> packs = new ArrayList<>();
    }

    private OpenYammUpdater() {
    }

    static native boolean nativeVerifyManifest(byte[] manifest, byte[] signature);

    static native int nativeContentFormat();

    static synchronized void loadNative() {
        if (!nativeLoaded) {
            System.loadLibrary("SDL3");
            System.loadLibrary("main");
            nativeLoaded = true;
        }
    }

    /** Development APKs bundle their content (assets/index.json) and take no updates. */
    static boolean bundlesContent(Context context) {
        try (InputStream input = context.getAssets().open("index.json")) {
            return true;
        } catch (IOException exception) {
            return false;
        }
    }

    /**
     * Before the engine starts: promotes a staged update the running APK can use, and says whether the game has
     * content to start with.
     */
    static boolean prepareContent(Context context) {
        if (bundlesContent(context)) {
            return true;
        }
        loadNative();
        promoteNextContent(context);
        return contentReady(context);
    }

    static File contentDirectory(Context context) {
        return new File(context.getFilesDir(), "content");
    }

    static File packDirectory(Context context) {
        return new File(contentDirectory(context), "packs");
    }

    /** The channel URL: [updates] url of settings.ini in the user data folder, else the release channel. */
    static String configuredUrl(Context context) {
        File settings = new File(context.getExternalFilesDir(null), "settings.ini");
        String section = "";
        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(new FileInputStream(settings), StandardCharsets.UTF_8))) {
            for (String line = reader.readLine(); line != null; line = reader.readLine()) {
                String trimmed = line.trim();
                if (trimmed.startsWith("[") && trimmed.endsWith("]")) {
                    section = trimmed.substring(1, trimmed.length() - 1).trim();
                } else if (section.equals("updates") && trimmed.indexOf('=') > 0) {
                    int equals = trimmed.indexOf('=');
                    String value = trimmed.substring(equals + 1).trim();
                    if (trimmed.substring(0, equals).trim().equals("url")
                            && (value.startsWith("https://") || value.startsWith("http://"))) {
                        return value.endsWith("/") ? value : value + "/";
                    }
                }
            }
        } catch (IOException ignored) {
            // No settings yet: the release channel.
        }
        return DEFAULT_URL;
    }

    static long installedVersionCode(Context context) {
        try {
            PackageInfo info = context.getPackageManager().getPackageInfo(context.getPackageName(), 0);
            return Build.VERSION.SDK_INT >= 28 ? info.getLongVersionCode() : info.versionCode;
        } catch (PackageManager.NameNotFoundException exception) {
            return 0;
        }
    }

    static JSONObject readJson(File file) {
        try (InputStream input = new FileInputStream(file)) {
            return new JSONObject(new String(readAll(input), StandardCharsets.UTF_8));
        } catch (IOException | JSONException exception) {
            return null;
        }
    }

    /** The release of the installed content, or "" before the first download. */
    static String installedRelease(Context context) {
        JSONObject index = readJson(new File(contentDirectory(context), "index.json"));
        return index != null ? index.optString("release", "") : "";
    }

    /**
     * A staged update (next.json) becomes the installed content once the app it was downloaded for runs; a player who
     * skipped the APK installation keeps the content that matches the installed app.
     */
    static void promoteNextContent(Context context) {
        File next = new File(contentDirectory(context), "next.json");
        JSONObject index = readJson(next);
        if (index == null) {
            return;
        }
        if (index.optLong("app_version_code", 0) <= installedVersionCode(context)
                && index.optInt("content_format", -1) == nativeContentFormat()) {
            next.renameTo(new File(contentDirectory(context), "index.json"));
            removeUnreferencedPacks(context);
        }
    }

    /** Every pack of the installed index is present with its size, in the format this app reads. */
    static boolean contentReady(Context context) {
        JSONObject index = readJson(new File(contentDirectory(context), "index.json"));
        if (index == null || index.optInt("content_format", -1) != nativeContentFormat()) {
            return false;
        }
        JSONArray packs = index.optJSONArray("packs");
        if (packs == null || packs.length() == 0) {
            return false;
        }
        for (int i = 0; i < packs.length(); ++i) {
            JSONObject pack = packs.optJSONObject(i);
            File file = new File(packDirectory(context), pack.optString("file"));
            if (!file.isFile() || file.length() != pack.optLong("size", -1)) {
                return false;
            }
        }
        return true;
    }

    /** Deletes packs that neither the installed nor the staged index uses. */
    static void removeUnreferencedPacks(Context context) {
        Set<String> referenced = new HashSet<>();
        for (String name : new String[] {"index.json", "next.json"}) {
            JSONObject index = readJson(new File(contentDirectory(context), name));
            JSONArray packs = index != null ? index.optJSONArray("packs") : null;
            for (int i = 0; packs != null && i < packs.length(); ++i) {
                referenced.add(packs.optJSONObject(i).optString("file"));
            }
        }
        File[] files = packDirectory(context).listFiles();
        for (int i = 0; files != null && i < files.length; ++i) {
            if (files[i].getName().endsWith(".zip") && !referenced.contains(files[i].getName())) {
                files[i].delete();
            }
        }
    }

    static Manifest fetchManifest(String baseUrl) throws IOException {
        String manifestUrl = baseUrl + "channels/stable/" + PLATFORM + ".json";
        byte[] manifestBytes = fetch(manifestUrl);
        byte[] signatureBytes = fetch(manifestUrl + ".sig");
        loadNative();
        if (!nativeVerifyManifest(manifestBytes, signatureBytes)) {
            throw new IOException("The update's signature is invalid; download OpenYAMM again from the website.");
        }
        try {
            JSONObject document = new JSONObject(new String(manifestBytes, StandardCharsets.UTF_8));
            if (document.getInt("schema") != 1 || !PLATFORM.equals(document.getString("platform"))
                    || document.getInt("min_updater_schema") > 1) {
                throw new IOException("This update needs the complete package from the website.");
            }
            Manifest manifest = new Manifest();
            manifest.release = document.getString("release");
            manifest.build = document.getString("build");
            manifest.notes = document.isNull("notes") ? "" : document.optString("notes", "");
            manifest.contentFormat = document.getInt("content_format");
            JSONObject app = document.getJSONObject("app");
            manifest.appUrl = storeUrl(app, "apps/", ".apk");
            manifest.appSha256 = app.getString("sha256");
            manifest.appSize = app.getLong("size");
            manifest.appVersionCode = app.optLong("android_version_code", 0);
            if (manifest.appVersionCode <= 0) {
                throw new IOException("The update server lists no app version; try again later.");
            }
            // The languages' packs are listed apart (language_packs), unread by the updaters before 2.0, which know
            // no language field and would record them as packs of every language (packaging/publish_release.py).
            JSONArray packs = document.getJSONArray("packs");
            JSONArray languagePacks = document.optJSONArray("language_packs");
            int count = packs.length() + (languagePacks != null ? languagePacks.length() : 0);
            for (int i = 0; i < count; ++i) {
                boolean apart = i >= packs.length();
                JSONObject item = apart ? languagePacks.getJSONObject(i - packs.length()) : packs.getJSONObject(i);
                Pack pack = new Pack();
                pack.id = item.getString("id");
                pack.packageName = item.getString("package");
                pack.mount = item.getString("mount");
                pack.file = item.getString("file");
                pack.url = storeUrl(item, "packs/", ".zip");
                pack.contentId = item.getString("content_id");
                pack.sha256 = item.getString("sha256");
                pack.size = item.getLong("size");
                pack.language = item.optString("language", "");
                if (apart && pack.language.isEmpty()) {
                    throw new IOException("The update lists a language pack without its language: " + pack.id);
                }
                if (!FILE_NAME.matcher(pack.file).matches()) {
                    throw new IOException("The update lists an invalid pack name: " + pack.file);
                }
                manifest.packs.add(pack);
            }
            return manifest;
        } catch (JSONException exception) {
            throw new IOException("The update server sent an invalid release: " + exception.getMessage());
        }
    }

    /**
     * A store file is addressed by its own hash: "folder/sha256.suffix" below the channel, or an absolute https URL
     * whose last path segment is "sha256.suffix" (a mirror).
     */
    private static String storeUrl(JSONObject file, String folder, String suffix) throws JSONException, IOException {
        String sha256 = file.getString("sha256");
        String url = file.getString("url");
        boolean addressed = url.equals(folder + sha256 + suffix)
            || (url.startsWith("https://") && url.endsWith("/" + sha256 + suffix));
        if (!HASH.matcher(sha256).matches() || !addressed) {
            throw new IOException("The update lists an invalid file address: " + url);
        }
        return url;
    }

    /** The download URL of a store file: absolute addresses as they are, others below the channel. */
    static String resolveUrl(String baseUrl, String url) {
        return url.startsWith("https://") ? url : baseUrl + url;
    }

    /** Orders X.Y releases; null when either is not one. */
    static Integer compareReleases(String left, String right) {
        int[] a = parseRelease(left);
        int[] b = parseRelease(right);
        if (a == null || b == null) {
            return null;
        }
        return a[0] != b[0] ? Integer.compare(a[0], b[0]) : Integer.compare(a[1], b[1]);
    }

    private static int[] parseRelease(String release) {
        if (release == null || !release.matches("(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)")) {
            return null;
        }
        String[] parts = release.split("\\.");
        return new int[] {Integer.parseInt(parts[0]), Integer.parseInt(parts[1])};
    }

    /** Packs of the manifest that are not in the store yet (an unchanged pack keeps its file name). */
    static List<Pack> missingPacks(Context context, Manifest manifest) {
        List<Pack> missing = new ArrayList<>();
        for (Pack pack : manifest.packs) {
            File file = new File(packDirectory(context), pack.file);
            if (!file.isFile() || file.length() != pack.size) {
                missing.add(pack);
            }
        }
        return missing;
    }

    /**
     * Whether the server's release is worth downloading: a newer one, or the installed one with packs missing (a phone
     * that an updater before 2.0 updated has none of the languages' packs: they are listed apart for those updaters).
     */
    static boolean offersUpdate(Context context, Manifest manifest, String installed) {
        Integer comparison = compareReleases(manifest.release, installed);
        return comparison != null
                && (comparison > 0 || (comparison == 0 && !missingPacks(context, manifest).isEmpty()));
    }

    static boolean needsApp(Context context, Manifest manifest) {
        return manifest.appVersionCode > installedVersionCode(context);
    }

    static long downloadSize(Context context, Manifest manifest) {
        long bytes = needsApp(context, manifest) ? manifest.appSize : 0;
        for (Pack pack : missingPacks(context, manifest)) {
            bytes += pack.size;
        }
        return bytes;
    }

    /** Writes the index of a downloaded release; the game mounts it as its asset root (packs/ beside it). */
    static void writeIndex(File target, Manifest manifest, long appVersionCode) throws IOException {
        try {
            JSONObject index = new JSONObject();
            index.put("schema", 1);
            index.put("release", manifest.release);
            index.put("build", manifest.build);
            index.put("profile", "android");
            index.put("content_format", manifest.contentFormat);
            index.put("store", "packs");
            index.put("app_version_code", appVersionCode);
            JSONArray packs = new JSONArray();
            for (Pack pack : manifest.packs) {
                JSONObject item = new JSONObject();
                item.put("id", pack.id);
                item.put("package", pack.packageName);
                item.put("mount", pack.mount);
                item.put("file", pack.file);
                item.put("size", pack.size);
                item.put("content_id", pack.contentId);
                item.put("sha256", pack.sha256);
                if (!pack.language.isEmpty()) {
                    item.put("language", pack.language);
                }
                packs.put(item);
            }
            index.put("packs", packs);
            File temporary = new File(target.getPath() + ".tmp");
            try (OutputStream output = new FileOutputStream(temporary)) {
                output.write(index.toString(1).getBytes(StandardCharsets.UTF_8));
                output.flush();
            }
            if (!temporary.renameTo(target)) {
                throw new IOException("Cannot write " + target);
            }
        } catch (JSONException exception) {
            throw new IOException(exception.getMessage());
        }
    }

    static byte[] fetch(String url) throws IOException {
        HttpURLConnection connection = open(url, 0);
        try {
            int status = connection.getResponseCode();
            if (status != 200) {
                throw new IOException("The update server answered HTTP " + status + " for " + url);
            }
            try (InputStream input = connection.getInputStream()) {
                return readAll(input);
            }
        } finally {
            connection.disconnect();
        }
    }

    /**
     * The pauses before each further attempt at a file after a broken connection or a busy server (HTTP 408, 429,
     * 5xx; nginx answers 503 above its connections per address, which a household or a mobile carrier's shared
     * address reaches), as in the desktop updater (engine/update/AppUpdater.cpp).
     */
    private static final int[] RETRY_DELAY_SECONDS = {0, 2, 5, 10, 20};

    /**
     * Downloads a file into place: resumes target.part with a Range request, checks the SHA-256 of the whole file and
     * only then renames it, so a store file is always complete and verified. A broken connection or a busy server is
     * retried after RETRY_DELAY_SECONDS, resuming the partial file; a complete file with the wrong bytes is downloaded
     * once more from scratch.
     */
    static void download(String url, File target, long size, String sha256, AtomicBoolean cancel, Progress progress)
            throws IOException {
        File part = new File(target.getPath() + ".part");
        boolean verificationFailed = false;
        for (int attempt = 0;; ++attempt) {
            long offset = part.isFile() ? part.length() : 0;
            if (offset > size) {
                part.delete();
                offset = 0;
            }
            progress.advance(offset);
            long received = offset;
            int status = 0;
            IOException failure = null;
            HttpURLConnection connection = null;
            try {
                connection = open(url, offset);
                status = connection.getResponseCode();
                if (status != 200 && status != 206) {
                    throw new IOException("The update server answered HTTP " + status + " for " + url);
                }
                if (status == 200 && offset > 0) {
                    // The server ignored the range: start over.
                    progress.advance(-offset);
                    received = 0;
                    offset = 0;
                }
                try (InputStream input = connection.getInputStream();
                        OutputStream output = new FileOutputStream(part, offset > 0)) {
                    byte[] buffer = new byte[256 * 1024];
                    for (int read = input.read(buffer); read >= 0; read = input.read(buffer)) {
                        if (cancel.get()) {
                            throw new IOException("cancelled");
                        }
                        output.write(buffer, 0, read);
                        received += read;
                        progress.advance(read);
                        if (received > size) {
                            break;
                        }
                    }
                }
            } catch (IOException exception) {
                if (cancel.get()) {
                    throw exception;
                }
                failure = exception;
            } finally {
                if (connection != null) {
                    connection.disconnect();
                }
            }
            if (failure == null && received == size && sha256.equals(sha256(part))) {
                target.delete();
                if (!part.renameTo(target)) {
                    throw new IOException("Cannot move " + part + " into place");
                }
                return;
            }
            progress.advance(-received);
            if (failure == null) {
                part.delete();
                if (verificationFailed) {
                    throw new IOException(target.getName() + " failed verification");
                }
                verificationFailed = true;
                continue;
            }
            boolean busy = status == 0 || status == 408 || status == 429 || status >= 500;
            if (!busy || attempt >= RETRY_DELAY_SECONDS.length) {
                throw failure;
            }
            try {
                for (int tenth = 0; tenth < RETRY_DELAY_SECONDS[attempt] * 10 && !cancel.get(); ++tenth) {
                    Thread.sleep(100);
                }
            } catch (InterruptedException exception) {
                throw new IOException("cancelled");
            }
            if (cancel.get()) {
                throw new IOException("cancelled");
            }
        }
    }

    static String sha256(File file) throws IOException {
        try (InputStream input = new FileInputStream(file)) {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] buffer = new byte[1 << 20];
            for (int read = input.read(buffer); read >= 0; read = input.read(buffer)) {
                digest.update(buffer, 0, read);
            }
            StringBuilder hex = new StringBuilder();
            for (byte value : digest.digest()) {
                hex.append(String.format("%02x", value & 0xff));
            }
            return hex.toString();
        } catch (NoSuchAlgorithmException exception) {
            throw new IOException(exception.getMessage());
        }
    }

    private static HttpURLConnection open(String url, long offset) throws IOException {
        HttpURLConnection connection = (HttpURLConnection) new URL(url).openConnection();
        connection.setConnectTimeout(15000);
        connection.setReadTimeout(30000);
        connection.setRequestProperty("User-Agent", "OpenYAMM-Android");
        if (offset > 0) {
            connection.setRequestProperty("Range", "bytes=" + offset + "-");
        }
        return connection;
    }

    private static byte[] readAll(InputStream input) throws IOException {
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        byte[] buffer = new byte[64 * 1024];
        for (int read = input.read(buffer); read >= 0; read = input.read(buffer)) {
            output.write(buffer, 0, read);
            if (output.size() > 16 * 1024 * 1024) {
                throw new IOException("The update server sent an oversized file");
            }
        }
        return output.toByteArray();
    }
}
