# SubsPy - Income & Expense Management

<p align="center">
  <img src="src/assets/icon_new.png" alt="SubsPy Logo" width="120"/>
</p>

An income and expense management application built with **Python** and **Flet**.
Runs on Windows, macOS, Linux, Raspberry Pi, and Android.

## Features

- 📋 **Entries** — Add, edit, and delete income/expenses
- 📅 **Recurring transactions** — Subscriptions, salaries, and other periodic transactions (e.g., every 30 days)
- 📊 **Reports** — Running balances for any selected time period
- 📄 **PDF Export** — Report export in PDF format with color differentiation (green = income, red = expenses)
- 🏷️ **Categories** — Organize transactions into custom categories
- 💾 **Backup/Restore** — Export and import data in JSON format
- ❔ **In-App Instructions** — Help icon at the top with instructions in Greek and English
- 🔎 **Analog zoom** — `Ctrl` + mouse wheel for dynamic zoom in/out with safe width limit
- 🌍 **Bilingual** — UI support for both Greek and English
- 🖥️ **Cross-platform** — Windows, macOS, Linux, Raspberry Pi, Android

## Application Execution (Release)

To run the application, download the corresponding release executable (e.g., `subspy.exe` for Windows) from the repository's Releases page and run it directly.

## Usage

### 📋 Entries
- Press **"Add"** to create a new entry
- Select **Income** or **Expense** from the picker
- Set the date, amount, category, and recurrence days
- Click on any row to edit or delete the entry
- Recurrence `0` = single transaction, `30` = monthly, `365` = annual

### 📊 Reports
1. Select "From" and "To" dates
2. Press **"Generate"** to calculate running balances
3. Press **"Print PDF"** to export the report

### 🛠️ Tools
- **Export**: Saves all data to a JSON file
- **Import**: Restores data from a JSON file
- **Categories**: Add and delete categories

### ❔ Instructions and Zoom
- Press the **?** icon at the top for brief instructions in Greek and English
- The green **Add** button is located in the top control group next to zoom and help
- Hold `Ctrl` and spin the mouse wheel for analog zoom. Zoom stops before the "Category" column is pushed off-screen
- Both Entries and Reports tables feature scrollbars for horizontal and vertical navigation

## Data Storage

| Platform | Database Location |
|----------|-------------------|
| Linux / Raspberry Pi | `~/subscriptions.db` |
| Windows | Next to the `subspy.exe` file |
| macOS | `~/Library/Application Support/SubsPy/subscriptions.db` |
| Android | Application internal storage |

## Technologies

- [Flet](https://flet.dev/) 0.80+ — Cross-platform UI framework
- [SQLite](https://sqlite.org/) — Local database
- [ReportLab](https://www.reportlab.com/) — PDF generation

## Version History

**v5.0.2** — October 2026
- Clean, text-free splash screen and refreshed currency bicycle icon (€ / $ wheels).
- New standalone release executable featuring the updated splash screen.

**v5.0.1** — October 2026
- New application icon and branding featuring a currency bicycle with Euro (€) and Dollar ($) wheels.
- Added visual splash screen during application launch.
- Built and published standalone release executable with integrated bootloader splash.

**v5.0.0** — October 2026
- Upgraded to Flet 1.0.5 and modernized dependencies.
- Table columns now dynamically expand to occupy the full width of the screen.
- Smooth mouse wheel zoom with `Ctrl` + wheel featuring rate-limiting and instant responsiveness.
- Direct header zoom buttons (+ / - / click 100% to reset).
- Permanently visible bottom horizontal scrollbar when zooming beyond 125%.
- Enlarged instructions dialog (800px) with larger, easily readable typography.

**v4.09** — July 2026
- Fixed the padding `AttributeError` that prevented the compiled executable from running.
- Locally excluded the `.agents` folder from the Git repository.
- Cleaned README.md of development and compilation instructions.

**v4.08** — June 2026
- Replaced transform-based zoom with actual `DataTable` sizing so that scrollbars correctly calculate grid height.
- Entries and Reports tables zoom row heights, headers, column spacing, texts, and icons without cutting off bottom rows.

**v4.07** — June 2026
- Fixed table cutting off on the right when zooming by removing logical width adjustments.
- Zoom layout now only adjusts height for vertical scroll without narrowing the table.

**v4.06** — June 2026
- Fixed vertical scroll in zoomed view to prevent cutting off bottom rows under the scroll bar.
- Zoomed content is now placed in a clipped layout slot with height adjusted to current zoom.

**v4.05** — June 2026
- Added visible scrollbars to Entries and Reports tables.
- Tables are now wrapped in horizontal and vertical scroll containers.

**v4.04** — June 2026
- Moved the green **Add** button to the top control group next to zoom and help.
- Increased dynamic zoom limit so the "Category" column can get closer to the right edge.

**v4.03** — June 2026
- Moved the zoom indicator and instructions icon closer to the table width instead of the right edge of the screen.
- Added safe zoom limit based on window width to keep the "Category" column visible.

**v4.02** — June 2026
- Added top instructions icon with Greek and English content.
- Added analog zoom for the entire UI using `Ctrl` + mouse wheel.
- Synced version in `pyproject.toml` and `src/version.py`.
- Added current `main.spec` for PyInstaller build.

**v4.01** — March 2026
- UI fixes for the new icon inside the app and in the README.

**v4.00** — March 2026
- Running balances in reports and PDFs.
- Recurring transactions "Every month" in addition to day intervals.
- Portable database `subscriptions.db` (next to `.exe` on Windows).
- New application icon.
- Layout & Bug fixes.

**v2.0** — February 2026
- Income and expense management (instead of only subscriptions).
- Cross-platform support (Windows, macOS, Linux, Android, Raspberry Pi).
- Greek DatePickers.
- PDF export with color-coded income/expenses.
- Category management.
- Data export/import in JSON.

**v1.0** — December 2025
- Initial release — subscription management.
- Voice assistant integration.
- Raspberry Pi only.

## License

MIT License

## Author

**SpyAlekos** — [spyalekos@gmail.com](mailto:spyalekos@gmail.com)
