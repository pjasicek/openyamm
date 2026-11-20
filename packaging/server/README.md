# Release server

The server only serves files: `/var/www/html/openyamm/` (releases) and `/var/www/html/openyamm-staging/` (test
releases) on `jasicek.net` (nginx). The release workflow uploads them with rsync over SSH as the user
`openyamm-deploy`, through the router's forward of port 2222; that port takes public keys only and only that user, whose
key can only write files below the web root (`setup_deploy_key.sh`). No publish script or signing key lives here; a
compromised server can serve wrong files but cannot produce a manifest that clients accept. See
[Releases](../RELEASE.md) and UPDATER_PLAN.md, 7.3 to 7.5.

```
/var/www/html/openyamm/
  updates/channels/stable/<platform>.json (+ .sig)   short cache lifetime
  updates/history/<version>/<platform>.json          every published manifest; releases.json lists the versions
  updates/packs/<sha256>.zip                         immutable
  updates/apps/<sha256>.zip|.apk                     immutable
  downloads/<version>/                               small download packages of the newest two releases
  1.0/index.html                                     existing release page (not managed by the publisher)
```

## One-time setup

1. `setup_deploy_key.sh` (from the developer's PC) creates `openyamm-deploy`, gives it the release folders, adds
   the port-2222 sshd rules and opens the port in ufw. Done on 2026-10-21.

2. nginx: install `nginx-openyamm.conf` as `/etc/nginx/snippets/openyamm.conf` and include it inside the
   `jasicek.net` server block of `/etc/nginx/sites-enabled/jasicek.net`; put
   `limit_conn_zone $binary_remote_addr zone=openyamm_per_ip:10m;` into `/etc/nginx/conf.d/openyamm-limits.conf`;
   raise `worker_connections` to 4096 and add `worker_rlimit_nofile 16384;` in `/etc/nginx/nginx.conf` (nginx's
   soft open-file limit is 1024). Then `sudo nginx -t && sudo systemctl reload nginx`. Done on 2026-10-18; the
   previous files are in `/etc/nginx/backup-openyamm-20261018/`. The snippet's `history/` rule and the removed
   `flatpak/` rule are newer than that installation. On 2026-10-22 the per-address limit went from 4 to 16
   connections (two players behind one address could get 503); the previous snippet is
   `/etc/nginx/snippets/openyamm.conf.before-limit16-*`.

3. The router forwards the public port 2222 to `192.168.1.128:2222` (`jasicek.net:22` is the router's own SSH).

4. From outside the home network, check Range and caching on a test file:

   ```sh
   curl -sI -H 'Range: bytes=0-15' https://jasicek.net/openyamm/updates/packs/<file>.zip   # 206, immutable
   ```

   After the first release, `packaging/publish_release.py verify` checks the manifests, signatures, Range and caching.

## Retention

Each upload removes content packs and apps that none of the newest three releases references (players mid-update and
rollbacks need the previous ones) and download folders older than the newest two. Files the publisher does not own
in those folders stay. The old `/var/www/html/openyamm/flatpak/` folder is no longer used and can be deleted.
