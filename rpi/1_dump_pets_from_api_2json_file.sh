#!/bin/bash
set -euo pipefail

# --------------------------------------------
# Petfinder API Data Dump Script (Enhanced)
# --------------------------------------------
#
# Usage:
#   ./1_dump_pets_from_api_2json_file.sh [type] [size] [zip_code] [limit] [output_file] [--compact] [--verbose] [additional api params]
#
# Example:
#   ./1_dump_pets_from_api_2json_file.sh dog medium 10001 50 dogs.json --verbose breed=beagle age=young
#
# Description of arguments:
#   [type]         animal type: dog, cat, rabbit, small-furry, horse, bird, scales-fins-other, barnyard
#   [size]         animal size: small, medium, large, xlarge
#   [zip_code]     5-digit US ZIP code
#   [limit]        number of records to fetch (max 100)
#   [output_file]  path to json output file
#   --compact      output compact JSON instead of pretty-printed
#   --verbose      output debug information to stderr
#   [additional]   any valid Petfinder API key=value param (e.g. breed=beagle)
#
# .env template:
#   PETFINDER_CLIENT_ID=your_client_id
#   PETFINDER_CLIENT_SECRET=your_secret
#
# This script sources .env if present in the working directory.

# Known valid types and sizes for validation
VALID_TYPES=(dog cat rabbit "small-furry" horse bird "scales-fins-other" barnyard)
VALID_SIZES=(small medium large xlarge)

# 1. Dependency checks
for dep in curl jq; do
  if ! command -v "$dep" &>/dev/null; then
    echo "Error: $dep is not installed. Please install it to proceed." >&2
    exit 1
  fi
done

# 2. Source environment from .env if present
if [[ -f .env ]]; then
  set -o allexport
  source .env
  set +o allexport
fi

# 3. Environment variable checks
if [[ -z "
${PETFINDER_CLIENT_ID:-}" || -z "${PETFINDER_CLIENT_SECRET:-}" ]]; then
  echo "Error: PETFINDER_CLIENT_ID and PETFINDER_CLIENT_SECRET must be set in your environment or .env file." >&2
  exit 1
fi

CLIENT_ID="$PETFINDER_CLIENT_ID"
CLIENT_SECRET="$PETFINDER_CLIENT_SECRET"

# 4. Input parsing and validation
what="${1:-cat}"
size="${2:-small}"
zip_code="${3:-10001}"
limit="${4:-100}"
output_file="${5:-pets.json}"

# Remove positional args
shift $(( ${#@} > 4 ? 5 : ${#@} ))

# Flags
COMPACT=false
VERBOSE=false
EXTRA_PARAMS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --compact) COMPACT=true;;
    --verbose) VERBOSE=true;;
    *=*) EXTRA_PARAMS+=("$1");;
  esac
  shift
done

# Output debug messages if VERBOSE is on
debug() { $VERBOSE && echo "[DEBUG] $*" >&2; }

# Validate type
if [[ ! " ${VALID_TYPES[@]} " =~ " $what " ]]; then
  echo "Error: Invalid animal type: $what. Valid: ${VALID_TYPES[*]}" >&2
  exit 1
fi
# Validate size
if [[ ! " ${VALID_SIZES[@]} " =~ " $size " ]]; then
  echo "Error: Invalid animal size: $size. Valid: ${VALID_SIZES[*]}" >&2
  exit 1
fi
# Validate zip code
if ! [[ "$zip_code" =~ ^[0-9]{5}$ ]]; then
  echo "Error: ZIP code must be a 5-digit number." >&2
  exit 1
fi
# Validate limit
if ! [[ "$limit" =~ ^[0-9]+$ ]]; then
  echo "Error: Limit must be a numeric value." >&2
  exit 1
fi

# 5. Petfinder API token caching (1 hour), using XDG_RUNTIME_DIR if set
CACHE_DIR="${XDG_RUNTIME_DIR:-/tmp}"  # Use /tmp if XDG_RUNTIME_DIR is not set
TOKEN_FILE="$CACHE_DIR/petfinder_token_${USER:-pet}"
TOKEN_EXPIRY_FILE="$CACHE_DIR/petfinder_token_expiry_${USER:-pet}"
current_time=$(date +%s)
token_valid=false

if [[ -f "$TOKEN_FILE" && -f "$TOKEN_EXPIRY_FILE" ]]; then
  expiry=$(cat "$TOKEN_EXPIRY_FILE")
  if [[ "$current_time" -lt "$expiry" ]]; then
    BR=$(cat "$TOKEN_FILE")
    token_valid=true
    debug "Using cached token."
  fi
fi

if [[ "$token_valid" != true ]]; then
  debug "Requesting new token from Petfinder."
  retries=3
  while (( retries > 0 )); do
    token_response=$(curl -s -w "\n%{http_code}" -d "grant_type=client_credentials&client_id=${CLIENT_ID}&client_secret=${CLIENT_SECRET}" "https://api.petfinder.com/v2/oauth2/token")
    http_code=$(echo "$token_response" | tail -n1)
    token_json=$(echo "$token_response" | head -n-1)
    if [[ "$http_code" == "200" ]]; then
      BR=$(echo "$token_json" | jq -r .access_token)
      expires_in=$(echo "$token_json" | jq -r .expires_in)
      if [[ -n "$BR" && "$BR" != "null" ]]; then
        echo "$BR" > "$TOKEN_FILE"
        echo $((current_time + expires_in - 60)) > "$TOKEN_EXPIRY_FILE"
        break
      fi
    else
      debug "Token request failed (HTTP $http_code). Retrying..."
    fi
    ((retries--))
    sleep 2
  done
  if [[ -z "${BR:-}" ]]; then
    echo "Failed to get bearer token from Petfinder API" >&2
    exit 1
  fi
fi

# 6. Build API params string
PARAMS="type=${what}&size=${size}&location=${zip_code}&limit=${limit}"
for kv in "${EXTRA_PARAMS[@]}"; do
  PARAMS+="&$kv"
done

# 7. Fetch animal data with retry (rate-limit aware)
retries=3
response=""
while (( retries > 0 )); do
  api_response=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer ${BR}" \
    "https://api.petfinder.com/v2/animals?$PARAMS")
  http_code=$(echo "$api_response" | tail -n1)
  response=$(echo "$api_response" | head -n-1)
  if [[ "$http_code" == "200" ]]; then
    break
  elif [[ "$http_code" == "429" ]]; then
    debug "Rate limited. Sleeping before retry..."
    sleep 5
  else
    debug "API call failed (HTTP $http_code). Retrying..."
    sleep 2
  fi
  ((retries--))
done
if [[ -z "$response" ]]; then
  echo "No data received from Petfinder API after multiple attempts" >&2
  exit 1
fi

# 8. JSON Schema Validation (expect .animals as array)
if ! echo "$response" | jq -e '.animals | arrays' >/dev/null 2>&1; then
  echo "API response not valid or missing .animals array" >&2
  if $VERBOSE; then
    echo "$response" >&2
  fi
  exit 1
fi

# 9. Output to file (pretty or compact)
if $COMPACT; then
  echo "$response" | jq -c . > "$output_file"
else
  echo "$response" | jq . > "$output_file"
fi

echo "Pet data successfully written to $output_file"