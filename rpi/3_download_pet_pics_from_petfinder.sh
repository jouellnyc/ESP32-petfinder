#!/bin/bash

# Enhanced pet picture downloader with robust error handling and logging
# Downloads pet images listed in pets.wget.queue.txt with various configuration options
#
# Usage:
#   ./3_download_pet_pics_from_petfinder.sh
#
# Environment Variables:
#   SLEEP_DURATION   - Sleep time between downloads in seconds (default: 1)
#   DOWNLOAD_DIR     - Directory to save downloaded images (default: current directory)
#   DRY_RUN          - Set to "true" to preview downloads without downloading (default: false)
#
# Examples:
#   DRY_RUN=true ./3_download_pet_pics_from_petfinder.sh
#   DOWNLOAD_DIR=images SLEEP_DURATION=2 ./3_download_pet_pics_from_petfinder.sh

# Configuration variables with defaults
SLEEP_DURATION="${SLEEP_DURATION:-1}"
DOWNLOAD_DIR="${DOWNLOAD_DIR:-.}"
DRY_RUN="${DRY_RUN:-false}"
QUEUE_FILE="pets.wget.queue.txt"

# Ensure logs directory exists
mkdir -p logs

# Function to log with timestamp
log_message() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "logs/${level,,}.log"
}

# Function to validate URL format
is_valid_url() {
    local url="$1"
    [[ "$url" =~ ^https?:// ]]
}

# Check if wget is installed
if ! command -v wget &> /dev/null; then
    log_message "ERROR" "wget is not installed. Please install wget before running this script."
    exit 1
fi

# Check if pets.wget.queue.txt exists
if [ ! -f "$QUEUE_FILE" ]; then
    log_message "ERROR" "pets.wget.queue.txt not found in current directory"
    exit 1
fi

# Create download directory if it doesn't exist
if [ "$DOWNLOAD_DIR" != "." ]; then
    mkdir -p "$DOWNLOAD_DIR"
    if [ $? -ne 0 ]; then
        log_message "ERROR" "Failed to create download directory: $DOWNLOAD_DIR"
        exit 1
    fi
fi

log_message "INFO" "Starting pet picture download process"
log_message "INFO" "Configuration: SLEEP_DURATION=$SLEEP_DURATION, DOWNLOAD_DIR=$DOWNLOAD_DIR, DRY_RUN=$DRY_RUN"

# Counters for summary
total_lines=0
valid_lines=0
downloaded=0
skipped=0
failed=0

# Main processing loop
while IFS=':' read -r name pic || [ -n "$name" ]; do
    total_lines=$((total_lines + 1))
    
    # Skip empty lines
    if [ -z "$name" ] && [ -z "$pic" ]; then
        continue
    fi
    
    # Validate line format (must contain both name and pic)
    if [ -z "$name" ] || [ -z "$pic" ]; then
        log_message "ERROR" "Invalid line format at line $total_lines: missing name or URL"
        continue
    fi
    
    # Validate URL format
    if ! is_valid_url "$pic"; then
        log_message "ERROR" "Invalid URL format for '$name': $pic (must start with http:// or https://)"
        continue
    fi
    
    valid_lines=$((valid_lines + 1))
    
    # Construct full file path
    file_path="${DOWNLOAD_DIR}/${name}.jpg"
    
    # Check if file already exists
    if [ -f "$file_path" ]; then
        log_message "SKIPPED" "File already exists: ${name}.jpg"
        skipped=$((skipped + 1))
    else
        if [ "$DRY_RUN" = "true" ]; then
            log_message "DRY_RUN" "Would download: $name from $pic to $file_path"
        else
            # Attempt to download the file
            log_message "INFO" "Downloading: $name from $pic"
            if wget -q -O "$file_path" "$pic" 2>/dev/null; then
                log_message "SUCCESS" "Downloaded: ${name}.jpg"
                downloaded=$((downloaded + 1))
            else
                log_message "ERROR" "Failed to download: $name from $pic"
                failed=$((failed + 1))
                # Clean up failed download file if it exists
                [ -f "$file_path" ] && rm -f "$file_path"
            fi
        fi
    fi
    
    # Sleep between downloads (unless in dry run mode)
    if [ "$DRY_RUN" != "true" ]; then
        sleep "$SLEEP_DURATION"
    fi
    
done < "$QUEUE_FILE"

# Print summary
log_message "INFO" "Download process completed"
log_message "INFO" "Summary: Total lines: $total_lines, Valid lines: $valid_lines, Downloaded: $downloaded, Skipped: $skipped, Failed: $failed"
