#!/bin/sh
# Usage: ./loadgen.sh [base_url]   (traffic generator for dashboards)
URL=${1:-http://localhost}
while true; do
  for m in none none none none slow error; do
    curl -s -o /dev/null -X POST "$URL/api/order" -H 'Content-Type: application/json' \
      -d "{\"item\":\"laptop\",\"qty\":1,\"simulate\":\"$m\"}"
    sleep 0.5
  done
done
