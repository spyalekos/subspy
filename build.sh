#!/bin/bash
# SubsPy - Build Script για Raspberry Pi
# Δημιουργεί εκτελέσιμο με PyInstaller
#
# Χρήση: ./build.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== SubsPy Build ==="
echo "Φάκελος: $SCRIPT_DIR"

# Έλεγχος αν υπάρχει το venv
if [ ! -d ".venv" ]; then
    echo "Δημιουργία virtual environment..."
    python3 -m venv .venv
    echo "Εγκατάσταση εξαρτήσεων..."
    .venv/bin/pip install flet reportlab pyinstaller
else
    echo "Βρέθηκε .venv"
    # Βεβαιώσου ότι το pyinstaller είναι εγκατεστημένο
    if ! .venv/bin/python -c "import PyInstaller" 2>/dev/null; then
        echo "Εγκατάσταση PyInstaller..."
        .venv/bin/pip install pyinstaller
    fi
fi

echo ""
echo "Μεταγλώττιση με PyInstaller..."
.venv/bin/pyinstaller subspy.spec --clean --noconfirm

echo ""
echo "=== Ολοκληρώθηκε! ==="
ls -lh dist/subspy
echo ""
echo "Εκτέλεση: ./dist/subspy"
