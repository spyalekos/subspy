"""
SubsPy - Εφαρμογή Διαχείρισης Εσόδων & Εξόδων
Cross-platform income/expense management with Flet.
Compatible with Flet 0.80+
"""

import flet as ft
import asyncio
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
    page.window.icon = "icon.ico"
    page.window.min_width = 800
    page.window.min_height = 550
    if not page.window.width or page.window.width < 950:
        page.window.width = 1000
    if not page.window.height or page.window.height < 650:
        page.window.height = 700

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
    target_zoom_scale = 1.0
    zoom_task: Optional[asyncio.Future] = None
    ctrl_pressed = False
    ZOOM_MIN = 0.75
    ZOOM_MAX = 2.2
    
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

    def zoomed(value: float, minimum: int = 1) -> int:
        """Scale layout values instead of using visual transforms."""
        return max(minimum, round(value * zoom_scale))

    def safe_show_dialog(dlg):
        """Show a dialog safely avoiding 'Dialog is already opened' error."""
        if dlg is None or getattr(dlg, "open", False):
            return
        try:
            if hasattr(page, '_dialogs') and dlg in page._dialogs.controls:
                page._dialogs.controls.remove(dlg)
        except Exception:
            pass
        dlg.open = True
        try:
            page.show_dialog(dlg)
        except Exception:
            dlg.open = True
            try:
                dlg.update()
            except Exception:
                page.update()

    def safe_close_dialog(dlg):
        """Close a dialog safely by setting dlg.open=False and letting Flutter dismiss it."""
        if dlg is None or not getattr(dlg, "open", False):
            return
        dlg.open = False
        try:
            dlg.update()
        except Exception:
            try:
                page.pop_dialog()
            except Exception:
                pass

    ZOOM_FIT_THRESHOLD = 1.25  # Up to 125% zoom, columns fit inside the window width

    def get_column_widths_subscriptions():
        """
        Compute column widths:
        - Up to ZOOM_FIT_THRESHOLD: columns dynamically fit 100% within the window width.
        - Above ZOOM_FIT_THRESHOLD: table expands beyond window width, showing horizontal scrollbar.
        """
        avail = max(700, int(page.width or page.window.width or 950) - 36)
        if zoom_scale <= ZOOM_FIT_THRESHOLD:
            eff_width = avail
        else:
            eff_width = round(avail * (zoom_scale / ZOOM_FIT_THRESHOLD))

        spacing = zoomed(16, minimum=8)
        inner_width = max(580, eff_width - (5 * spacing) - 24)
        
        w_desc = round(inner_width * 0.28)
        w_date = round(inner_width * 0.14)
        w_amount = round(inner_width * 0.14)
        w_type = round(inner_width * 0.14)
        w_repeat = round(inner_width * 0.14)
        w_cat = inner_width - (w_desc + w_date + w_amount + w_type + w_repeat)
        return [w_desc, w_date, w_amount, w_type, w_repeat, w_cat], spacing, eff_width

    def get_column_widths_report():
        """
        Compute report column widths:
        - Up to ZOOM_FIT_THRESHOLD: columns dynamically fit 100% within the window width.
        - Above ZOOM_FIT_THRESHOLD: table expands beyond window width, showing horizontal scrollbar.
        """
        avail = max(700, int(page.width or page.window.width or 950) - 36)
        if zoom_scale <= ZOOM_FIT_THRESHOLD:
            eff_width = avail
        else:
            eff_width = round(avail * (zoom_scale / ZOOM_FIT_THRESHOLD))

        spacing = zoomed(14, minimum=6)
        inner_width = max(580, eff_width - (6 * spacing) - 24)
        
        w_date = round(inner_width * 0.12)
        w_desc = round(inner_width * 0.24)
        w_type = round(inner_width * 0.12)
        w_repeat = round(inner_width * 0.12)
        w_cat = round(inner_width * 0.14)
        w_amount = round(inner_width * 0.13)
        w_bal = inner_width - (w_date + w_desc + w_type + w_repeat + w_cat + w_amount)
        return [w_date, w_desc, w_type, w_repeat, w_cat, w_amount, w_bal], spacing, eff_width

    zoom_status = ft.Text("100%", size=13, color=ft.Colors.GREY_700, weight=ft.FontWeight.BOLD)

    def apply_table_zoom():
        subscriptions_table.heading_row_height = zoomed(56)
        subscriptions_table.data_row_min_height = zoomed(44)
        subscriptions_table.data_row_max_height = zoomed(52)
        report_table.heading_row_height = zoomed(56)
        report_table.data_row_min_height = zoomed(44)
        report_table.data_row_max_height = zoomed(52)
        zoom_status.size = 13

    def render_current_zoom():
        apply_table_zoom()
        refresh_subscriptions(update_page=False, force_reload=False)
        if report_table.rows:
            refresh_report(update_page=False)

    async def _async_apply_zoom(target: float):
        await asyncio.sleep(0.06)
        nonlocal zoom_scale
        if target == zoom_scale:
            return
        zoom_scale = target
        zoom_status.value = f"{round(zoom_scale * 100)}%"
        render_current_zoom()
        page.update()

    def apply_zoom(delta: float, immediate: bool = False):
        nonlocal target_zoom_scale, zoom_task, zoom_scale
        next_scale = max(ZOOM_MIN, min(ZOOM_MAX, round(target_zoom_scale + delta, 2)))
        target_zoom_scale = next_scale
        zoom_status.value = f"{round(target_zoom_scale * 100)}%"

        if zoom_task and not zoom_task.done():
            zoom_task.cancel()

        if immediate:
            zoom_scale = target_zoom_scale
            render_current_zoom()
            page.update()
        else:
            try:
                zoom_status.update()
            except Exception:
                pass
            zoom_task = page.run_task(_async_apply_zoom, target_zoom_scale)

    last_scroll_time = 0.0

    def on_zoom_scroll(e):
        if not ctrl_pressed:
            return

        nonlocal last_scroll_time
        import time
        now = time.time()
        # Drop excessive wheel events to keep the WebSocket buffer completely responsive
        if now - last_scroll_time < 0.08:
            return
        last_scroll_time = now

        scroll_delta = getattr(e, "scroll_delta", None)
        dy = getattr(scroll_delta, "y", 0) if scroll_delta else 0
        if dy == 0:
            return
        apply_zoom(0.10 if dy < 0 else -0.10, immediate=False)

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
        safe_close_dialog(subscription_dialog)
    
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
        
        try:
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
        except Exception as ex:
            show_snackbar(f"Σφάλμα κατά την αποθήκευση: {ex}", error=True)
    
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
        
        safe_show_dialog(subscription_dialog)
    
    # ==================== ENTRIES TAB CONTENT ====================
    
    col_widths_sub, sub_spacing, sub_total_w = get_column_widths_subscriptions()

    sub_col_desc_text = ft.Text("Περιγραφή", weight=ft.FontWeight.BOLD)
    sub_col_date_text = ft.Text("Ημερομηνία", weight=ft.FontWeight.BOLD)
    sub_col_amount_text = ft.Text("Ποσό (€)", weight=ft.FontWeight.BOLD)
    sub_col_type_text = ft.Text("Τύπος", weight=ft.FontWeight.BOLD)
    sub_col_repeat_text = ft.Text("Επανάληψη", weight=ft.FontWeight.BOLD)
    sub_col_cat_text = ft.Text("Κατηγορία", weight=ft.FontWeight.BOLD)

    sub_header_containers = [
        ft.Container(content=sub_col_desc_text, width=col_widths_sub[0]),
        ft.Container(content=sub_col_date_text, width=col_widths_sub[1]),
        ft.Container(content=sub_col_amount_text, width=col_widths_sub[2], alignment=ft.Alignment(1, 0)),
        ft.Container(content=sub_col_type_text, width=col_widths_sub[3]),
        ft.Container(content=sub_col_repeat_text, width=col_widths_sub[4]),
        ft.Container(content=sub_col_cat_text, width=col_widths_sub[5]),
    ]

    subscriptions_table = ft.DataTable(
        columns=[
            ft.DataColumn(sub_header_containers[0]),
            ft.DataColumn(sub_header_containers[1]),
            ft.DataColumn(sub_header_containers[2], numeric=True),
            ft.DataColumn(sub_header_containers[3]),
            ft.DataColumn(sub_header_containers[4]),
            ft.DataColumn(sub_header_containers[5]),
        ],
        rows=[],
        border=ft.Border.all(1, ft.Colors.GREY_300),
        border_radius=8,
        heading_row_color=ft.Colors.BLUE_50,
        heading_row_height=56,
        column_spacing=sub_spacing,
        data_row_min_height=44,
        data_row_max_height=50,
        show_checkbox_column=False,
    )
    
    def on_row_click(subscription_id: int):
        if getattr(subscription_dialog, "open", False):
            return
        sub = db.get_subscription_by_id(subscription_id)
        if sub:
            open_subscription_dialog(sub)
    
    cached_subscriptions: list = []

    def refresh_subscriptions(update_page: bool = True, force_reload: bool = True):
        nonlocal cached_subscriptions
        if force_reload or not cached_subscriptions:
            cached_subscriptions = db.get_all_subscriptions()
        subscriptions = cached_subscriptions
        subscriptions_table.rows.clear()
        row_text_size = zoomed(14)
        row_icon_size = zoomed(16)
        col_w, sp, tot_w = get_column_widths_subscriptions()
        
        subscriptions_table.column_spacing = sp
        subscriptions_table.width = tot_w
        for i, cont in enumerate(sub_header_containers):
            cont.width = col_w[i]
        
        header_text_size = zoomed(14)
        sub_col_desc_text.size = header_text_size
        sub_col_date_text.size = header_text_size
        sub_col_amount_text.size = header_text_size
        sub_col_type_text.size = header_text_size
        sub_col_repeat_text.size = header_text_size
        sub_col_cat_text.size = header_text_size
        
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
                    ft.DataCell(ft.Container(
                        content=ft.Text(sub['description'], size=row_text_size, overflow=ft.TextOverflow.ELLIPSIS),
                        width=col_w[0]
                    )),
                    ft.DataCell(ft.Container(
                        content=ft.Text(date_formatted, size=row_text_size),
                        width=col_w[1]
                    )),
                    ft.DataCell(ft.Container(
                        content=ft.Text(f"{amount_prefix}€{sub['amount']:.2f}", size=row_text_size, color=amount_color, weight=ft.FontWeight.BOLD),
                        width=col_w[2],
                        alignment=ft.Alignment(1, 0)
                    )),
                    ft.DataCell(ft.Container(
                        content=ft.Row([
                            ft.Icon(type_icon, size=row_icon_size, color=type_color),
                            ft.Text(type_text, size=row_text_size, color=type_color),
                        ], spacing=4),
                        width=col_w[3]
                    )),
                    ft.DataCell(ft.Container(
                        content=ft.Text(repeat_text, size=row_text_size),
                        width=col_w[4]
                    )),
                    ft.DataCell(ft.Container(
                        content=ft.Text(sub['category'], size=row_text_size, overflow=ft.TextOverflow.ELLIPSIS),
                        width=col_w[5]
                    )),
                ],
                on_select_change=lambda e, sid=sub['id']: on_row_click(sid)
            )
            subscriptions_table.rows.append(row)
        
        if update_page:
            page.update()
    
    def add_subscription_click(e):
        open_subscription_dialog()
    
    subscriptions_content = ft.Container(
        padding=10,
        expand=True,
        content=ft.Column([
            ft.Row([
                ft.Text("Καταχωρήσεις", size=20, weight=ft.FontWeight.BOLD),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(height=6),
            ft.Container(
                content=ft.GestureDetector(
                    on_scroll=on_zoom_scroll,
                    content=ft.Row([
                        ft.Column([subscriptions_table], scroll=ft.ScrollMode.AUTO)
                    ], scroll=ft.ScrollMode.ALWAYS, expand=True),
                ),
                expand=True
            )
        ], expand=True)
    )
    
    # ==================== REPORTS TAB CONTENT ====================
    
    report_from_text = ft.Text(report_from_date.strftime("%d/%m/%Y"), size=14)
    report_to_text = ft.Text(report_to_date.strftime("%d/%m/%Y"), size=14)
    
    col_widths_rep, rep_spacing, rep_total_w = get_column_widths_report()

    rep_col_date_text = ft.Text("Ημερομηνία", weight=ft.FontWeight.BOLD)
    rep_col_desc_text = ft.Text("Περιγραφή", weight=ft.FontWeight.BOLD)
    rep_col_type_text = ft.Text("Τύπος", weight=ft.FontWeight.BOLD)
    rep_col_repeat_text = ft.Text("Επανάληψη", weight=ft.FontWeight.BOLD)
    rep_col_cat_text = ft.Text("Κατηγορία", weight=ft.FontWeight.BOLD)
    rep_col_amount_text = ft.Text("Ποσό (€)", weight=ft.FontWeight.BOLD)
    rep_col_bal_text = ft.Text("Υπόλοιπο", weight=ft.FontWeight.BOLD)

    rep_header_containers = [
        ft.Container(content=rep_col_date_text, width=col_widths_rep[0]),
        ft.Container(content=rep_col_desc_text, width=col_widths_rep[1]),
        ft.Container(content=rep_col_type_text, width=col_widths_rep[2]),
        ft.Container(content=rep_col_repeat_text, width=col_widths_rep[3]),
        ft.Container(content=rep_col_cat_text, width=col_widths_rep[4]),
        ft.Container(content=rep_col_amount_text, width=col_widths_rep[5], alignment=ft.Alignment(1, 0)),
        ft.Container(content=rep_col_bal_text, width=col_widths_rep[6], alignment=ft.Alignment(1, 0)),
    ]

    report_table = ft.DataTable(
        columns=[
            ft.DataColumn(rep_header_containers[0]),
            ft.DataColumn(rep_header_containers[1]),
            ft.DataColumn(rep_header_containers[2]),
            ft.DataColumn(rep_header_containers[3]),
            ft.DataColumn(rep_header_containers[4]),
            ft.DataColumn(rep_header_containers[5], numeric=True),
            ft.DataColumn(rep_header_containers[6], numeric=True),
        ],
        rows=[],
        border=ft.Border.all(1, ft.Colors.GREY_300),
        border_radius=8,
        heading_row_color=ft.Colors.ORANGE_50,
        heading_row_height=56,
        data_row_min_height=44,
        data_row_max_height=50,
        column_spacing=rep_spacing,
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
    
    def refresh_report(update_page: bool = True):
        from_str = report_from_date.strftime("%Y-%m-%d")
        to_str = report_to_date.strftime("%Y-%m-%d")
        
        # Calculate charges for the selected period
        charges = db.get_progressive_charges(from_str, to_str)
        
        report_table.rows.clear()
        row_text_size = zoomed(14)
        row_icon_size = zoomed(16)
        col_w, sp, tot_w = get_column_widths_report()
        report_table.column_spacing = sp
        report_table.width = tot_w
        for i, cont in enumerate(rep_header_containers):
            cont.width = col_w[i]

        header_text_size = zoomed(14)
        rep_col_date_text.size = header_text_size
        rep_col_desc_text.size = header_text_size
        rep_col_type_text.size = header_text_size
        rep_col_repeat_text.size = header_text_size
        rep_col_cat_text.size = header_text_size
        rep_col_amount_text.size = header_text_size
        rep_col_bal_text.size = header_text_size
        
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
                ft.DataCell(ft.Container(content=ft.Text(date_formatted, size=row_text_size), width=col_w[0])),
                ft.DataCell(ft.Container(content=ft.Text(charge['description'], size=row_text_size, overflow=ft.TextOverflow.ELLIPSIS), width=col_w[1])),
                ft.DataCell(ft.Container(content=ft.Row([
                    ft.Icon(type_icon, size=row_icon_size, color=type_color),
                    ft.Text(type_text, size=row_text_size, color=type_color),
                ], spacing=4), width=col_w[2])),
                ft.DataCell(ft.Container(content=ft.Text(repeat_text, size=row_text_size), width=col_w[3])),
                ft.DataCell(ft.Container(content=ft.Text(charge['category'], size=row_text_size, overflow=ft.TextOverflow.ELLIPSIS), width=col_w[4])),
                ft.DataCell(ft.Container(content=ft.Text(f"{amount_prefix}€{charge['amount']:.2f}", size=row_text_size, color=amount_color, weight=ft.FontWeight.BOLD), width=col_w[5], alignment=ft.Alignment(1, 0))),
                ft.DataCell(ft.Container(content=ft.Text(f"{balance_prefix}€{abs(running_balance):.2f}", size=row_text_size, color=balance_color, weight=ft.FontWeight.BOLD), width=col_w[6], alignment=ft.Alignment(1, 0))),
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
        if update_page:
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
                content=ft.GestureDetector(
                    on_scroll=on_zoom_scroll,
                    content=ft.Row([
                        ft.Column([report_table], scroll=ft.ScrollMode.AUTO)
                    ], scroll=ft.ScrollMode.ALWAYS, expand=True),
                ),
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
                        padding=ft.Padding.symmetric(horizontal=5, vertical=2),
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
    main_column = ft.Column(expand=True)

    instructions_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Row([
            ft.Icon(ft.CupertinoIcons.QUESTION_CIRCLE, color=ft.Colors.BLUE_700, size=28),
            ft.Text("Οδηγίες Χρήσης / Instructions", weight=ft.FontWeight.BOLD, size=22),
        ], spacing=12),
        content=ft.Container(
            width=800,
            padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            content=ft.Column([
                ft.Text("Ελληνικά", weight=ft.FontWeight.BOLD, size=18, color=ft.Colors.BLUE_900),
                ft.Text("• Καταχωρήσεις: Πατήστε «Προσθήκη» για έσοδα ή έξοδα και πατήστε σε οποιαδήποτε γραμμή του πίνακα για επεξεργασία ή διαγραφή.", size=16),
                ft.Text("• Αναφορές: Επιλέξτε διάστημα ημερομηνιών και πατήστε «Δημιουργία» για προβολή κινήσεων και υπολοίπων ή «Εκτύπωση PDF».", size=16),
                ft.Text("• Εργαλεία: Δημιουργήστε αντίγραφα ασφαλείας σε αρχείο JSON, κάντε ανάκτηση (restore) και διαχειριστείτε κατηγορίες.", size=16),
                ft.Text("• Zoom: Κρατήστε πατημένο το πλήκτρο Ctrl και γυρίστε τη ρόδα του ποντικιού για μεγέθυνση ή σμίκρυνση, ή χρησιμοποιήστε τα κουμπιά [+] και [-] στην κεφαλίδα (κλικ στο ποσοστό για επαναφορά στο 100%).", size=16),
                ft.Divider(height=22),
                ft.Text("English", weight=ft.FontWeight.BOLD, size=18, color=ft.Colors.BLUE_900),
                ft.Text("• Entries: Click 'Add' for income or expenses, and click any table row to edit or delete it.", size=16),
                ft.Text("• Reports: Select date range and click 'Generate' to view progressive balances, or 'Export PDF'.", size=16),
                ft.Text("• Tools: Export/import JSON backups and manage transaction categories.", size=16),
                ft.Text("• Zoom: Hold Ctrl and rotate the mouse wheel to scale up or down, or use the [+] and [-] buttons in the header (click percentage to reset to 100%).", size=16),
            ], spacing=12, scroll=ft.ScrollMode.AUTO)
        ),
        actions=[
            ft.TextButton(
                "OK",
                icon=ft.CupertinoIcons.CHECKMARK,
                style=ft.ButtonStyle(color=ft.Colors.BLUE_700),
                on_click=lambda e: safe_close_dialog(instructions_dialog)
            )
        ],
    )

    def open_instructions(e):
        safe_show_dialog(instructions_dialog)

    def zoom_in_click(e):
        apply_zoom(0.10, immediate=True)

    def zoom_out_click(e):
        apply_zoom(-0.10, immediate=True)

    def zoom_reset_click(e):
        nonlocal target_zoom_scale, zoom_task
        if zoom_task and not zoom_task.done():
            zoom_task.cancel()
        target_zoom_scale = 1.0
        apply_zoom(0, immediate=True)

    zoom_controls = ft.Row([
        ft.Button(
            "Προσθήκη",
            icon=ft.CupertinoIcons.PLUS,
            bgcolor=ft.Colors.GREEN_600,
            color=ft.Colors.WHITE,
            icon_color=ft.Colors.WHITE,
            on_click=add_subscription_click,
        ),
        ft.Row([
            ft.IconButton(
                icon=ft.CupertinoIcons.MINUS_CIRCLE,
                icon_color=ft.Colors.BLUE_700,
                tooltip="Σμίκρυνση (Ctrl + Ρόδα προς τα κάτω)",
                on_click=zoom_out_click,
                icon_size=18,
            ),
            ft.Container(
                content=zoom_status,
                tooltip="Επαναφορά στο 100% (Κλικ)",
                on_click=zoom_reset_click,
                padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                border=ft.Border.all(1, ft.Colors.BLUE_200),
                border_radius=4,
                bgcolor=ft.Colors.WHITE,
            ),
            ft.IconButton(
                icon=ft.CupertinoIcons.PLUS_CIRCLE,
                icon_color=ft.Colors.BLUE_700,
                tooltip="Μεγέθυνση (Ctrl + Ρόδα προς τα επάνω)",
                on_click=zoom_in_click,
                icon_size=18,
            ),
        ], spacing=2, alignment=ft.MainAxisAlignment.CENTER),
        ft.IconButton(
            icon=ft.CupertinoIcons.QUESTION_CIRCLE,
            icon_color=ft.Colors.BLUE_700,
            tooltip="Οδηγίες / Instructions",
            on_click=open_instructions,
            icon_size=20,
        ),
    ], spacing=8, alignment=ft.MainAxisAlignment.END)

    app_header = ft.Container(
        padding=ft.Padding.symmetric(horizontal=16, vertical=8),
        bgcolor=ft.Colors.BLUE_50,
        border=ft.Border(bottom=ft.BorderSide(1, ft.Colors.BLUE_100)),
        content=ft.Row([
            ft.Row([
                ft.Image(src="icon_new.png", width=28, height=28, fit=ft.BoxFit.CONTAIN, border_radius=4),
                ft.Text("SubsPy", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
            ], spacing=8),
            zoom_controls,
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
    )


    
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

    main_column.controls = [
        app_header,
        content_container,
        nav_bar,
    ]
    resize_task: Optional[asyncio.Future] = None

    async def _async_resize():
        await asyncio.sleep(0.05)
        try:
            render_current_zoom()
            page.update()
        except Exception:
            pass

    def on_page_resize(e):
        nonlocal resize_task
        if resize_task and not resize_task.done():
            resize_task.cancel()
        resize_task = page.run_task(_async_resize)

    page.on_resize = on_page_resize
    page.on_keyboard_event = on_page_keyboard
    apply_table_zoom()
    
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
    page.update()

    try:
        import pyi_splash
        pyi_splash.close()
    except ImportError:
        pass


ft.run(main)
