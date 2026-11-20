#!/usr/bin/env bash
# Sets up the release upload on the server (packaging/RELEASE.md). Run once from a machine that logs in to the server
# with sudo rights; running it again keeps the existing key.
#
#   - a key pair ~/openyamm-keys/ci-deploy-ed25519 for the publish job;
#   - the user openyamm-deploy (no password), whose only key is limited to rsync writes below the web root
#     (rrsync -wo: no shell, no reading, no forwarding), owning only the release folders there;
#   - sshd on a second port, 2222, for the router's forward from the internet: public keys only, openyamm-deploy only.
#     Port 22 keeps serving the LAN; ufw opens 2222.
#
# Usage: packaging/server/setup_deploy_key.sh [SSH_DESTINATION]   (default: server, an ~/.ssh/config entry)
set -euo pipefail

destination="${1:-server}"
keys_dir="${OPENYAMM_KEYS_DIR:-$HOME/openyamm-keys}"
key="$keys_dir/ci-deploy-ed25519"

mkdir -p "$keys_dir"
chmod 700 "$keys_dir"
if [ ! -f "$key" ]; then
    ssh-keygen -q -t ed25519 -N '' -C openyamm-ci-deploy -f "$key"
    echo "Created $key"
fi

# ssh joins its arguments into one remote command line, so they are quoted for the remote shell.
ssh "$destination" "bash -s -- $(printf '%q ' "$(cat "$key.pub")")" <<'REMOTE'
set -euo pipefail
public_key="$1"
if ! id openyamm-deploy > /dev/null 2>&1; then
    sudo useradd --system --create-home --home-dir /home/openyamm-deploy --shell /bin/sh openyamm-deploy
fi
# No password, but not locked: key logins only. sshd runs the forced command through this shell.
sudo usermod -p '*' openyamm-deploy
sudo install -d -m 700 -o openyamm-deploy -g openyamm-deploy /home/openyamm-deploy/.ssh
printf 'command="%s -wo /var/www/html",restrict %s\n' "$(command -v rrsync)" "$public_key" \
    | sudo tee /home/openyamm-deploy/.ssh/authorized_keys > /dev/null
sudo chown openyamm-deploy:openyamm-deploy /home/openyamm-deploy/.ssh/authorized_keys
sudo chmod 600 /home/openyamm-deploy/.ssh/authorized_keys
sudo mkdir -p /var/www/html/openyamm/updates /var/www/html/openyamm/downloads /var/www/html/openyamm-staging
sudo chown -R openyamm-deploy:openyamm-deploy /var/www/html/openyamm/updates /var/www/html/openyamm/downloads \
    /var/www/html/openyamm-staging
sudo tee /etc/ssh/sshd_config.d/openyamm-public.conf > /dev/null <<'CONF'
# Port 22 serves the LAN (ufw allows it only from there). The router forwards the internet's port 2222 here: keys only,
# and only the OpenYAMM release upload (openyamm-deploy, whose key is limited to rrsync writes).
Port 22
Port 2222

Match LocalPort 2222
    AuthenticationMethods publickey
    PasswordAuthentication no
    KbdInteractiveAuthentication no
    PermitRootLogin no
    AllowUsers openyamm-deploy
    X11Forwarding no
    AllowTcpForwarding no
    AllowAgentForwarding no
    PermitTunnel no
CONF
sudo sshd -t
sudo systemctl reload ssh
if sudo ufw status | grep -q '^Status: active'; then
    sudo ufw allow 2222/tcp comment 'OpenYAMM release upload (keys only)' > /dev/null
fi
echo "Folders openyamm-deploy can write below /var/www/html:"
sudo find /var/www/html -maxdepth 2 -user openyamm-deploy -printf '  %p\n'
REMOTE

# The key must open no shell, read nothing and write with rsync; the developer's key must not log in on port 2222.
host="$(ssh -G "$destination" | awk '$1 == "hostname" { print $2 }')"
ssh_options="-o BatchMode=yes -o IdentitiesOnly=yes -i $key -p 2222"
if ssh $ssh_options "openyamm-deploy@$host" true 2>/dev/null; then
    echo "error: the deploy key opened a shell" >&2
    exit 1
fi
if ssh -o BatchMode=yes -p 2222 "$(ssh -G "$destination" | awk '$1 == "user" { print $2 }')@$host" true 2>/dev/null; then
    echo "error: port 2222 accepts other logins than openyamm-deploy" >&2
    exit 1
fi
probe="$(mktemp -d)"
trap 'rm -rf "$probe"' EXIT
rsync -r --dry-run -e "ssh $ssh_options" "$probe/" "openyamm-deploy@$host:openyamm-staging/"
echo "Verified: port 2222 takes only the deploy key, which writes with rsync and opens no shell."
echo
echo "Store the private key as the OPENYAMM_DEPLOY_SSH_KEY secret of the GitHub environment 'release':"
echo "  $key"
