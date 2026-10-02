# Phase 2 Quickstart & Validation Guide

**Feature**: Phase 2 — Domain Entities & XDG Configuration Engine  
**Date**: 2026-10-02  
**Status**: Completed  

---

## 1. Automated Test Execution

Run the complete Phase 2 test suite including unit, integration, and regression tests:

```bash
# Run all unit tests for domain entities and configuration
pytest tests/unit/test_models.py tests/unit/test_config.py -v

# Run Phase 1 regression tests (must remain 100% passing)
pytest tests/unit/test_legacy_baseline.py -v

# Run Phase 2 E2E workflow tests
pytest tests/e2e/test_config_e2e.py -v

# Run entire test suite
pytest -v
```

---

## 2. End-to-End Manual Verification Scenarios

### Scenario 1: Permission Safety in Read-Only Directories (DEF-003 Reproduction)
Verifies that the CLI operates and saves settings without permissions issues even when the script directory is read-only.

```bash
# 1. Create a temporary read-only directory
TMP_APP_DIR=$(mktemp -d)
cp f2m.py pyproject.toml "$TMP_APP_DIR/"
cp -r f2m/ "$TMP_APP_DIR/"
chmod -R 555 "$TMP_APP_DIR"  # Read-only permissions

# 2. Set an isolated HOME for test
TEST_HOME=$(mktemp -d)

# 3. Run config command from read-only directory
HOME="$TEST_HOME" python3 "$TMP_APP_DIR/f2m.py" config set proxy http://127.0.0.1:8080

# 4. Verify exit code is 0 and config is written to $TEST_HOME/.config/f2m/config.ini
cat "$TEST_HOME/.config/f2m/config.ini"
# Expected: proxy = http://127.0.0.1:8080

# 5. Cleanup
chmod -R 777 "$TMP_APP_DIR"
rm -rf "$TMP_APP_DIR" "$TEST_HOME"
```

---

### Scenario 2: Legacy `f2m.conf` Migration
Verifies non-destructive migration on first launch.

```bash
# 1. Set an isolated HOME
TEST_HOME=$(mktemp -d)
MIGRATE_DIR=$(mktemp -d)
cp f2m.py pyproject.toml "$MIGRATE_DIR/"
cp -r f2m/ "$MIGRATE_DIR/"

# 2. Place a legacy f2m.conf with custom settings next to f2m.py
cat << 'EOF' > "$MIGRATE_DIR/f2m.conf"
[f2m]
base_url = https://custom.film2media.xyz
download_dir = ~/CustomMovies
EOF

# 3. Run f2m config
HOME="$TEST_HOME" python3 "$MIGRATE_DIR/f2m.py" config

# 4. Verify:
# - Legacy file still exists untouched: cat "$MIGRATE_DIR/f2m.conf"
# - New XDG file created with custom values: cat "$TEST_HOME/.config/f2m/config.ini"

# 5. Cleanup
rm -rf "$TEST_HOME" "$MIGRATE_DIR"
```

---

### Scenario 3: Environment Variable Precedence
Verifies environment variables override on-disk configuration without mutating disk.

```bash
# 1. Run config with F2M_PROXY override
F2M_PROXY="http://proxy.internal:3128" python3 f2m.py config

# Expected Output:
# proxy = http://proxy.internal:3128
```
