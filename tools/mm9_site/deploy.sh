#!/usr/bin/env bash
# Publishes output/mm9_site to https://jasicek.net/openyamm/mm9-guide/ (/var/www/html/openyamm/mm9-guide/ on the
# server, root-owned like the MAW guide beside it). Uploads to ~/mm9-guide-upload with the login user, then installs
# with sudo. Run tools/mm9_site/build_site.py first.
# Usage: tools/mm9_site/deploy.sh [SSH_DESTINATION]   (default: 192.168.1.128, the server on the LAN)
set -euo pipefail
destination="${1:-192.168.1.128}"
site="$(cd "$(dirname "$0")/../.." && pwd)/output/mm9_site"
rsync -rt --delete --chmod=D755,F644 --exclude=page.html --exclude=data/presentations.json \
    -e "ssh -o BatchMode=yes -o ConnectTimeout=10" "$site/" "$destination:mm9-guide-upload/"
ssh -o BatchMode=yes "$destination" \
    'sudo -n rsync -rt --delete --chmod=D755,F644 --chown=root:root ~/mm9-guide-upload/ /var/www/html/openyamm/mm9-guide/'
curl -fsS -o /dev/null -w "published: %{http_code} https://jasicek.net/openyamm/mm9-guide/\n" https://jasicek.net/openyamm/mm9-guide/
