# SubsPy - Income & Expense Management

<p align="center">
  <img src="src/assets/icon_new.png" alt="SubsPy Logo" width="128"/>
</p>

Greek version of the README is available at [README.md](README.md).

An income and expense management application built with **Python** and **Flet**.
Runs on Windows, macOS, Linux, Raspberry Pi, and Android.

## Features

- 📋 **Entries** — Add, edit, and delete income and expense records.
- 📅 **Recurring Transactions** — Subscriptions, salaries, and periodic entries (e.g., monthly or customized day intervals).
- 📊 **Reports & Running Balances** — Running balances and summaries for any selected date range.
- 📄 **PDF Export** — Color-coded PDF reports (green = income, red = expenses) with complete balance breakdown.
- 🏷️ **Categories** — Organize transactions into custom categories.
- 💾 **Backup & Restore** — Export and import all application data via JSON.
- 🔎 **Instant & Analog Zoom** — Direct zoom buttons (+ / - / click percentage to reset), plus smooth `Ctrl` + mouse wheel scaling.
- 📐 **Dynamic Table Layout** — Columns automatically expand to fill 100% of the screen width, with a pinned bottom horizontal scrollbar when zooming.
- ❔ **Built-in Instructions** — Spacious, comfortable help window available in both Greek and English.
- 🖼️ **Native Splash Screen** — Instant startup screen featuring the currency bicycle emblem (€ and $ wheels).
- 🌍 **Bilingual Support** — Full UI support for Greek and English.
- 🖥️ **Cross-platform** — Native experience across Windows, macOS, Linux, Raspberry Pi, and Android.

## Running the Application (Release)

To run the application, download the pre-built standalone executable of the latest release (e.g., `subspy.exe` for Windows) from the [Releases](https://github.com/spyalekos/subspy/releases) page and run it directly without installing external dependencies.

## Usage

### 📋 Entries
- Click **"+ Add"** in the top control group to create a new entry.
- Select **Income** or **Expense** from the type picker.
- Specify date, description, amount, category, and recurrence days.
- Click any table row to edit or delete that entry.
- Recurrence: `0` = one-off entry, `30` = monthly, `365` = annual.

### 📊 Reports
1. Switch to the **"Reports"** tab.
2. Select start ("From") and end ("To") dates.
3. Click **"Generate"** to compute running balances and list all matching transactions.
4. Click **"Print PDF"** to create and view the printable PDF report.

### 🛠️ Tools
- **Export**: Exports all transactions and categories into a JSON backup file.
- **Import**: Restores records from a previously exported JSON backup.
- **Categories**: Create new or delete existing custom categories.

### 🔍 Zoom Controls & Help
- **Zoom In / Out**: Use the **+** and **-** buttons on the top bar or hold `Ctrl` and scroll the mouse wheel.
- **Reset Zoom**: Click directly on the zoom percentage button (e.g., **100%**) to immediately return to default scaling.
- **Help**: Click the **?** button at the top right for detailed built-in guidance.

## Data Storage

| Platform | Database Location (`subscriptions.db`) |
|----------|----------------------------------------|
| Windows | Next to the `subspy.exe` file |
| Linux / Raspberry Pi | `~/subscriptions.db` |
| macOS | `~/Library/Application Support/SubsPy/subscriptions.db` |
| Android | Application internal private storage |

## Technologies

- [Python](https://www.python.org/) 3.10+
- [Flet](https://flet.dev/) 1.0+ — Modern Cross-platform UI Framework
- [SQLite](https://sqlite.org/) — Embedded local database
- [ReportLab](https://www.reportlab.com/) — PDF generation engine
- [Pillow](https://python-pillow.org/) — Image asset processing and rendering

## Version History

**v5.0.3** — October 2026
- Removed obsolete image assets from the repository to optimize release package size.
- Harmonized and structured user documentation (README in Greek and English).

**v5.0.2** — October 2026
- Clean, text-free splash screen and refreshed currency bicycle icon (€ / $ wheels).
- Polished asset integration in the standalone executable.

**v5.0.1** — October 2026
- New application icon and branding featuring a currency bicycle with Euro (€) and Dollar ($) wheels.
- Added native bootloader splash screen.
- Published updated release executable.

**v5.0.0** — October 2026
- Upgraded to Flet 1.0.5 and modernized runtime dependencies.
- Table columns now dynamically expand to occupy the full width of the screen.
- Added direct zoom buttons (+ / - / click percentage to reset) and smooth `Ctrl` + mouse wheel zoom.
- Permanently visible bottom horizontal scrollbar when zooming beyond 125%.
- Enlarged instructions dialog (800px) with comfortable typography.

**v4.09** — July 2026
- Compatibility fixes and resolution of executable startup errors.

**v4.08** — June 2026
- Replaced transform-based zoom with true `DataTable` sizing for accurate scrollbar calculations.

**v4.07** — June 2026
- Layout optimizations for horizontal scrolling stability.

**v4.06** — June 2026
- Fixed vertical scrolling in zoomed view to prevent row truncation.

**v4.05** — June 2026
- Visible horizontal and vertical scrollbars for Entries and Reports tables.

**v4.04** — June 2026
- Relocated **+ Add** button to the top toolbar with green highlight.
- Enhanced dynamic zoom boundary calculations.

**v4.03** — June 2026
- Refined toolbar controls layout and safe screen margin constraints.

**v4.02** — June 2026
- Integrated in-app instructions dialog and analog zoom support.

**v4.01** — March 2026
- Icon and UI rendering fixes.

**v4.00** — March 2026
- Running balances in Reports and PDF exports.
- Support for monthly recurrence intervals.
- Portable `subscriptions.db` database alongside executable on Windows.
- Layout enhancements and bug fixes.

**v2.0** — February 2026
- Complete income and expense tracking.
- Cross-platform support (Windows, macOS, Linux, Android, Raspberry Pi).
- Greek DatePickers.
- Color-coded PDF export.
- Category management and JSON backup/restore.

**v1.0** — December 2025
- Initial release for subscription management.

## License

MIT License
