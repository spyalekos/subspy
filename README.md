# SubsPy - Εφαρμογή Διαχείρισης Εσόδων & Εξόδων

Μια cross-platform εφαρμογή για τη διαχείριση εσόδων και εξόδων, κατασκευασμένη με Python και Flet.

## Χαρακτηριστικά

- 📋 **Διαχείριση Εσόδων/Εξόδων** — Προσθήκη, επεξεργασία και διαγραφή καταχωρήσεων
- 📅 **Επαναλαμβανόμενες Κινήσεις** — Υποστήριξη για μη-επαναλαμβανόμενες και επαναλαμβανόμενες (π.χ. συνδρομές, μισθοί)
- 📊 **Προοδευτικές Αναφορές** — Υπολογισμός χρεώσεων για οποιοδήποτε χρονικό διάστημα
- 📄 **Εξαγωγή PDF** — Δημιουργία PDF αναφορών με έγχρωμη διάκριση εσόδων/εξόδων
- 🏷️ **Κατηγοριοποίηση** — Οργάνωση με προσαρμοσμένες κατηγορίες
- 💾 **Εξαγωγή/Εισαγωγή** — Backup και επαναφορά δεδομένων σε JSON
- 🌍 **Ελληνική Γλώσσα** — Πλήρης υποστήριξη ελληνικών
- 🖥️ **Cross-Platform** — Windows, macOS, Linux, Raspberry Pi, Android

## Εγκατάσταση

### Απαιτήσεις
- Python 3.10+

### Εγκατάσταση εξαρτήσεων

```bash
# Δημιουργία virtual environment
python3 -m venv .venv
source .venv/bin/activate    # Linux/Mac
# .venv\Scripts\activate     # Windows

pip install flet reportlab
```

### Εκτέλεση

```bash
.venv/bin/python src/main.py
```

## Χρήση

### Καταχωρήσεις
- Πατήστε **"Προσθήκη"** για νέα καταχώρηση (έσοδο ή έξοδο)
- Κάντε κλικ σε μια καταχώρηση για επεξεργασία ή διαγραφή
- **Επανάληψη 0** = μη επαναλαμβανόμενη κίνηση

### Αναφορές
1. Επιλέξτε ημερομηνίες "Από" και "Έως"
2. Πατήστε **"Δημιουργία"** για υπολογισμό χρεώσεων
3. Πατήστε **"Εκτύπωση PDF"** για εξαγωγή

### Εργαλεία
- **Εξαγωγή**: Αποθηκεύει τα δεδομένα σε JSON
- **Εισαγωγή**: Επαναφορά δεδομένων από JSON (με FilePicker ή χειροκίνητη εισαγωγή path)
- **Κατηγορίες**: Διαχείριση προσαρμοσμένων κατηγοριών

## Τεχνολογίες

- **Flet 0.80+** — Cross-platform UI framework
- **SQLite** — Τοπική βάση δεδομένων
- **ReportLab** — Δημιουργία PDF

## Δομή Έργου

```
subspy/
├── src/
│   ├── main.py            # Κύρια εφαρμογή Flet
│   ├── database.py        # Λειτουργίες βάσης δεδομένων
│   ├── pdf_export.py      # Δημιουργία PDF
│   └── platform_utils.py  # Cross-platform utilities
├── pyproject.toml         # Εξαρτήσεις έργου
├── build.sh               # Build script (Raspberry Pi / PyInstaller)
├── build_all.sh           # Cross-platform build reference
└── README.md              # Τεκμηρίωση
```

## Build για διαφορετικές πλατφόρμες

> **Σημείωση**: Τα `flet build` commands χρειάζονται [Flutter SDK](https://docs.flutter.dev/get-started/install).

| Πλατφόρμα | Εντολή | Σημειώσεις |
|-----------|--------|------------|
| **Raspberry Pi** | `./build.sh` | PyInstaller, τρέχει τοπικά |
| **Linux** | `flet build linux` | Flet CLI |
| **Windows** | `flet build windows` | Μόνο σε Windows |
| **macOS** | `flet build macos` | Μόνο σε Mac + Xcode |
| **Android APK** | `flet build apk` | Χρειάζεται Android SDK |
| **Android AAB** | `flet build aab` | Για Play Store |
| **Web** | `flet build web` | Static web app |

Ή χρησιμοποιήστε το `build_all.sh`:
```bash
./build_all.sh rpi    # Raspberry Pi
./build_all.sh apk    # Android APK
./build_all.sh run    # Τρέξε τοπικά
```

## Αποθήκευση Δεδομένων

| Πλατφόρμα | Τοποθεσία Βάσης Δεδομένων |
|-----------|--------------------------|
| Linux / Raspberry Pi | `~/subscriptions.db` |
| Windows | `%APPDATA%\SubsPy\subscriptions.db` |
| macOS | `~/Library/Application Support/SubsPy/subscriptions.db` |
| Android | Εσωτερικός χώρος αποθήκευσης εφαρμογής |

## Έκδοση

**v2.0** (Φεβρουάριος 2026)
- Διαχείριση εσόδων και εξόδων
- Cross-platform υποστήριξη (Windows, macOS, Linux, Android, RPi)
- FilePicker για εισαγωγή JSON
- Ελληνικά DatePickers
- Εξαγωγή PDF με έγχρωμη διάκριση
- Διαχείριση κατηγοριών

## Άδεια

MIT License

## Συγγραφέας

Alekos