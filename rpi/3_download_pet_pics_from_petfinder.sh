#!/bin/bash

#
# Pet Picture Downloader
# Downloads pet images from URLs listed in pets.wget.queue.txt
#
# Usage:
#   3_download_pet_pics_from_petfinder.sh [OPTIONS]
#
# Options:
#   -h, --help              Show this help message
#   -p, --parallel N        Enable parallel downloads with N simultaneous jobs (default: 1)
#   -r, --retries N         Number of retry attempts for failed downloads (default: 3)
#   -s, --sleep N           Sleep duration between downloads in seconds (default: 1)
#   -o, --output-dir DIR    Output directory for downloaded images (default: current dir)
#   -q, --queue-file FILE   Queue file to read from (default: pets.wget.queue.txt)
#   --success-log FILE      Success log filename (default: success.log)
#   --error-log FILE        Error log filename (default: error.log)
#   --skip-log FILE         Skip log filename (default: skipped.log)
#
# Environment Variables:
#   PARALLEL_DOWNLOADS      Number of parallel downloads (overridden by -p)
#   RETRY_ATTEMPTS          Number of retry attempts (overridden by -r)
#   SLEEP_DURATION          Sleep duration between downloads (overridden by -s)
#   OUTPUT_DIR              Output directory (overridden by -o)
#   SUCCESS_LOG             Success log filename (overridden by --success-log)
#   ERROR_LOG               Error log filename (overridden by --error-log)
#   SKIP_LOG                Skip log filename (overridden by --skip-log)
#

set -euo pipefail

# Default configuration (can be overridden by environment variables or arguments)
PARALLEL_DOWNLOADS=${PARALLEL_DOWNLOADS:-1}
RETRY_ATTEMPTS=${RETRY_ATTEMPTS:-3}
SLEEP_DURATION=${SLEEP_DURATION:-1}
OUTPUT_DIR=${OUTPUT_DIR:-"."}
QUEUE_FILE=${QUEUE_FILE:-"pets.wget.queue.txt"}
SUCCESS_LOG=${SUCCESS_LOG:-"success.log"}
ERROR_LOG=${ERROR_LOG:-"error.log"}
SKIP_LOG=${SKIP_LOG:-"skipped.log"}

# Global variables for script state
INTERRUPTED=0
TOTAL_PROCESSED=0
TOTAL_DOWNLOADED=0
TOTAL_SKIPPED=0
TOTAL_FAILED=0

# Function to display usage information
usage() {
    cat << 'EOF'
Pet Picture Downloader

Downloads pet images from URLs listed in pets.wget.queue.txt

Usage:
  3_download_pet_pics_from_petfinder.sh [OPTIONS]

Options:
  -h, --help              Show this help message
  -p, --parallel N        Enable parallel downloads with N simultaneous jobs (default: 1)
  -r, --retries N         Number of retry attempts for failed downloads (default: 3)
  -s, --sleep N           Sleep duration between downloads in seconds (default: 1)
  -o, --output-dir DIR    Output directory for downloaded images (default: current dir)
  -q, --queue-file FILE   Queue file to read from (default: pets.wget.queue.txt)
  --success-log FILE      Success log filename (default: success.log)
  --error-log FILE        Error log filename (default: error.log)
  --skip-log FILE         Skip log filename (default: skipped.log)

Environment Variables:
  PARALLEL_DOWNLOADS      Number of parallel downloads (overridden by -p)
  RETRY_ATTEMPTS          Number of retry attempts (overridden by -r)
  SLEEP_DURATION          Sleep duration between downloads (overridden by -s)
  OUTPUT_DIR              Output directory (overridden by -o)
  SUCCESS_LOG             Success log filename (overridden by --success-log)
  ERROR_LOG               Error log filename (overridden by --error-log)
  SKIP_LOG                Skip log filename (overridden by --skip-log)

Examples:
  # Basic usage (backward compatible)
  ./3_download_pet_pics_from_petfinder.sh

  # Parallel downloads with 5 simultaneous jobs
  ./3_download_pet_pics_from_petfinder.sh --parallel 5

  # Custom output directory and retry settings
  ./3_download_pet_pics_from_petfinder.sh --output-dir ./images --retries 5

EOF
}

# Function to get current timestamp
get_timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}

# Function to log messages with timestamps
log_message() {
    local logfile="$1"
    local message="$2"
    echo "[$(get_timestamp)] $message" >> "$logfile"
}

# Function to handle script interruption gracefully
cleanup() {
    INTERRUPTED=1
    echo ""
    echo "Interrupt received. Cleaning up..."
    
    # Wait for background jobs to finish (if any)
    wait
    
    echo "Download summary:"
    echo "  Total processed: $TOTAL_PROCESSED"
    echo "  Downloaded: $TOTAL_DOWNLOADED"
    echo "  Skipped: $TOTAL_SKIPPED"
    echo "  Failed: $TOTAL_FAILED"
    
    exit 130
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Function to validate queue file format
validate_queue_file() {
    local queue_file="$1"
    local line_num=0
    local errors=0
    
    echo "Validating queue file: $queue_file"
    
    while IFS= read -r line; do
        ((line_num++))
        
        # Skip empty lines and comments
        if [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]]; then
            continue
        fi
        
        # Check if line contains at least one colon
        if [[ "$line" != *":"* ]]; then
            echo "Error: Line $line_num has invalid format (expected name:url): $line" >&2
            ((errors++))
            continue
        fi
        
        # Extract name and URL (name is before first colon, url is everything after)
        local name="${line%%:*}"
        local url="${line#*:}"
        
        # Validate name is not empty
        if [[ -z "$name" ]]; then
            echo "Error: Line $line_num has empty name: $line" >&2
            ((errors++))
        fi
        
        # Validate URL is not empty and looks like a URL
        if [[ -z "$url" ]]; then
            echo "Error: Line $line_num has empty URL: $line" >&2
            ((errors++))
        elif [[ ! "$url" =~ ^https?:// ]]; then
            echo "Warning: Line $line_num URL doesn't start with http(s)://: $url" >&2
        fi
        
    done < "$queue_file"
    
    if [[ $errors -gt 0 ]]; then
        echo "Found $errors validation errors in $queue_file" >&2
        return 1
    fi
    
    echo "Queue file validation passed"
    return 0
}

# Function to download a single image with retry logic
download_image() {
    local name="$1"
    local url="$2"
    local output_file="$3"
    local attempt=1
    
    while [[ $attempt -le $RETRY_ATTEMPTS ]]; do
        if [[ $INTERRUPTED -eq 1 ]]; then
            return 1
        fi
        
        if wget -q --timeout=30 --tries=1 -O "$output_file" "$url" 2>/dev/null; then
            log_message "$SUCCESS_LOG" "Downloaded $name.jpg (attempt $attempt)"
            ((TOTAL_DOWNLOADED++))
            return 0
        else
            if [[ $attempt -eq $RETRY_ATTEMPTS ]]; then
                log_message "$ERROR_LOG" "Failed to download $name.jpg from $url after $RETRY_ATTEMPTS attempts"
                ((TOTAL_FAILED++))
                # Remove partial download if it exists
                [[ -f "$output_file" ]] && rm -f "$output_file"
                return 1
            else
                # Don't echo this in production mode to reduce noise
                # echo "Download attempt $attempt failed for $name.jpg, retrying..." >&2
                ((attempt++))
                sleep 1
            fi
        fi
    done
}

# Function to process a single line from the queue
process_line() {
    local line="$1"
    
    # Skip empty lines and comments
    if [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]]; then
        return 0
    fi
    
    # Extract name and URL
    local name="${line%%:*}"
    local url="${line#*:}"
    local output_file="$OUTPUT_DIR/${name}.jpg"
    
    ((TOTAL_PROCESSED++))
    
    # Only download if file does not already exist
    if [[ ! -f "$output_file" ]]; then
        download_image "$name" "$url" "$output_file" || true  # Don't fail script on download failure
        
        # Sleep between downloads (only in single-threaded mode)
        if [[ $PARALLEL_DOWNLOADS -eq 1 && $SLEEP_DURATION -gt 0 ]]; then
            sleep "$SLEEP_DURATION"
        fi
    else
        log_message "$SKIP_LOG" "Skipped $name.jpg, file already exists"
        ((TOTAL_SKIPPED++))
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -p|--parallel)
            PARALLEL_DOWNLOADS="$2"
            shift 2
            ;;
        -r|--retries)
            RETRY_ATTEMPTS="$2"
            shift 2
            ;;
        -s|--sleep)
            SLEEP_DURATION="$2"
            shift 2
            ;;
        -o|--output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -q|--queue-file)
            QUEUE_FILE="$2"
            shift 2
            ;;
        --success-log)
            SUCCESS_LOG="$2"
            shift 2
            ;;
        --error-log)
            ERROR_LOG="$2"
            shift 2
            ;;
        --skip-log)
            SKIP_LOG="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1" >&2
            echo "Use --help for usage information" >&2
            exit 1
            ;;
    esac
done

# Validate arguments
if [[ ! "$PARALLEL_DOWNLOADS" =~ ^[1-9][0-9]*$ ]]; then
    echo "Error: Parallel downloads must be a positive integer" >&2
    exit 1
fi

if [[ ! "$RETRY_ATTEMPTS" =~ ^[1-9][0-9]*$ ]]; then
    echo "Error: Retry attempts must be a positive integer" >&2
    exit 1
fi

if [[ ! "$SLEEP_DURATION" =~ ^[0-9]+$ ]]; then
    echo "Error: Sleep duration must be a non-negative integer" >&2
    exit 1
fi

# Ensure output directory exists
if [[ ! -d "$OUTPUT_DIR" ]]; then
    mkdir -p "$OUTPUT_DIR" || {
        echo "Error: Cannot create output directory: $OUTPUT_DIR" >&2
        exit 1
    }
fi

# Fail if queue file does not exist
if [[ ! -f "$QUEUE_FILE" ]]; then
    echo "Error: $QUEUE_FILE not found" >&2
    exit 1
fi

# Validate queue file format
if ! validate_queue_file "$QUEUE_FILE"; then
    echo "Error: Queue file validation failed" >&2
    exit 1
fi

echo "Starting pet picture downloads..."
echo "Configuration:"
echo "  Queue file: $QUEUE_FILE"
echo "  Output directory: $OUTPUT_DIR"
echo "  Parallel downloads: $PARALLEL_DOWNLOADS"
echo "  Retry attempts: $RETRY_ATTEMPTS"
echo "  Sleep duration: ${SLEEP_DURATION}s"
echo "  Success log: $SUCCESS_LOG"
echo "  Error log: $ERROR_LOG"
echo "  Skip log: $SKIP_LOG"
echo ""

# Process the queue file
if [[ $PARALLEL_DOWNLOADS -eq 1 ]]; then
    # Single-threaded processing (backward compatible)
    while IFS= read -r line; do
        if [[ $INTERRUPTED -eq 1 ]]; then
            break
        fi
        process_line "$line"
    done < "$QUEUE_FILE"
else
    # Parallel processing
    echo "Using parallel downloads with $PARALLEL_DOWNLOADS simultaneous jobs"
    
    # Process lines and manage parallel jobs
    job_count=0
    while IFS= read -r line; do
        if [[ $INTERRUPTED -eq 1 ]]; then
            break
        fi
        
        # Skip empty lines and comments
        if [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]]; then
            continue
        fi
        
        # Wait if we've reached the parallel limit
        while [[ $job_count -ge $PARALLEL_DOWNLOADS ]]; do
            if wait -n; then
                ((job_count--))
            fi
        done
        
        # Start background job
        process_line "$line" &
        ((job_count++))
        
    done < "$QUEUE_FILE"
    
    # Wait for all remaining jobs to complete
    wait
fi

# Final summary
echo ""
echo "Download completed!"
echo "Summary:"
echo "  Total processed: $TOTAL_PROCESSED"
echo "  Downloaded: $TOTAL_DOWNLOADED"
echo "  Skipped: $TOTAL_SKIPPED"  
echo "  Failed: $TOTAL_FAILED"
