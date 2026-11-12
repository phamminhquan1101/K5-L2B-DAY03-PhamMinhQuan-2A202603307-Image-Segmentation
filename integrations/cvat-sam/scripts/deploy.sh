#!/usr/bin/env bash
set -euo pipefail
root=$1
device=$2
project=$3
project_directory=$4
network=$5
shift 5
nuctl="$root/.cache/nuctl"
chmod +x "$nuctl"
compose=(docker compose --project-name "$project" --project-directory "$project_directory")
for compose_file in "$@"; do
    compose+=(-f "$compose_file")
done
compose+=(-f "$root/compose.override.yml")
# Validate before changing services. Only recreate the two services receiving an override.
"${compose[@]}" config --quiet
"${compose[@]}" up -d --no-deps nuclio cvat_server cvat_worker_annotation
for attempt in $(seq 1 60); do
    if curl --fail --silent http://localhost:8070/api/projects >/dev/null; then break; fi
    sleep 1
done
curl --fail --silent http://localhost:8070/api/projects >/dev/null
if ! "$nuctl" get project cvat --platform local >/dev/null 2>&1; then
    "$nuctl" create project cvat --platform local
fi
config="$root/nuclio/mobilesam/function.yaml"
if [ "$device" = gpu ]; then config="$root/nuclio/mobilesam/function-gpu.yaml"; fi
"$nuctl" deploy --project-name cvat --platform local \
    --path "$root/nuclio/mobilesam" --file "$config" \
    --platform-config "{\"attributes\":{\"network\":\"$network\"}}"
"$nuctl" get functions --platform local
