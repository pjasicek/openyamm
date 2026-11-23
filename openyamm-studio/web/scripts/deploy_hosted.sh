#!/bin/bash
# Uploads a staged hosted page (scripts/stage_hosted.mjs --out <site>) to https://oyeditor.jasicek.net
# (packaging/server/nginx-oyeditor.conf, web root /var/www/oyeditor on the release server). The versioned folder goes
# first, then studio/versions.json and the root index.html, so a visitor never gets sent to a version not there yet.
# Older versions stay: a page open in one keeps working.
#
#   openyamm-studio/web/scripts/deploy_hosted.sh <site folder> [ssh destination, default: server]
set -euo pipefail
site=${1:?usage: deploy_hosted.sh <site folder> [ssh destination]}
dest=${2:-server}
root=/var/www/oyeditor
[ -f "$site/index.html" ] && [ -f "$site/studio/versions.json" ] || { echo "not a staged site: $site" >&2; exit 1; }
latest=$(node -e 'console.log(JSON.parse(require("fs").readFileSync(process.argv[1])).latest)' "$site/studio/versions.json")
[ -d "$site/studio/$latest" ] || { echo "versions.json names $latest, which is not staged" >&2; exit 1; }

ssh "$dest" "mkdir -p $root/studio"
rsync -rlt --chmod=D755,F644 "$site/studio/$latest/" "$dest:$root/studio/$latest/"
rsync -lt --chmod=F644 "$site/studio/versions.json" "$dest:$root/studio/versions.json"
rsync -lt --chmod=F644 "$site/index.html" "$dest:$root/index.html"
echo "deployed $latest to https://oyeditor.jasicek.net/"
