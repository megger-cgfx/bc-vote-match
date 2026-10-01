#!/bin/bash
# Regenerate /etc/portal.yaml from the container's real env (PID 1), then restart comfyui.
set -u
# Load the container environment (the instance env block lives in PID 1's environ;
# an SSH login shell does NOT inherit it — that's why portal.yaml came out empty).
while IFS= read -r -d '' kv; do
  export "$kv"
done < /proc/1/environ

cd /opt/portal-aio/caddy_manager
/opt/portal-aio/venv/bin/python caddy_config_manager.py
echo "=== portal.yaml ==="
cat /etc/portal.yaml
echo "=== restart comfyui ==="
supervisorctl restart comfyui
sleep 20
supervisorctl status comfyui
echo "=== system_stats ==="
curl -s -m 10 http://localhost:18188/system_stats
echo
echo "CURL_RC=$?"
