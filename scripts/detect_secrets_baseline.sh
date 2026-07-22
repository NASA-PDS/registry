#!/bin/bash
# Single source of truth for detect-secrets arguments.
# Per-repo exclusions go in .detect-secrets-ignore (one regex per line, # for comments).
#
# Usage:
#   scripts/detect_secrets_baseline.sh scan   # Regenerate .secrets.baseline
#   scripts/detect_secrets_baseline.sh audit  # Interactively audit .secrets.baseline
#   scripts/detect_secrets_baseline.sh        # Check for new secrets vs baseline
set -e

# Prefer venv's detect-secrets over system install
if [ -f ".venv/bin/detect-secrets" ]; then
    DETECT_SECRETS=".venv/bin/detect-secrets"
else
    DETECT_SECRETS="detect-secrets"
fi

# Global excludes applied in every repo
GLOBAL_EXCLUDES=(
    '\.secrets\..*'
    '\.git.*'
    '\.pre-commit-config\.yaml'
    '\.mypy_cache'
    '\.pytest_cache'
    '\.tox'
    '\.venv'
    'venv'
    'dist'
    'build'
    '.*\.egg-info'
    'scripts/detect_secrets_baseline\.sh'
)

EXCLUDE_ARGS=()
for pat in "${GLOBAL_EXCLUDES[@]}"; do
    EXCLUDE_ARGS+=(--exclude-files "$pat")
done

# Per-repo excludes from .detect-secrets-ignore (one regex per line, # comments ok)
if [ -f .detect-secrets-ignore ]; then
    while IFS= read -r line || [ -n "$line" ]; do
        [[ "$line" =~ ^[[:space:]]*# ]] && continue
        [[ -z "${line// }" ]] && continue
        EXCLUDE_ARGS+=(--exclude-files "$line")
    done < .detect-secrets-ignore
fi

compare_secrets() {
    diff \
        <(python3 -c "
import json, sys
with open(sys.argv[1]) as f: data = json.load(f)
lines = [f\"{k},{s['hashed_secret']}\" for k, v in data.get('results', {}).items() for s in v]
print('\n'.join(sorted(lines)))
" "$1") \
        <(python3 -c "
import json, sys
with open(sys.argv[1]) as f: data = json.load(f)
lines = [f\"{k},{s['hashed_secret']}\" for k, v in data.get('results', {}).items() for s in v]
print('\n'.join(sorted(lines)))
" "$2") \
        >/dev/null
}

if [ "$1" = "scan" ]; then
    $DETECT_SECRETS scan "${EXCLUDE_ARGS[@]}" > .secrets.baseline
    echo "Updated .secrets.baseline"
    echo "Next step: run 'scripts/detect_secrets_baseline.sh audit' to review and classify detected secrets."
elif [ "$1" = "audit" ]; then
    $DETECT_SECRETS audit .secrets.baseline
else
    # Check 1: Fail if any secrets in the baseline have not been audited
    unaudited=$(python3 -c "
import json, sys
with open('.secrets.baseline') as f: data = json.load(f)
count = sum(1 for v in data.get('results', {}).values() for s in v if 'is_secret' not in s)
print(count)
")
    if [ "$unaudited" -gt 0 ]; then
        echo "⚠️ Attention Required! ⚠️" >&2
        echo "$unaudited secret(s) in .secrets.baseline have not been audited." >&2
        echo "Run 'scripts/detect_secrets_baseline.sh audit' to review and classify each detected secret." >&2
        exit 1
    fi

    # Check 2: Fail if any new secrets are detected that are not in the baseline
    cp .secrets.baseline .secrets.new
    $DETECT_SECRETS scan "${EXCLUDE_ARGS[@]}" --baseline .secrets.new

    if ! compare_secrets .secrets.baseline .secrets.new; then
        echo "⚠️ Attention Required! ⚠️" >&2
        echo "New secrets have been detected in your recent commit. Due to security concerns, we cannot display detailed information here and we cannot proceed until this issue is resolved." >&2
        echo "" >&2
        echo "Please follow the steps below on your local machine to reveal and handle the secrets:" >&2
        echo "" >&2
        echo "1️⃣ Run the 'detect-secrets' tool on your local machine. This tool will identify and clean up the secrets. You can find detailed instructions at this link: https://nasa-ammos.github.io/slim/continuous-testing/starter-kits/#detect-secrets" >&2
        echo "" >&2
        echo "2️⃣ After cleaning up the secrets, commit your changes and re-push your update to the repository." >&2
        echo "" >&2
        echo "Your efforts to maintain the security of our codebase are greatly appreciated!" >&2
        rm -f .secrets.new
        exit 1
    fi

    rm -f .secrets.new
fi
