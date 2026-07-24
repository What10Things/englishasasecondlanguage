#!/usr/bin/env bash
set -euo pipefail
DOMAIN="englishasaforeignlanguage.com"
A=$(dig +short A "$DOMAIN" | paste -sd, -)
AAAA=$(dig +short AAAA "$DOMAIN" | paste -sd, -)
CNAME=$(dig +short CNAME "$DOMAIN" | paste -sd, -)
HTTPS=$(dig +short HTTPS "$DOMAIN" | paste -sd, -)
WWW_A=$(dig +short A "www.$DOMAIN" | paste -sd, -)
WWW_AAAA=$(dig +short AAAA "www.$DOMAIN" | paste -sd, -)
MSG="A=${A:-none}; AAAA=${AAAA:-none}; HTTPS=${HTTPS:-none}; wwwA=${WWW_A:-none}; wwwAAAA=${WWW_AAAA:-none}"
echo "$MSG"
echo "message=$MSG" >> "$GITHUB_OUTPUT"
