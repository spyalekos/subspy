#!/bin/bash
# ===================================================================
# SubsPy - Cross-Platform Build Reference
# ===================================================================
#
# PREREQUISITES:
#   - Python 3.10+
#   - Flet CLI: pip install flet
#   - Flutter SDK (για flet build εντολές)
#   - Για Android: Android SDK
#   - Για iOS/macOS: Mac + Xcode
#
# ΣΗΜΕΙΩΣΗ: Κάθε flet build εντολή πρέπει να τρέχει στο
# αντίστοιχο λειτουργικό σύστημα (εκτός Android).
# ===================================================================

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

show_help() {
    echo "Χρήση: ./build_all.sh [ΕΝΤΟΛΗ]"
    echo ""
    echo "Διαθέσιμες εντολές:"
    echo "  rpi       - Build για Raspberry Pi (PyInstaller)"
    echo "  linux     - Build για Linux (Flet CLI)"
    echo "  windows   - Build για Windows (τρέχει μόνο σε Windows)"
    echo "  macos     - Build για macOS (τρέχει μόνο σε Mac)"
    echo "  apk       - Build Android APK"
    echo "  aab       - Build Android App Bundle (Play Store)"
    echo "  web       - Build Web App"
    echo "  run       - Τρέξε την εφαρμογή τοπικά"
    echo ""
    echo "Παραδείγματα:"
    echo "  ./build_all.sh rpi"
    echo "  ./build_all.sh apk"
    echo "  ./build_all.sh run"
}

case "${1:-help}" in
    rpi)
        echo "=== Build για Raspberry Pi (PyInstaller) ==="
        ./build.sh
        ;;
    linux)
        echo "=== Build για Linux ==="
        flet build linux
        ;;
    windows)
        echo "=== Build για Windows ==="
        echo "ΣΗΜΕΙΩΣΗ: Αυτή η εντολή πρέπει να τρέχει σε Windows."
        flet build windows
        ;;
    macos)
        echo "=== Build για macOS ==="
        echo "ΣΗΜΕΙΩΣΗ: Αυτή η εντολή πρέπει να τρέχει σε Mac."
        flet build macos
        ;;
    apk)
        echo "=== Build Android APK ==="
        flet build apk
        ;;
    aab)
        echo "=== Build Android App Bundle ==="
        flet build aab
        ;;
    web)
        echo "=== Build Web App ==="
        flet build web
        ;;
    run)
        echo "=== Εκτέλεση εφαρμογής ==="
        if [ -f ".venv/bin/python" ]; then
            .venv/bin/python src/main.py
        else
            python3 src/main.py
        fi
        ;;
    help|*)
        show_help
        ;;
esac
