#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."

HOST=$(grep -m1 server_name nginx/https.conf | awk '{print $2}' | tr -d ';')

git pull --ff-only
docker compose -f docker-compose.yml -f docker-compose.https.yml up -d --build

for i in $(seq 1 30); do
  if curl -fs -m 5 -o /dev/null "https://$HOST/healthz"; then
    echo "Healthy: https://$HOST"
    exit 0
  fi
  sleep 2
done

echo "Health check failed. See: docker compose logs nginx app" >&2
exit 1
