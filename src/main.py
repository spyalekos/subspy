"""
SubsPy - Εφαρμογή Διαχείρισης Εσόδων & Εξόδων
Cross-platform income/expense management with Flet.
Compatible with Flet 0.80+
"""

import flet as ft
from datetime import datetime, timedelta
from typing import Optional
import os

import database as db
from pdf_export import generate_report_pdf, get_default_pdf_path, REPORTLAB_AVAILABLE
from platform_utils import get_documents_dir, open_file_with_default_app, get_platform
from version import VERSION

APP_VERSION = VERSION


def main(page: ft.Page):
    """Main application entry point."""
    page.title = f"SubsPy - Διαχείριση Εσόδων & Εξόδων v{APP_VERSION}"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    
    # Set the window and app icon (looks in assets_dir)
    page.window.icon = "icon_new.png"
    # Set Greek locale for DatePickers
    page.locale_configuration = ft.LocaleConfiguration(
        supported_locales=[ft.Locale("el", "GR")],
        current_locale=ft.Locale("el", "GR"),
    )
    
    # State
    selected_subscription_id: Optional[int] = None
    selected_tab_index = 0
    dlg_selected_date = datetime.now()
    report_from_date = datetime.now()
    report_to_date = datetime.now() + timedelta(days=30)
    zoom_scale = 1.0
    ctrl_pressed = False
    ZOOM_MIN = 0.75
    ZOOM_MAX = 2.2
    CATEGORY_SAFE_WIDTH = 910
    NAV_RESERVED_HEIGHT = 90
    MIN_ZOOM_BODY_HEIGHT = 260
    
    # ==================== HELPER FUNCTIONS ====================
    
    # Create a persistent snackbar
    snackbar = ft.SnackBar(content=ft.Text(""))
    page.overlay.append(snackbar)
    
    def show_snackbar(message: str, error: bool = False):
        """Show a snackbar message."""
        snackbar.content = ft.Text(message)
        snackbar.bgcolor = ft.Colors.RED_400 if error else ft.Colors.GREEN_400
        snackbar.open = True
        page.update()
    
    def get_categories_list() -> list:
        """Get all categories from database."""
        return db.get_all_categories()

    def is_control_key(key: str) -> bool:
        """Return True for common Flet/Flutter labels of the Ctrl key."""
        normalized = (key or "").lower()
        return "control" in normalized or normalized in {"ctrl", "controlleft", "controlright"}
    
    # ==================== ENTRY DIALOG ====================
    
    dlg_description = ft.TextField(
        label="Περιγραφή",
        autofocus=True,
        expand=True
    )
    dlg_amount = ft.TextField(
        label="Ποσό (€)",
        keyboard_type=ft.KeyboardType.NUMBER,
        width=120
    )
    dlg_repeat_mode = ft.Dropdown(
        label="Τύπος Επανάληψης",
        width=180,
        options=[
            ft.dropdown.Option("days", "Ανά ημέρες"),
            ft.dropdown.Option("monthly", "Κάθε μήνα")
        ],
        value="days"
    )
    dlg_repeat_days = ft.TextField(
        label="Επανάληψη (ημέρες)",
        keyboard_type=ft.KeyboardType.NUMBER,
        width=120,
        value="0"
    )
    
    def on_repeat_mode_change(e):
        if dlg_repeat_mode.value == "monthly":
            dlg_repeat_days.visible = False
        else:
            dlg_repeat_days.visible = True
        page.update()
        
    dlg_repeat_mode.on_change = on_repeat_mode_change
    dlg_category = ft.Dropdown(
        label="Κατηγορία",
        width=200,
        options=[]
    )
    dlg_entry_type = ft.SegmentedButton(
        selected=["expense"],
        segments=[
            ft.Segment(value="expense", label=ft.Text("Έξοδο"), icon=ft.Icon(ft.CupertinoIcons.ARROW_DOWN, color=ft.Colors.RED_700)),
            ft.Segment(value="income", label=ft.Text("Έσοδο"), icon=ft.Icon(ft.CupertinoIcons.ARROW_UP, color=ft.Colors.GREEN_700)),
        ],
    )
    dlg_date_text = ft.Text("", size=14)
    
    dlg_delete_button = ft.TextButton(
        "Διαγραφή",
        icon=ft.CupertinoIcons.TRASH,
        style=ft.ButtonStyle(color=ft.Colors.RED_400),
        visible=False
    )
    
    def close_subscription_dialog(e=None):
        page.pop_dialog()
        page.update()
    
    def save_subscription(e):
        nonlocal selected_subscription_id, dlg_selected_date
        
        description = dlg_description.value.strip() if dlg_description.value else ""
        if not description:
            show_snackbar("Παρακαλώ εισάγετε περιγραφή.", error=True)
            return
        
        try:
            amount = float(dlg_amount.value.replace(',', '.'))
        except (ValueError, AttributeError):
            show_snackbar("Μη έγκυρο ποσό.", error=True)
            return
        
        try:
            repeat_days = int(dlg_repeat_days.value or "0")
        except ValueError:
            repeat_days = 0
            
        repeat_mode = dlg_repeat_mode.value or "days"
        
        charge_date = dlg_selected_date.strftime("%Y-%m-%d")
        category = dlg_category.value or ""
        entry_type = list(dlg_entry_type.selected)[0] if dlg_entry_type.selected else "expense"
        
        if selected_subscription_id:
            db.update_subscription(
                selected_subscription_id,
                description, charge_date, amount, repeat_days, category, entry_type, repeat_mode
            )
            show_snackbar("Η καταχώρηση ενημερώθηκε!")
        else:
            db.add_subscription(description, charge_date, amount, repeat_days, category, entry_type, repeat_mode)
            show_snackbar("Η καταχώρηση προστέθηκε!")
        
        close_subscription_dialog()
        refresh_subscriptions()
    
    def delete_subscription(e):
        nonlocal selected_subscription_id
        if selected_subscription_id:
            db.delete_subscription(selected_subscription_id)
            show_snackbar("Η καταχώρηση διαγράφηκε!")
            close_subscription_dialog()
            refresh_subscriptions()
    
    dlg_delete_button.on_click = delete_subscription
    
    # Date picker for subscription dialog
    date_picker_sub = ft.DatePicker(
        first_date=datetime(2020, 1, 1),
        last_date=datetime(2100, 12, 31),
        help_text="Επιλέξτε ημερομηνία",
        cancel_text="Ακύρωση",
        confirm_text="ΟΚ",
        error_format_text="Μη έγκυρη μορφή",
        error_invalid_text="Μη έγκυρη ημερομηνία",
        field_hint_text="Ημέρα/Μήνας/Έτος",
        field_label_text="Ημερομηνία",
    )
    
    def on_date_picker_change(e):
        nonlocal dlg_selected_date
        if date_picker_sub.value:
            # Convert UTC to local timezone before extracting date
            raw = date_picker_sub.value
            local_dt = raw.astimezone() if raw.tzinfo else raw
            picked = local_dt.date()
            dlg_selected_date = datetime(picked.year, picked.month, picked.day, 12, 0, 0)
            dlg_date_text.value = dlg_selected_date.strftime("%d/%m/%Y")
            page.update()
    
    date_picker_sub.on_change = on_date_picker_change
    page.overlay.append(date_picker_sub)
    
    def open_date_picker(e):
        nonlocal dlg_selected_date
        date_picker_sub.value = dlg_selected_date
        date_picker_sub.open = True
        page.update()
    
    dlg_date_button = ft.TextButton(
        "Επιλογή Ημερομηνίας",
        icon=ft.CupertinoIcons.CALENDAR,
        on_click=open_date_picker
    )
    
    subscription_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Καταχώρηση"),
        content=ft.Container(
            width=480,
            content=ft.Column([
                dlg_entry_type,
                dlg_description,
                ft.Row([
                    dlg_date_button,
                    dlg_date_text
                ], alignment=ft.MainAxisAlignment.START),
                ft.Row([
                    dlg_amount,
                    dlg_repeat_mode,
                    dlg_repeat_days
                ]),
                dlg_category,
                ft.Text("Επανάληψη ανά 0 ημέρες = μη επαναλαμβανόμενη", size=11, italic=True, color=ft.Colors.GREY_600)
            ], tight=True, spacing=10)
        ),
        actions=[
            dlg_delete_button,
            ft.TextButton("Ακύρωση", on_click=close_subscription_dialog),
            ft.TextButton("Αποθήκευση", on_click=save_subscription)
        ],
        actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN
    )
    
    def open_subscription_dialog(subscription: Optional[dict] = None):
        nonlocal selected_subscription_id, dlg_selected_date
        
        dlg_category.options = [ft.dropdown.Option(c) for c in get_categories_list()]
        
        if subscription:
            selected_subscription_id = subscription['id']
            dlg_description.value = subscription['description']
            dlg_amount.value = str(subscription['amount'])
            dlg_repeat_mode.value = subscription.get('repeat_mode', 'days')
            dlg_repeat_days.value = str(subscription['repeat_days'])
            dlg_repeat_days.visible = (dlg_repeat_mode.value == 'days')
            dlg_category.value = subscription['category']
            dlg_entry_type.selected = [subscription.get('entry_type', 'expense')]
            dlg_selected_date = datetime.strptime(subscription['charge_date'], '%Y-%m-%d')
            dlg_date_text.value = dlg_selected_date.strftime("%d/%m/%Y")
            dlg_delete_button.visible = True
            subscription_dialog.title = ft.Text("Επεξεργασία Καταχώρησης")
        else:
            selected_subscription_id = None
            dlg_description.value = ""
            dlg_amount.value = ""
            dlg_repeat_mode.value = "days"
            dlg_repeat_days.value = "0"
            dlg_repeat_days.visible = True
            dlg_category.value = None
            dlg_entry_type.selected = ["expense"]
            dlg_selected_date = datetime.now()
            dlg_date_text.value = dlg_selected_date.strftime("%d/%m/%Y")
            dlg_delete_button.visible = False
            subscription_dialog.title = ft.Text("Νέα Καταχώρηση")
        
        page.show_dialog(subscription_dialog)
    
    # ==================== ENTRIES TAB CONTENT ====================
    
    subscriptions_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Περιγραφή", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Ημερομηνία", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Ποσό (€)", weight=ft.FontWeight.BOLD), numeric=True),
            ft.DataColumn(ft.Text("Τύπος", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Επανάληψη", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Κατηγορία", weight=ft.FontWeight.BOLD)),
        ],
        rows=[],
        border=ft.Border.all(1, ft.Colors.GREY_300),
        border_radius=8,
        heading_row_color=ft.Colors.BLUE_50,
        data_row_max_height=50,
        show_checkbox_column=False,
    )
    
    def on_row_click(subscription_id: int):
        sub = db.get_subscription_by_id(subscription_id)
        if sub:
            open_subscription_dialog(sub)
    
    def refresh_subscriptions():
        subscriptions = db.get_all_subscriptions()
        subscriptions_table.rows.clear()
        
        for sub in subscriptions:
            date_formatted = datetime.strptime(sub['charge_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
            repeat_mode = sub.get('repeat_mode', 'days')
            if repeat_mode == 'monthly':
                repeat_text = "Κάθε μήνα"
            else:
                repeat_text = f"{sub['repeat_days']} ημέρες" if sub['repeat_days'] > 0 else "Μία φορά"
            
            entry_type = sub.get('entry_type', 'expense')
            is_income = entry_type == 'income'
            amount_color = ft.Colors.GREEN_700 if is_income else ft.Colors.RED_700
            amount_prefix = "+" if is_income else "−"
            type_text = "Έσοδο" if is_income else "Έξοδο"
            type_icon = ft.CupertinoIcons.ARROW_UP if is_income else ft.CupertinoIcons.ARROW_DOWN
            type_color = ft.Colors.GREEN_700 if is_income else ft.Colors.RED_700
            
            row = ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(sub['description'])),
                    ft.DataCell(ft.Text(date_formatted)),
                    ft.DataCell(ft.Text(f"{amount_prefix}€{sub['amount']:.2f}", color=amount_color, weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Row([ft.Icon(type_icon, size=16, color=type_color), ft.Text(type_text, color=type_color)], spacing=2)),
                    ft.DataCell(ft.Text(repeat_text)),
                    ft.DataCell(ft.Text(sub['category'])),
                ],
                on_select_change=lambda e, sid=sub['id']: on_row_click(sid)
            )
            subscriptions_table.rows.append(row)
        
        page.update()
    
    def add_subscription_click(e):
        open_subscription_dialog()
    
    subscriptions_content = ft.Container(
        padding=10,
        expand=True,
        content=ft.Column([
            ft.Text("Καταχωρήσεις", size=20, weight=ft.FontWeight.BOLD),
            ft.Container(height=10),
            ft.Container(
                content=ft.Column([
                    ft.Row([subscriptions_table], scroll=ft.ScrollMode.ALWAYS)
                ], scroll=ft.ScrollMode.ALWAYS),
                expand=True
            )
        ], expand=True)
    )
    
    # ==================== REPORTS TAB CONTENT ====================
    
    report_from_text = ft.Text(report_from_date.strftime("%d/%m/%Y"), size=14)
    report_to_text = ft.Text(report_to_date.strftime("%d/%m/%Y"), size=14)
    
    report_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Ημερομηνία", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Περιγραφή", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Τύπος", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Επανάληψη", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Κατηγορία", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Ποσό (€)", weight=ft.FontWeight.BOLD), numeric=True),
            ft.DataColumn(ft.Text("Υπόλοιπο", weight=ft.FontWeight.BOLD), numeric=True),
        ],
        rows=[],
        border=ft.Border.all(1, ft.Colors.GREY_300),
        border_radius=8,
        heading_row_color=ft.Colors.ORANGE_50,
        column_spacing=20,
    )
    
    report_total_text = ft.Text("Σύνολο: €0.00", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.YELLOW_700)
    report_count_text = ft.Text("Χρεώσεις: 0", size=14)
    
    # Report date pickers
    date_picker_from = ft.DatePicker(
        first_date=datetime(2020, 1, 1),
        last_date=datetime(2100, 12, 31),
        help_text="Ημερομηνία Από",
        cancel_text="Ακύρωση",
        confirm_text="ΟΚ",
    )
    date_picker_to = ft.DatePicker(
        first_date=datetime(2020, 1, 1),
        last_date=datetime(2100, 12, 31),
        help_text="Ημερομηνία Έως",
        cancel_text="Ακύρωση",
        confirm_text="ΟΚ",
    )
    
    def on_report_from_change(e):
        nonlocal report_from_date
        if date_picker_from.value:
            # Convert UTC to local timezone before extracting date
            raw = date_picker_from.value
            local_dt = raw.astimezone() if raw.tzinfo else raw
            picked = local_dt.date()
            report_from_date = datetime(picked.year, picked.month, picked.day, 12, 0, 0)
            report_from_text.value = report_from_date.strftime("%d/%m/%Y")
            page.update()
    
    def on_report_to_change(e):
        nonlocal report_to_date
        if date_picker_to.value:
            # Convert UTC to local timezone before extracting date
            raw = date_picker_to.value
            local_dt = raw.astimezone() if raw.tzinfo else raw
            picked = local_dt.date()
            report_to_date = datetime(picked.year, picked.month, picked.day, 12, 0, 0)
            report_to_text.value = report_to_date.strftime("%d/%m/%Y")
            page.update()
    
    date_picker_from.on_change = on_report_from_change
    date_picker_to.on_change = on_report_to_change
    page.overlay.append(date_picker_from)
    page.overlay.append(date_picker_to)
    
    def open_report_from_picker(e):
        date_picker_from.value = report_from_date
        date_picker_from.open = True
        page.update()
    
    def open_report_to_picker(e):
        date_picker_to.value = report_to_date
        date_picker_to.open = True
        page.update()
    
    def refresh_report():
        from_str = report_from_date.strftime("%Y-%m-%d")
        to_str = report_to_date.strftime("%Y-%m-%d")
        
        # Calculate charges for the selected period
        charges = db.get_progressive_charges(from_str, to_str)
        
        report_table.rows.clear()
        
        running_balance = 0.0
        
        for charge in charges:
            date_formatted = datetime.strptime(charge['date'], '%Y-%m-%d').strftime('%d/%m/%Y')
            entry_type = charge.get('entry_type', 'expense')
            is_income = entry_type == 'income'
            
            if is_income:
                running_balance += charge['amount']
            else:
                running_balance -= charge['amount']
            
            amount_color = ft.Colors.GREEN_700 if is_income else ft.Colors.RED_700
            amount_prefix = "+" if is_income else "−"
            
            type_text = "Έσοδο" if is_income else "Έξοδο"
            type_icon = ft.CupertinoIcons.ARROW_UP if is_income else ft.CupertinoIcons.ARROW_DOWN
            type_color = ft.Colors.GREEN_700 if is_income else ft.Colors.RED_700
            
            # Get repeat info from the subscription
            sub_data = db.get_subscription_by_id(charge.get('subscription_id'))
            repeat_mode = sub_data.get('repeat_mode', 'days') if sub_data else 'days'
            repeat_days = sub_data['repeat_days'] if sub_data else 0
            if repeat_mode == 'monthly':
                repeat_text = "Κάθε μήνα"
            else:
                repeat_text = f"{repeat_days} ημέρες" if repeat_days > 0 else "Μία φορά"
                
            balance_color = ft.Colors.GREEN_700 if running_balance >= 0 else ft.Colors.RED_700
            balance_prefix = "+" if running_balance >= 0 else "−"
            
            row = ft.DataRow(cells=[
                ft.DataCell(ft.Text(date_formatted)),
                ft.DataCell(ft.Text(charge['description'])),
                ft.DataCell(ft.Row([ft.Icon(type_icon, size=16, color=type_color), ft.Text(type_text, color=type_color)], spacing=2)),
                ft.DataCell(ft.Text(repeat_text)),
                ft.DataCell(ft.Text(charge['category'])),
                ft.DataCell(ft.Text(f"{amount_prefix}€{charge['amount']:.2f}", color=amount_color, weight=ft.FontWeight.BOLD)),
                ft.DataCell(ft.Text(f"{balance_prefix}€{abs(running_balance):.2f}", color=balance_color, weight=ft.FontWeight.BOLD)),
            ])
            report_table.rows.append(row)
        
        # Show net balance with color
        if running_balance >= 0:
            report_total_text.value = f"Τελικό Υπόλοιπο: +€{running_balance:.2f}"
            report_total_text.color = ft.Colors.GREEN_700
        else:
            report_total_text.value = f"Τελικό Υπόλοιπο: −€{abs(running_balance):.2f}"
            report_total_text.color = ft.Colors.RED_700
        report_count_text.value = f"Κινήσεις: {len(charges)}"
        page.update()
    
    def generate_report_click(e):
        refresh_report()
    
    def export_pdf_click(e):
        if not REPORTLAB_AVAILABLE:
            show_snackbar("Η βιβλιοθήκη reportlab δεν είναι διαθέσιμη.", error=True)
            return
        
        from_str = report_from_date.strftime("%Y-%m-%d")
        to_str = report_to_date.strftime("%Y-%m-%d")
        charges = db.get_progressive_charges(from_str, to_str)
        
        pdf_path = get_default_pdf_path()
        success, message = generate_report_pdf(charges, from_str, to_str, pdf_path, report_from_date)
        
        if success:
            show_snackbar(f"PDF: {pdf_path}")
            try:
                open_file_with_default_app(pdf_path)
            except Exception as ex:
                show_snackbar(f"Δεν ήταν δυνατό το άνοιγμα: {ex}", error=True)
        else:
            show_snackbar(message, error=True)
    
    reports_content = ft.Container(
        padding=10,
        expand=True,
        content=ft.Column([
            ft.Text("Προοδευτικές Χρεώσεις", size=20, weight=ft.FontWeight.BOLD),
            ft.Container(height=10),
            ft.Row([
                ft.Column([
                    ft.Text("Από:", weight=ft.FontWeight.BOLD),
                    ft.Row([
                        ft.IconButton(icon=ft.CupertinoIcons.CALENDAR, on_click=open_report_from_picker),
                        report_from_text
                    ])
                ]),
                ft.Column([
                    ft.Text("Έως:", weight=ft.FontWeight.BOLD),
                    ft.Row([
                        ft.IconButton(icon=ft.CupertinoIcons.CALENDAR, on_click=open_report_to_picker),
                        report_to_text
                    ])
                ]),
                ft.TextButton("Δημιουργία", icon=ft.CupertinoIcons.SEARCH, on_click=generate_report_click),
                ft.TextButton("Εκτύπωση PDF", icon=ft.CupertinoIcons.DOC_TEXT, on_click=export_pdf_click),
            ], alignment=ft.MainAxisAlignment.START, spacing=20),
            ft.Container(height=10),
            ft.Row([report_count_text, report_total_text], spacing=20),
            ft.Container(height=10),
            ft.Container(
                content=ft.Column([
                    ft.Row([report_table], scroll=ft.ScrollMode.ALWAYS)
                ], scroll=ft.ScrollMode.ALWAYS),
                expand=True
            )
        ], expand=True)
    )
    
    # ==================== IMPORT/EXPORT TAB CONTENT ====================
    
    export_status = ft.Text("", size=12)
    import_status = ft.Text("", size=12)
    
    # Export path field - shows where file will be saved
    export_path_display = ft.Text("", size=11, color=ft.Colors.GREY_600, selectable=True)
    
    # Import path field - user enters path manually
    import_path_field = ft.TextField(
        label="Διαδρομή αρχείου JSON",
        hint_text="π.χ. C:\\Users\\...\\subspy_backup.json",
        expand=True,
    )
    
    # Category management
    new_category_field = ft.TextField(
        label="Νέα Κατηγορία",
        expand=True,
        on_submit=lambda e: add_category_click(e),  # Allow Enter key
    )
    categories_count_text = ft.Text("", size=12, color=ft.Colors.GREY_600)
    categories_list = ft.Column([], scroll=ft.ScrollMode.AUTO, height=200)
    
    def refresh_categories_list():
        categories_list.controls.clear()
        all_cats = get_categories_list()
        categories_count_text.value = f"Σύνολο: {len(all_cats)} κατηγορίες"
        
        if not all_cats:
            categories_list.controls.append(
                ft.Text("Δεν υπάρχουν κατηγορίες. Προσθέστε μία!", italic=True, color=ft.Colors.GREY_500)
            )
        else:
            for cat in all_cats:
                categories_list.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text(cat, expand=True, size=14),
                            ft.IconButton(
                                icon=ft.CupertinoIcons.TRASH,
                                icon_color=ft.Colors.RED_400,
                                icon_size=20,
                                tooltip=f"Διαγραφή '{cat}'",
                                on_click=lambda e, c=cat: delete_category(c)
                            )
                        ]),
                        padding=ft.padding.symmetric(horizontal=5, vertical=2),
                        border_radius=5,
                        bgcolor=ft.Colors.WHITE,
                    )
                )
        page.update()
    
    def add_category_click(e):
        new_cat = new_category_field.value.strip() if new_category_field.value else ""
        if not new_cat:
            return
        
        # Check if category already exists
        existing_cats = get_categories_list()
        if new_cat in existing_cats:
            show_snackbar(f"Η κατηγορία '{new_cat}' υπάρχει ήδη!", error=True)
            return
        
        db.add_category(new_cat)
        new_category_field.value = ""
        refresh_categories_list()
        show_snackbar(f"Κατηγορία '{new_cat}' προστέθηκε!")
    
    def delete_category(cat_name):
        """Διαγραφή κατηγορίας από τη βάση."""
        db.delete_category(cat_name)
        refresh_categories_list()
        show_snackbar(f"Κατηγορία '{cat_name}' διαγράφηκε!")
    
    def export_database_click(e):
        """Export database to JSON file."""
        default_filename = f"subspy_backup_{datetime.now().strftime('%Y%m%d')}.json"
        export_path = os.path.join(get_documents_dir(), default_filename)
        
        success, message = db.export_database(export_path)
        if success:
            export_status.value = f"Εξαγωγή επιτυχής: {message}"
            export_status.color = ft.Colors.GREEN_700
            export_path_display.value = f"Αποθηκεύτηκε: {export_path}"
        else:
            export_status.value = message
            export_status.color = ft.Colors.RED_700
            export_path_display.value = ""
        page.update()
    
    def import_database_click(e):
        """Execute the import from JSON file."""
        import_path = import_path_field.value.strip() if import_path_field.value else ""
        if not import_path:
            import_status.value = "Παρακαλώ εισάγετε τη διαδρομή του αρχείου"
            import_status.color = ft.Colors.RED_700
            page.update()
            return
        
        if not os.path.exists(import_path):
            import_status.value = f"Το αρχείο δεν βρέθηκε: {import_path}"
            import_status.color = ft.Colors.RED_700
            page.update()
            return
        
        success, message = db.import_database(import_path, replace=True)
        if success:
            import_status.value = message
            import_status.color = ft.Colors.GREEN_700
            refresh_subscriptions()
        else:
            import_status.value = message
            import_status.color = ft.Colors.RED_700
        page.update()
    
    import_export_content = ft.Container(
        padding=20,
        expand=True,
        content=ft.Column([
            ft.Text("Διαχείριση Δεδομένων", size=20, weight=ft.FontWeight.BOLD),
            ft.Container(height=10),
            
            # Export section
            ft.Container(
                padding=15,
                border=ft.Border.all(1, ft.Colors.GREY_300),
                border_radius=10,
                content=ft.Column([
                    ft.Text("Εξαγωγή Βάσης Δεδομένων", size=16, weight=ft.FontWeight.BOLD),
                    ft.Text("Αποθηκεύει τις καταχωρήσεις σε αρχείο JSON.", size=12, color=ft.Colors.GREY_600),
                    ft.Container(height=5),
                    ft.TextButton(
                        "Εξαγωγή",
                        icon=ft.CupertinoIcons.TRAY_ARROW_DOWN,
                        on_click=export_database_click
                    ),
                    export_status,
                    export_path_display
                ])
            ),
            
            ft.Container(height=15),
            
            # Import section
            ft.Container(
                padding=15,
                border=ft.Border.all(1, ft.Colors.GREY_300),
                border_radius=10,
                content=ft.Column([
                    ft.Text("Εισαγωγή Βάσης Δεδομένων", size=16, weight=ft.FontWeight.BOLD),
                    ft.Text("Εισάγει καταχωρήσεις από αρχείο JSON (αντικαθιστά τα υπάρχοντα).", 
                           size=12, color=ft.Colors.ORANGE_700),
                    ft.Container(height=5),
                    import_path_field,
                    ft.Text("Αντιγράψτε την πλήρη διαδρομή του αρχείου JSON.", size=10, italic=True, color=ft.Colors.GREY_500),
                    ft.Container(height=5),
                    ft.TextButton(
                        "Εισαγωγή",
                        icon=ft.CupertinoIcons.TRAY_ARROW_UP,
                        on_click=import_database_click
                    ),
                    import_status
                ])
            ),
            
            ft.Container(height=15),
            
            # Categories section
            ft.Container(
                padding=15,
                border=ft.Border.all(1, ft.Colors.GREEN_200),
                border_radius=10,
                bgcolor=ft.Colors.GREEN_50,
                content=ft.Column([
                    ft.Row([
                        ft.Text("Διαχείριση Κατηγοριών", size=16, weight=ft.FontWeight.BOLD),
                        categories_count_text
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Container(height=5),
                    ft.Row([
                        new_category_field,
                        ft.IconButton(
                            icon=ft.CupertinoIcons.PLUS_CIRCLE,
                            icon_color=ft.Colors.GREEN_700,
                            tooltip="Προσθήκη κατηγορίας",
                            on_click=add_category_click
                        )
                    ]),
                    ft.Container(height=5),
                    ft.Text("Υπάρχουσες κατηγορίες:", size=12, weight=ft.FontWeight.BOLD),
                    categories_list
                ])
            ),
            
            ft.Container(height=15),
            
            # Info section
            ft.Container(
                padding=15,
                bgcolor=ft.Colors.BLUE_50,
                border_radius=10,
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.CupertinoIcons.INFO_CIRCLE, color=ft.Colors.BLUE_700),
                        ft.Text("Πληροφορίες", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700, size=16)
                    ]),
                    ft.Divider(height=1, color=ft.Colors.BLUE_200),
                    ft.Text(f"Έκδοση: {APP_VERSION}", size=12, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Βάση δεδομένων: {db.get_db_path()}", size=11, color=ft.Colors.GREY_600),
                    ft.Container(height=10),
                    ft.Row([
                        ft.Icon(ft.CupertinoIcons.DOC_TEXT, size=18, color=ft.Colors.BLUE_600),
                        ft.Text("Τι κάνει η εφαρμογή", weight=ft.FontWeight.BOLD, size=13)
                    ]),
                    ft.Text(
                        "Το SubsPy είναι μια εφαρμογή διαχείρισης εσόδων και εξόδων. "
                        "Σας βοηθά να παρακολουθείτε τις οικονομικές σας κινήσεις, "
                        "τόσο μεμονωμένες όσο και επαναλαμβανόμενες (π.χ. συνδρομές, μισθοί).",
                        size=11, color=ft.Colors.GREY_700
                    ),
                    ft.Container(height=8),
                    ft.Row([
                        ft.Icon(ft.CupertinoIcons.STAR, size=18, color=ft.Colors.AMBER_600),
                        ft.Text("Δυνατότητες", weight=ft.FontWeight.BOLD, size=13)
                    ]),
                    ft.Column([
                        ft.Row([ft.Icon(ft.CupertinoIcons.PLUS_CIRCLE, size=14, color=ft.Colors.GREEN_600),
                                ft.Text("Καταχώρηση εσόδων και εξόδων με ημερομηνία, ποσό και κατηγορία", size=11)], spacing=5),
                        ft.Row([ft.Icon(ft.CupertinoIcons.REPEAT, size=14, color=ft.Colors.ORANGE_600),
                                ft.Text("Επαναλαμβανόμενες κινήσεις (π.χ. κάθε 30 ημέρες για μηνιαίες συνδρομές)", size=11)], spacing=5),
                        ft.Row([ft.Icon(ft.CupertinoIcons.CHART_BAR, size=14, color=ft.Colors.PURPLE_600),
                                ft.Text("Αναφορές προοδευτικών χρεώσεων για οποιοδήποτε χρονικό διάστημα", size=11)], spacing=5),
                        ft.Row([ft.Icon(ft.CupertinoIcons.DOC_TEXT, size=14, color=ft.Colors.RED_600),
                                ft.Text("Εξαγωγή αναφοράς σε PDF με έγχρωμη διάκριση εσόδων/εξόδων", size=11)], spacing=5),
                        ft.Row([ft.Icon(ft.CupertinoIcons.TAG, size=14, color=ft.Colors.TEAL_600),
                                ft.Text("Διαχείριση κατηγοριών (προσθήκη, διαγραφή)", size=11)], spacing=5),
                        ft.Row([ft.Icon(ft.CupertinoIcons.ARROW_UP_ARROW_DOWN, size=14, color=ft.Colors.BLUE_600),
                                ft.Text("Εξαγωγή/Εισαγωγή δεδομένων σε μορφή JSON για backup", size=11)], spacing=5),
                    ], spacing=4),
                    ft.Container(height=8),
                    ft.Row([
                        ft.Icon(ft.CupertinoIcons.QUESTION_CIRCLE, size=18, color=ft.Colors.TEAL_600),
                        ft.Text("Πώς λειτουργεί", weight=ft.FontWeight.BOLD, size=13)
                    ]),
                    ft.Column([
                        ft.Text("• Καταχωρήσεις: Προσθέστε έσοδα/έξοδα. Πατήστε πάνω σε μια εγγραφή για επεξεργασία ή διαγραφή.", size=11, color=ft.Colors.GREY_700),
                        ft.Text("• Επανάληψη: Επιλέξτε 'Ανά ημέρες' (π.χ. 365 = ετήσια) ή 'Κάθε μήνα' για μηνιαίες συνδρομές.", size=11, color=ft.Colors.GREY_700),
                        ft.Text("• Αναφορές: Επιλέξτε ημερομηνίες «Από» και «Έως» για προβολή κινήσεων και προοδευτικών υπολοίπων.", size=11, color=ft.Colors.GREY_700),
                        ft.Text("• Τα ποσά εμφανίζονται με χρώμα: πράσινο (+) για έσοδα/θετικά υπόλοιπα, κόκκινο (−) για έξοδα/αρνητικά.", size=11, color=ft.Colors.GREY_700),
                    ], spacing=3),
                    ft.Container(height=8),
                    ft.Text("© 2026 SpyAlekos", size=10, italic=True, color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER),
                ])
            )
        ], scroll=ft.ScrollMode.AUTO)
    )
    
    # ==================== NAVIGATION ====================
    
    tab_contents = [subscriptions_content, reports_content, import_export_content]
    content_container = ft.Container(expand=True, content=subscriptions_content)
    zoom_status = ft.Text("100%", size=12, color=ft.Colors.GREY_700)
    main_column = ft.Column(expand=True)
    zoom_body = ft.Column()
    zoom_slot = ft.Container(expand=True, clip_behavior=ft.ClipBehavior.HARD_EDGE)

    instructions_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Row([
            ft.Icon(ft.CupertinoIcons.QUESTION_CIRCLE, color=ft.Colors.BLUE_700),
            ft.Text("Οδηγίες / Instructions", weight=ft.FontWeight.BOLD),
        ], spacing=8),
        content=ft.Container(
            width=520,
            content=ft.Column([
                ft.Text("Ελληνικά", weight=ft.FontWeight.BOLD, size=14),
                ft.Text("• Καταχωρήσεις: Πατήστε «Προσθήκη» για έσοδα ή έξοδα και πατήστε σε γραμμή για επεξεργασία.", size=12),
                ft.Text("• Αναφορές: Επιλέξτε διάστημα και πατήστε «Δημιουργία» ή «Εκτύπωση PDF».", size=12),
                ft.Text("• Εργαλεία: Κάντε backup/restore σε JSON και διαχειριστείτε κατηγορίες.", size=12),
                ft.Text("• Zoom: Κρατήστε Ctrl και γυρίστε τη ρόδα του ποντικιού για μεγέθυνση ή σμίκρυνση όλης της οθόνης.", size=12),
                ft.Divider(height=12),
                ft.Text("English", weight=ft.FontWeight.BOLD, size=14),
                ft.Text("• Entries: Use Add for income or expenses, and click a row to edit it.", size=12),
                ft.Text("• Reports: Pick a date range, then Generate or export a PDF.", size=12),
                ft.Text("• Tools: Back up/restore JSON data and manage categories.", size=12),
                ft.Text("• Zoom: Hold Ctrl and use the mouse wheel to scale the whole screen up or down.", size=12),
            ], spacing=6, scroll=ft.ScrollMode.AUTO)
        ),
        actions=[ft.TextButton("OK", on_click=lambda e: close_subscription_dialog())],
    )

    def open_instructions(e):
        page.show_dialog(instructions_dialog)

    zoom_controls = ft.Row([
        ft.Button(
            "Προσθήκη",
            icon=ft.CupertinoIcons.PLUS,
            bgcolor=ft.Colors.GREEN_600,
            color=ft.Colors.WHITE,
            icon_color=ft.Colors.WHITE,
            on_click=add_subscription_click,
        ),
        zoom_status,
        ft.IconButton(
            icon=ft.CupertinoIcons.QUESTION_CIRCLE,
            icon_color=ft.Colors.BLUE_700,
            tooltip="Οδηγίες / Instructions",
            on_click=open_instructions,
        ),
    ], spacing=4)

    app_header = ft.Container(
        padding=ft.padding.symmetric(horizontal=12, vertical=8),
        bgcolor=ft.Colors.BLUE_50,
        content=ft.Row([
            ft.Row([
                ft.Icon(ft.CupertinoIcons.MONEY_EURO_CIRCLE, color=ft.Colors.BLUE_700, size=22),
                ft.Text("SubsPy", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                ft.Container(width=390),
                zoom_controls,
            ], spacing=8),
        ], alignment=ft.MainAxisAlignment.START, scroll=ft.ScrollMode.AUTO),
    )

    def get_max_zoom() -> float:
        available_width = getattr(page, "width", None) or getattr(page.window, "width", None) or 1024
        return max(1.0, min(ZOOM_MAX, available_width / CATEGORY_SAFE_WIDTH))

    def update_zoom_body_geometry():
        available_height = getattr(page, "height", None) or getattr(page.window, "height", None) or 720
        slot_height = max(MIN_ZOOM_BODY_HEIGHT, available_height - NAV_RESERVED_HEIGHT)
        zoom_body.height = slot_height / zoom_scale
        zoom_body.width = (getattr(page, "width", None) or getattr(page.window, "width", None) or 1024) / zoom_scale
        zoom_body.scale = ft.Scale(scale=zoom_scale, alignment=ft.Alignment(-1, -1))

    def apply_zoom(delta: float):
        nonlocal zoom_scale
        next_scale = max(ZOOM_MIN, min(get_max_zoom(), round(zoom_scale + delta, 2)))
        if next_scale == zoom_scale:
            zoom_status.value = f"{round(zoom_scale * 100)}%"
            update_zoom_body_geometry()
            page.update()
            return

        zoom_scale = next_scale
        zoom_status.value = f"{round(zoom_scale * 100)}%"
        update_zoom_body_geometry()
        page.update()

    def clamp_zoom_to_window(e=None):
        apply_zoom(0)

    def on_zoom_scroll(e):
        if not ctrl_pressed:
            return

        scroll_delta = getattr(e, "scroll_delta", None)
        dy = getattr(scroll_delta, "y", 0) if scroll_delta else 0
        apply_zoom(0.05 if dy < 0 else -0.05)

    def on_key_down(e):
        nonlocal ctrl_pressed
        if is_control_key(getattr(e, "key", "")):
            ctrl_pressed = True

    def on_key_up(e):
        nonlocal ctrl_pressed
        if is_control_key(getattr(e, "key", "")):
            ctrl_pressed = False

    def on_page_keyboard(e):
        nonlocal ctrl_pressed
        ctrl_pressed = bool(getattr(e, "ctrl", False)) or is_control_key(getattr(e, "key", ""))
    
    def on_nav_change(e):
        selected_index = e.control.selected_index
        content_container.content = tab_contents[selected_index]
        page.update()
    
    nav_bar = ft.NavigationBar(
        selected_index=0,
        on_change=on_nav_change,
        destinations=[
            ft.NavigationBarDestination(
                icon=ft.CupertinoIcons.MONEY_EURO_CIRCLE,
                selected_icon=ft.CupertinoIcons.MONEY_EURO_CIRCLE_FILL,
                label="Καταχωρήσεις",
            ),
            ft.NavigationBarDestination(
                icon=ft.CupertinoIcons.CHART_BAR,
                selected_icon=ft.CupertinoIcons.CHART_BAR_FILL,
                label="Αναφορές",
            ),
            ft.NavigationBarDestination(
                icon=ft.CupertinoIcons.ARROW_UP_ARROW_DOWN,
                label="Εργαλεία",
            ),
        ],
    )

    zoom_body.controls = [
        app_header,
        content_container,
    ]
    zoom_slot.content = zoom_body
    update_zoom_body_geometry()
    main_column.controls = [
        zoom_slot,
        nav_bar,
    ]
    page.on_keyboard_event = on_page_keyboard
    page.window.on_event = clamp_zoom_to_window
    
    # Main layout
    page.add(
        ft.SafeArea(
            expand=True,
            content=ft.Container(
                expand=True,
                content=ft.KeyboardListener(
                    autofocus=True,
                    on_key_down=on_key_down,
                    on_key_up=on_key_up,
                    content=ft.GestureDetector(
                        on_scroll=on_zoom_scroll,
                        content=main_column,
                    ),
                ),
            )
        )
    )
    
    # Initial load
    refresh_subscriptions()
    refresh_categories_list()


ft.run(main)
