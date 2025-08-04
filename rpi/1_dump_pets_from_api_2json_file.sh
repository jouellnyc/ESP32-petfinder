#!/bin/bash
set -euo pipefail

# --------------------------------------------
# Petfinder API Data Dump Script (Full Rewrite)
# --------------------------------------------
#
# Usage:
#   ./1_dump_pets_from_api_2json_file.sh [type] [size] [zip_code] [limit] [output_file]
#
# Example:
#   ./1_dump_pets_from_api_2json_file.sh dog medium 10001 50 dogs.json
#

# 1. Dependency checks
for dep in curl jq; do
  if ! command -v "$dep" &>/dev/null; then
    echo "Error: $dep is not installed. Please install it to proceed." >&2
    exit 1
  fi
done

# 2. Environment variable checks
if [[ -z "
${PETFINDER_CLIENT_ID:-}" || -z "${PETFINDER_CLIENT_SECRET:-}" ]]; then
  echo "Error: PETFINDER_CLIENT_ID and PETFINDER_CLIENT_SECRET must be set in your environment." >&2
  exit 1
fi

CLIENT_ID="$PETFINDER_CLIENT_ID"
CLIENT_SECRET="$PETFINDER_CLIENT_SECRET"

# 3. Input parsing and validation
what="${1:-cat}"
size="${2:-small}"
zip_code="${3:-10001}"
limit="${4:-100}"
output_file="${5:-pets.json}"

if ! [[ "$zip_code" =~ ^[0-9]{5}$ ]]; then
  echo "Error: ZIP code must be a 5-digit number." >&2
  exit 1
fi

if ! [[ "$limit" =~ ^[0-9]+$ ]]; then
  echo "Error: Limit must be a numeric value." >&2
  exit 1
fi

# 4. Petfinder API token caching (1 hour)
TOKEN_FILE="/tmp/petfinder_token"
TOKEN_EXPIRY_FILE="/tmp/petfinder_token_expiry"
current_time=$(date +%s)
token_valid=false

if [[ -f "$TOKEN_FILE" && -f "$TOKEN_EXPIRY_FILE" ]]; then
  expiry=$(cat "$TOKEN_EXPIRY_FILE")
  if [[ "$current_time" -lt "$expiry" ]]; then
    BR=$(cat "$TOKEN_FILE")
    token_valid=true
  fi
fi

if [[ "$token_valid" != true ]]; then
  token_response=$(curl -s -d "grant_type=client_credentials&client_id=${CLIENT_ID}&client_secret=${CLIENT_SECRET}" "https://api.petfinder.com/v2/oauth2/token")
  BR=$(echo "$token_response" | jq -r .access_token)
  expires_in=$(echo "$token_response" | jq -r .expires_in)
  if [[ -z "$BR" || "$BR" == "null" ]]; then
    echo "Failed to get bearer token from Petfinder API" >&2
    exit 1
  fi
  echo "$BR" > "$TOKEN_FILE"
  echo $((current_time + expires_in - 60)) > "$TOKEN_EXPIRY_FILE"
fi

# 5. Fetch animal data
response=$(curl -s -H "Authorization: Bearer ${BR}" \
  "https://api.petfinder.com/v2/animals?type=${what}&size=${size}&location=${zip_code}&limit=${limit}")

if [[ -z "$response" ]]; then
  echo "No data received from Petfinder API" >&2
  exit 1
fi

# 6. Output to file
echo "$response" | jq . > "$output_file"
echo "Pet data successfully written to $output_file"