#!/bin/bash

# Build a JSON pipeline file from a Painless source file.
# This script properly escapes JSON special characters.

set -e

if [ $# -ne 3 ]; then
    echo "Usage: build_json.sh <painless_file> <json_file> <description>" >&2
    exit 1
fi

painless_file="$1"
json_file="$2"
description="$3"

# Read painless source and join into single line (stripping empty lines)
source=""
while IFS= read -r line || [ -n "$line" ]; do
    trimmed_line="${line#"${line%%[![:space:]]*}"}"
    trimmed_line="${trimmed_line%"${trimmed_line##*[![:space:]]}"}"
    if [ -n "$trimmed_line" ]; then
        if [ -z "$source" ]; then
            source="$trimmed_line"
        else
            source="$source $trimmed_line"
        fi
    fi
done < "$painless_file"

# Escape special characters for JSON using sed
# Escape backslash, double quote, forward slash, AND &
escaped_source=$(printf '%s' "$source" | sed 's/\\/\\\\/g; s/"/\\"/g; s/\//\\\//g; s/&/\\&/g')

# Write JSON file (avoid variable expansion in heredoc)
cat > "$json_file" <<'JSONEOF'
{
  "description": "DESCRIPTION_PLACEHOLDER",
  "processors": [
    {
      "script": {
        "lang": "painless",
        "source": "SOURCE_PLACEHOLDER"
      }
    }
  ]
}
JSONEOF

# Replace placeholders with actual values
sed "s/DESCRIPTION_PLACEHOLDER/$description/g; s/SOURCE_PLACEHOLDER/$escaped_source/g" "$json_file" > "${json_file}.tmp"
mv "${json_file}.tmp" "$json_file"

echo "Built: $json_file"

