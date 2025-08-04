#!/bin/bash
set -euo pipefail

# Pull data from the Petfinder API and save to pets.json
# Usage: ./1_dump_pets_from_api_2json_file.sh [type] [size] [zip_code] [limit]

CLIENT_ID="${PETFINDER_CLIENT_ID:?Set PETFINDER_CLIENT_ID}"
CLIENT_SECRET="${PETFINDER_CLIENT_SECRET:?Set PETFINDER_CLIENT_SECRET}"

what="${1:-cat}"
size="${2:-small}"
zip_code="${3:-ZZZZ}"
limit="${4:-100}"

token_response=$(curl -s -d "grant_type=client_credentials&client_id=${CLIENT_ID}&client_secret=${CLIENT_SECRET}" https://api.petfinder.com/v2/oauth2/token)
BR=$(echo "$token_response" | jq -r .access_token)

if [[ -z "$BR" || "$BR" == "null" ]]; then
  echo "Failed to get bearer token from Petfinder API" >&2
  exit 1
fi

response=$(curl -s -H "Authorization: Bearer ${BR}" "https://api.petfinder.com/v2/animals?type=${what}&size=${size}&location=${zip_code}&limit=${limit}")

if [[ -z "$response" ]]; then
  echo "No data received from Petfinder API" >&2
  exit 1
fi

echo "$response" | jq . > pets.json

echo "Pet data successfully written to pets.json"