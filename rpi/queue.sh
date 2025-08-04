#!/bin/bash

# Improved queue.sh script for ESP32-petfinder
# This script moves raw files to the webserver root directory under a static filename.
# It ensures the ESP32 device can access the expected file with robust error handling,
# configurable parameters, timestamped logging, and file archiving.

# Configurable parameters (can be overridden by env vars or args)
SOURCE_DIR="${1:-${SOURCE_DIR:-.}}"
DEST_FILE="${2:-${DEST_FILE:-/var/www/html/256.my_photo.jpg.raw}}"
ARCHIVE_DIR="${3:-${ARCHIVE_DIR:-./archive}}"
LOG_FILE="${LOG_FILE:-/var/log/queue_script.log}"

# Create archive directory if it doesn't exist
mkdir -p "$ARCHIVE_DIR"

# Logging function with timestamps
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $*" | tee -a "$LOG_FILE"
}

log "Starting queue.sh with SOURCE_DIR=$SOURCE_DIR, DEST_FILE=$DEST_FILE, ARCHIVE_DIR=$ARCHIVE_DIR"

# Infinite loop to process files
while true; do
    found_any=false
    
    # Find and process raw files in the source directory
    for FILE in "$SOURCE_DIR"/*.raw; do
        # Skip if no matching files (glob didn't expand)
        [ ! -f "$FILE" ] && continue
        found_any=true

        log "Processing file: $FILE"
        
        # Check if destination file is already in use
        if [[ -f "$DEST_FILE" ]]; then
            log "Destination file $DEST_FILE exists, waiting..."
            sleep 5
        else
            # Copy file to destination with error handling
            if cp "$FILE" "$DEST_FILE"; then
                log "Copied $FILE to $DEST_FILE"
                
                # Wait for ESP32 to process the file
                sleep 25
                
                # Archive the processed file with error handling
                if mv "$FILE" "$ARCHIVE_DIR/"; then
                    log "Archived $FILE"
                else
                    log "Failed to archive $FILE"
                fi
            else
                log "Error copying $FILE to $DEST_FILE"
            fi
        fi
    done
    
    # Only sleep if no files were found to avoid log spam
    if ! $found_any; then
        sleep 5
    fi
done
