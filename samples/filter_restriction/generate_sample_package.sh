#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SAMPLE_FILE="$SCRIPT_DIR/lennox_filter_restriction_monitor_package_sample.yaml"

usage() {
    cat >&2 <<'EOF'
Usage: generate_sample_package.sh OUTPUT_FILE SYSTEM_PREFIX

Generate an installation-specific package from
lennox_filter_restriction_monitor_package_sample.yaml.

Arguments:
  OUTPUT_FILE   Path to the generated package YAML.
  SYSTEM_PREFIX System prefix such as upstairs, downstairs, or main_house.
EOF
}

if [[ $# -ne 2 ]]; then
    usage
    exit 1
fi

OUTPUT_FILE="$1"
SYSTEM_PREFIX="$2"

SYSTEM_LABEL="$(printf '%s' "$SYSTEM_PREFIX" | sed 's/_/ /g' | awk '{for(i=1;i<=NF;i++){$i=toupper(substr($i,1,1)) substr($i,2)}; print}')"

if [[ ! -f "$SAMPLE_FILE" ]]; then
    echo "Sample file not found: $SAMPLE_FILE" >&2
    exit 1
fi

mkdir -p "$(dirname "$OUTPUT_FILE")"

python3 - "$SAMPLE_FILE" "$SYSTEM_PREFIX" "$SYSTEM_LABEL" "$OUTPUT_FILE" <<'PY'
from pathlib import Path
import re
import sys

sample_path = Path(sys.argv[1])
system_prefix = sys.argv[2]
system_label = sys.argv[3]
output_path = Path(sys.argv[4])

SYSTEM_PREFIX = "SYSTEM_PREFIX"
SYSTEM_LABEL = "SYSTEM_LABEL"

content = sample_path.read_text()

# Remove generic-only guidance comments from generated output.
content = re.sub(
    r"\n# GENERATED-ONLY-STRIP-START\n.*?# GENERATED-ONLY-STRIP-END\n",
    "\n",
    content,
    flags=re.DOTALL,
)

content = re.sub(r"(# - watchdog automation\n)#\n#", r"\1#", content, count=1)

# Replace explicit placeholders in entity ids, unique_ids, references,
# helper names, and user-facing labels.
content = content.replace(SYSTEM_PREFIX, system_prefix)
content = content.replace(SYSTEM_LABEL, system_label)

output_path.write_text(content)
PY

echo "Generated package: $OUTPUT_FILE"
