# SubsPy - Διαχείριση Εσόδων & Εξόδων

<p align="center">
  <img src="src/assets/icon_new.png" alt="SubsPy Logo" width="120"/>
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
- ❔ **Οδηγίες στην εφαρμογή** — Εικονίδιο βοήθειας στο επάνω μέρος με οδηγίες στα Ελληνικά και Αγγλικά
- 🔎 **Αναλογικό zoom** — `Ctrl` + ρόδα ποντικιού για δυναμική μεγέθυνση/σμίκρυνση με ασφαλές όριο πλάτους
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

# Συγχρονισμός εξαρτήσεων
uv sync
```

### Εκτέλεση

```bash
# Με Flet CLI (hot reload)
uv run flet run src

# Ή απευθείας
uv run python src/main.py
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
2. Πατήστε **«Δημιουργία»** για υπολογισμό προοδευτικών υπόλοιπων
3. Πατήστε **«Εκτύπωση PDF»** για εξαγωγή αναφοράς

### 🛠️ Εργαλεία
- **Εξαγωγή**: Αποθηκεύει όλα τα δεδομένα σε αρχείο JSON
- **Εισαγωγή**: Επαναφορά δεδομένων από αρχείο JSON
- **Κατηγορίες**: Προσθήκη και διαγραφή κατηγοριών

### ❔ Οδηγίες και zoom
- Πατήστε το εικονίδιο **?** στο επάνω μέρος για σύντομες οδηγίες στα Ελληνικά και Αγγλικά
- Το **+ Προσθήκη** βρίσκεται στο επάνω control group, δίπλα στην ένδειξη zoom και στη βοήθεια
- Κρατήστε πατημένο το `Ctrl` και γυρίστε τη ρόδα του ποντικιού για αναλογικό zoom. Το zoom σταματά πριν βγει εκτός οθόνης η περιοχή της στήλης «Κατηγορία».
- Οι πίνακες Καταχωρήσεων και Αναφορών έχουν εμφανείς μπάρες κύλισης για οριζόντια και κάθετη πλοήγηση.

## English Quick Notes

- Use the top **?** icon for built-in Greek/English instructions.
- Use the green **Add** button in the top control group next to zoom and help.
- Hold `Ctrl` and use the mouse wheel to scale the UI up or down. Zoom stops before the Category column area is pushed off screen.
- Entries and Reports tables show scrollbars for horizontal and vertical navigation.

## Δομή έργου

```
subspy/
├── src/
│   ├── main.py            # Κύρια εφαρμογή Flet
│   ├── version.py         # Hardcoded έκδοση εφαρμογής
│   ├── database.py        # SQLite βάση δεδομένων
│   ├── pdf_export.py      # Δημιουργία PDF (ReportLab)
│   ├── platform_utils.py  # Ανίχνευση πλατφόρμας & cross-platform paths
│   └── assets/            # Εικονίδια & splash screens
├── pyproject.toml         # Ρυθμίσεις & εξαρτήσεις
├── main.spec              # Τρέχον PyInstaller spec
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
| **Linux** | `uv run flet build linux` | Flet CLI + Flutter |
| **Windows** | `uv run flet build windows` | Μόνο σε Windows |
| **macOS** | `uv run flet build macos` | Μόνο σε Mac + Xcode |
| **Android APK** | `uv run flet build apk` | Android SDK |
| **Android AAB** | `uv run flet build aab` | Για Play Store |
| **Web** | `uv run flet build web` | Static web app |

Το τρέχον PyInstaller spec είναι το `main.spec` και η εντολή build για `.exe` είναι:

```bash
uv run pyinstaller main.spec
```

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
| Windows | Δίπλα στο αρχείο `subspy.exe` |
| macOS | `~/Library/Application Support/SubsPy/subscriptions.db` |
| Android | Εσωτερικός χώρος εφαρμογής |

## Τεχνολογίες

- [Flet](https://flet.dev/) 0.80+ — Cross-platform UI framework
- [SQLite](https://sqlite.org/) — Τοπική βάση δεδομένων
- [ReportLab](https://www.reportlab.com/) — Δημιουργία PDF

## Ιστορικό εκδόσεων

**v4.08** — Ιούνιος 2026
- Αντικαταστάθηκε το transform-based zoom με πραγματικές διαστάσεις `DataTable`, ώστε οι μπάρες κύλισης να υπολογίζουν σωστά το πλήρες ύψος του grid.
- Οι πίνακες Καταχωρήσεων και Αναφορών κάνουν zoom σε ύψη γραμμών, headers, αποστάσεις στηλών, κείμενα και εικονίδια χωρίς να κόβονται οι κάτω γραμμές.

**v4.07** — Ιούνιος 2026
- Διορθώθηκε το κόψιμο του grid δεξιά κατά το zoom, αφαιρώντας τη λανθασμένη προσαρμογή λογικού πλάτους
- Το zoom layout προσαρμόζει πλέον μόνο το ύψος για κάθετη κύλιση, χωρίς να στενεύει τον πίνακα

**v4.06** — Ιούνιος 2026
- Διορθώθηκε το κάθετο scroll σε zoomed προβολή ώστε να μην κόβονται οι τελευταίες γραμμές κάτω από την κάτω μπάρα
- Το zoomed περιεχόμενο τοποθετείται πλέον σε clipped layout slot με ύψος προσαρμοσμένο στο τρέχον zoom

**v4.05** — Ιούνιος 2026
- Προστέθηκαν εμφανείς μπάρες κύλισης στους πίνακες Καταχωρήσεων και Αναφορών
- Οι πίνακες τυλίγονται πλέον σε οριζόντιο και κάθετο scroll container

**v4.04** — Ιούνιος 2026
- Μεταφέρθηκε το **+ Προσθήκη** στο επάνω control group δίπλα στο zoom και τη βοήθεια, με πράσινο χρώμα
- Αυξήθηκε το δυναμικό όριο zoom ώστε η στήλη «Κατηγορία» να μπορεί να φτάνει πολύ πιο κοντά στο δεξί άκρο

**v4.03** — Ιούνιος 2026
- Μετακινήθηκε η ένδειξη zoom και το εικονίδιο οδηγιών πιο κοντά στο πλάτος του πίνακα, αντί για το δεξί άκρο της οθόνης
- Προστέθηκε ασφαλές όριο zoom βάσει πλάτους παραθύρου ώστε η στήλη «Κατηγορία» να παραμένει ορατή

**v4.02** — Ιούνιος 2026
- Προστέθηκε επάνω εικονίδιο οδηγιών με περιεχόμενο στα Ελληνικά και Αγγλικά
- Προστέθηκε αναλογικό zoom όλου του UI με `Ctrl` + ρόδα ποντικιού
- Ευθυγραμμίστηκε η έκδοση σε `pyproject.toml` και `src/version.py`
- Προστέθηκε τρέχον `main.spec` για PyInstaller build

**v4.01** — Μάρτιος 2026
- Διορθώσεις στην απεικόνιση του νέου εικονιδίου μέσα στην ίδια την εφαρμογή και στο README

**v4.00** — Μάρτιος 2026
- Προοδευτικά υπόλοιπα (Running balances) στις αναφορές και στα PDF
- Επαναλαμβανόμενες κινήσεις "Κάθε μήνα" εκτός από υπολογισμό ημερών
- Φορητή βάση δεδομένων `subscriptions.db` (στα Windows, πλέον δίπλα στο `.exe`)
- Νέο εικονίδιο εφαρμογής
- Layout & Bug fixes

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
