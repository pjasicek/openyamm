#!/usr/bin/env bash
# Publishes output/xeen_site to https://jasicek.net/openyamm/xeen-guide/ (/var/www/html/openyamm/xeen-guide/ on the
# server, root-owned like the MM9 and MAW guides beside it). Uploads to ~/xeen-guide-upload with the login user, then
# installs with sudo. Run tools/xeen_site/build_site.py first.
# Usage: tools/xeen_site/deploy.sh [SSH_DESTINATION]   (default: 192.168.1.128, the server on the LAN)
set -euo pipefail
destination="${1:-192.168.1.128}"
site="$(cd "$(dirname "$0")/../.." && pwd)/output/xeen_site"
rsync -rt --delete --chmod=D755,F644 --exclude=page.html --exclude=data/presentations.json \
    -e "ssh -o BatchMode=yes -o ConnectTimeout=10" "$site/" "$destination:xeen-guide-upload/"
ssh -o BatchMode=yes "$destination" \
    'sudo -n rsync -rt --delete --chmod=D755,F644 --chown=root:root ~/xeen-guide-upload/ /var/www/html/openyamm/xeen-guide/'
curl -fsS -o /dev/null -w "published: %{http_code} https://jasicek.net/openyamm/xeen-guide/\n" https://jasicek.net/openyamm/xeen-guide/
