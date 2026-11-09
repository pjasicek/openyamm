#!/usr/bin/env bash
# Publishes output/maw_site to https://jasicek.net/openyamm/maw-guide/ (/var/www/html/openyamm/maw-guide/ on the
# server, root-owned like the MM9 guide beside it). Uploads to ~/maw-guide-upload with the login user, then installs
# with sudo. Run tools/maw_site/build_site.py first.
# Usage: tools/maw_site/deploy.sh [SSH_DESTINATION]   (default: 192.168.1.128, the server on the LAN)
set -euo pipefail
destination="${1:-192.168.1.128}"
site="$(cd "$(dirname "$0")/../.." && pwd)/output/maw_site"
rsync -rt --delete --chmod=D755,F644 --exclude=page.html --exclude=work/ \
    -e "ssh -o BatchMode=yes -o ConnectTimeout=10" "$site/" "$destination:maw-guide-upload/"
ssh -o BatchMode=yes "$destination" \
    'sudo -n rsync -rt --delete --chmod=D755,F644 --chown=root:root ~/maw-guide-upload/ /var/www/html/openyamm/maw-guide/'
curl -fsS -o /dev/null -w "published: %{http_code} https://jasicek.net/openyamm/maw-guide/\n" https://jasicek.net/openyamm/maw-guide/
