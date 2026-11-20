#!/usr/bin/env bash
# Publishes the solo-class page to https://jasicek.net/openyamm/maw-solo/ (/var/www/html/openyamm/maw-solo/ on the
# server, root-owned like the MAW guide beside it). Builds the page, uploads to ~/maw-solo-upload with the login user,
# then installs with sudo. Its own folder: the MAW guide's deploy.sh mirrors output/maw_site with --delete.
# Usage: devdocs/maw/solo_sim/page/deploy.sh [SSH_DESTINATION]   (default: 192.168.1.128, the server on the LAN)
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
repo="$(cd "$here/../../../.." && pwd)"
work="${SOLO_SIM_DIR:-$repo/output/maw_solo_sim}"
destination="${1:-192.168.1.128}"
python3 "$here/make_page.py"
rsync -rt --delete --chmod=D755,F644 -e "ssh -o BatchMode=yes -o ConnectTimeout=10" "$work/page/deploy/" \
    "$destination:maw-solo-upload/"
ssh -o BatchMode=yes "$destination" \
    'sudo -n mkdir -p /var/www/html/openyamm/maw-solo && sudo -n rsync -rt --delete --chmod=D755,F644 --chown=root:root ~/maw-solo-upload/ /var/www/html/openyamm/maw-solo/'
curl -fsS -o /dev/null -w "published: %{http_code} https://jasicek.net/openyamm/maw-solo/\n" https://jasicek.net/openyamm/maw-solo/
