# SubsPy - Διαχείριση Εσόδων & Εξόδων

<p align="center">
  <img src="src/assets/icon.png" alt="SubsPy Logo" width="120"/>
</p>

Εφαρμογή διαχείρισης εσόδων και εξόδων, κατασκευασμένη με **Python** και **Flet**.
Τρέχει σε Windows, macOS, Linux, Raspberry Pi και Android.

## Χαρακτηριστικά

- 📋 **Καταχωρήσεις** — Προσθήκη, επεξεργασία και διαγραφή εσόδων/εξόδων
- 📅 **Επαναλαμβανόμενες κινήσεις** — Συνδρομές, μισθοί και άλλες περιοδικές κινήσεις (π.χ. κάθε 30 ημέρες)
- 📊 **Αναφορές** — Προοδευτικές χρεώσεις για οποιοδήποτε χρονικό διάστημα
- 📄 **Εξαγωγή PDF** — Αναφορά σε PDF με έγχρωμη διάκριση (πράσινο = έσοδα, κόκκινο = έξοδα)
- 🏷️ **Κατηγορίες** — Οργάνωση κινήσεων σε προσαρμοσμένες κατηγορίες
- 💾 **Backup/Restore** — Εξαγωγή και εισαγωγή δεδομένων σε JSON
- 🌍 **Ελληνικά** — Πλήρες ελληνικό UI (μενού, DatePickers, μηνύματα)
- 🖥️ **Cross-platform** — Windows, macOS, Linux, Raspberry Pi, Android

## Γρήγορη εκκίνηση

### Απαιτήσεις
- Python 3.10+

### Εγκατάσταση

```bash
# Κλωνοποίηση
git clone https://github.com/spyalekos/subspy.git
cd subspy

# Δημιουργία virtual environment
python3 -m venv .venv
source .venv/bin/activate    # Linux/Mac
# .venv\Scripts\activate     # Windows

# Εγκατάσταση εξαρτήσεων
pip install flet reportlab
```

### Εκτέλεση

```bash
# Με Flet CLI (hot reload)
flet run src

# Ή απευθείας
.venv/bin/python src/main.py
```

## Χρήση

### 📋 Καταχωρήσεις
- Πατήστε **«Προσθήκη»** για νέα εγγραφή
- Επιλέξτε **Έσοδο** ή **Έξοδο** από τον επιλογέα
- Ορίστε ημερομηνία, ποσό, κατηγορία και ημέρες επανάληψης
- Πατήστε σε μια γραμμή για επεξεργασία ή διαγραφή
- Επανάληψη `0` = μοναδική κίνηση, `30` = μηνιαία, `365` = ετήσια

### 📊 Αναφορές
1. Επιλέξτε ημερομηνίες «Από» και «Έως»
2. Πατήστε **«Δημιουργία»** για υπολογισμό χρεώσεων
3. Πατήστε **«Εκτύπωση PDF»** για εξαγωγή αναφοράς

### 🛠️ Εργαλεία
- **Εξαγωγή**: Αποθηκεύει όλα τα δεδομένα σε αρχείο JSON
- **Εισαγωγή**: Επαναφορά δεδομένων από αρχείο JSON
- **Κατηγορίες**: Προσθήκη και διαγραφή κατηγοριών

## Δομή έργου

```
subspy/
├── src/
│   ├── main.py            # Κύρια εφαρμογή Flet
│   ├── database.py        # SQLite βάση δεδομένων
│   ├── pdf_export.py      # Δημιουργία PDF (ReportLab)
│   ├── platform_utils.py  # Ανίχνευση πλατφόρμας & cross-platform paths
│   └── assets/            # Εικονίδια & splash screens
├── pyproject.toml         # Ρυθμίσεις & εξαρτήσεις
├── build.sh               # PyInstaller build (Raspberry Pi)
├── build_all.sh           # Build reference script (όλες οι πλατφόρμες)
└── README.md
```

## Build

> **Σημείωση**: Για `flet build` χρειάζεται [Flutter SDK](https://docs.flutter.dev/get-started/install).
> Για Raspberry Pi χρησιμοποιούμε PyInstaller (δεν χρειάζεται Flutter).

| Πλατφόρμα | Εντολή | Σημειώσεις |
|-----------|--------|------------|
| **Raspberry Pi** | `./build.sh` | PyInstaller, χωρίς Flutter |
| **Linux** | `flet build linux` | Flet CLI + Flutter |
| **Windows** | `flet build windows` | Μόνο σε Windows |
| **macOS** | `flet build macos` | Μόνο σε Mac + Xcode |
| **Android APK** | `flet build apk` | Android SDK |
| **Android AAB** | `flet build aab` | Για Play Store |
| **Web** | `flet build web` | Static web app |

```bash
# Ή μέσω build_all.sh:
./build_all.sh rpi    # Raspberry Pi
./build_all.sh apk    # Android
./build_all.sh run    # Τρέξε τοπικά
```

## Αποθήκευση δεδομένων

| Πλατφόρμα | Βάση δεδομένων |
|-----------|---------------|
| Linux / Raspberry Pi | `~/subscriptions.db` |
| Windows | `%APPDATA%\SubsPy\subscriptions.db` |
| macOS | `~/Library/Application Support/SubsPy/subscriptions.db` |
| Android | Εσωτερικός χώρος εφαρμογής |

## Τεχνολογίες

- [Flet](https://flet.dev/) 0.80+ — Cross-platform UI framework
- [SQLite](https://sqlite.org/) — Τοπική βάση δεδομένων
- [ReportLab](https://www.reportlab.com/) — Δημιουργία PDF

## Ιστορικό εκδόσεων

**v2.0** — Φεβρουάριος 2026
- Διαχείριση εσόδων και εξόδων (αντί μόνο συνδρομών)
- Cross-platform υποστήριξη (Windows, macOS, Linux, Android, Raspberry Pi)
- Ελληνικά DatePickers
- Εξαγωγή PDF με έγχρωμη διάκριση εσόδων/εξόδων
- Διαχείριση κατηγοριών
- Εισαγωγή/Εξαγωγή δεδομένων σε JSON

**v1.0** — Δεκέμβριος 2025
- Αρχική έκδοση — διαχείριση συνδρομών
- Voice assistant integration
- Raspberry Pi only

## Άδεια

MIT License

## Συγγραφέας

**SpyAlekos** — [spyalekos@gmail.com](mailto:spyalekos@gmail.com)