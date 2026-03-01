"""
SubsPy - PDF Export
Generate PDF reports for progressive charges.
"""

from datetime import datetime
from typing import List
import os

from platform_utils import get_documents_dir

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def register_fonts():
    """Register fonts for Greek text support."""
    if not REPORTLAB_AVAILABLE:
        return
    
    # Try to register a font that supports Greek
    font_paths = [
        # Windows
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        # Linux
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
        # macOS
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
    ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('CustomFont', font_path))
                return 'CustomFont'
            except:
                pass
    
    return 'Helvetica'  # Fallback


def generate_report_pdf(
    charges: List[dict],
    from_date: str,
    to_date: str,
    filepath: str,
    raw_from_date: datetime = None
) -> tuple[bool, str]:
    """
    Generate PDF report for progressive charges.
    Returns (success, message).
    """
    import database as db  # local import avoiding circular dependancy issues if any
    
    if not REPORTLAB_AVAILABLE:
        return False, "Η βιβλιοθήκη reportlab δεν είναι εγκατεστημένη."
    
    try:
        font_name = register_fonts()
        
        # Create document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom styles with Greek support
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName=font_name,
            fontSize=16,
            spaceAfter=12,
            alignment=1  # Center
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=11,
            spaceAfter=20,
            alignment=1  # Center
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=10
        )
        
        # Title
        elements.append(Paragraph("Αναφορά Προοδευτικών Χρεώσεων", title_style))
        
        # Date range
        from_formatted = datetime.strptime(from_date, '%Y-%m-%d').strftime('%d/%m/%Y')
        to_formatted = datetime.strptime(to_date, '%Y-%m-%d').strftime('%d/%m/%Y')
        elements.append(Paragraph(
            f"Περίοδος: {from_formatted} - {to_formatted}",
            subtitle_style
        ))
        
        # Export date
        elements.append(Paragraph(
            f"Ημερομηνία εκτύπωσης: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            normal_style
        ))
        elements.append(Spacer(1, 10*mm))
        
        if not charges:
            elements.append(Paragraph("Δεν υπάρχουν χρεώσεις για την επιλεγμένη περίοδο.", normal_style))
        else:
            # Table data
            table_data = [
                ['Ημερομηνία', 'Περιγραφή', 'Κατηγορία', 'Ποσό (€)', 'Υπόλοιπο']
            ]
            
            # Styles for colored amounts
            amount_style_expense = ParagraphStyle(
                'AmountExpense',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=9,
                textColor=colors.HexColor('#C62828'),  # Red
                alignment=2  # Right
            )
            amount_style_income = ParagraphStyle(
                'AmountIncome',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=9,
                textColor=colors.HexColor('#2E7D32'),  # Green
                alignment=2  # Right
            )
            cell_style = ParagraphStyle(
                'CellStyle',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=9,
            )
            
            
            # Opening balance for running balance
            running_balance = 0.0
            total = 0.0
            total_income = 0.0
            total_expenses = 0.0
            for charge in charges:
                date_formatted = datetime.strptime(charge['date'], '%Y-%m-%d').strftime('%d/%m/%Y')
                amount = charge['amount']
                entry_type = charge.get('entry_type', 'expense')
                is_income = entry_type == 'income'
                
                if is_income:
                    total -= amount
                    total_income += amount
                    running_balance += amount
                    amount_text = Paragraph(f"+€{amount:.2f}", amount_style_income)
                else:
                    total += amount
                    total_expenses += amount
                    running_balance -= amount
                    amount_text = Paragraph(f"−€{amount:.2f}", amount_style_expense)
                
                if running_balance >= 0:
                    balance_text = Paragraph(f"+€{running_balance:.2f}", amount_style_income)
                else:
                    balance_text = Paragraph(f"−€{abs(running_balance):.2f}", amount_style_expense)
                
                table_data.append([
                    date_formatted,
                    Paragraph(charge['description'][:40], cell_style),
                    Paragraph(charge['category'][:20], cell_style),
                    amount_text,
                    balance_text
                ])
            
            # Total row
            if running_balance >= 0:
                total_text = Paragraph(f"+€{running_balance:.2f}", amount_style_income)
            else:
                total_text = Paragraph(f"−€{abs(running_balance):.2f}", amount_style_expense)
            table_data.append(['', '', '', Paragraph('Τελ. Υπόλοιπο:', cell_style), total_text])
            
            # Create table
            col_widths = [23*mm, 60*mm, 30*mm, 23*mm, 23*mm]
            table = Table(table_data, colWidths=col_widths, repeatRows=1)
            
            # Table style
            table.setStyle(TableStyle([
                # Header
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2196F3')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), font_name),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                
                # Body
                ('FONTNAME', (0, 1), (-1, -1), font_name),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Date column
                ('ALIGN', (3, 1), (4, -1), 'RIGHT'),   # Amount & Balance columns
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                
                # Alternating row colors
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#fff8ec')]),
                
                # Total row
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#a5dfdf')),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                ('FONTSIZE', (0, -1), (-1, -1), 10),
                
                # Grid
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BBDEFB')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1976D2')),
            ]))
            
            elements.append(table)
            
            # Summary Table
            elements.append(Spacer(1, 10*mm))
            
            summary_data = [
                ['Σύνοψη', 'Πλήθος', 'Ποσό']
            ]
            summary_data.append(['Κινήσεις', str(len(charges)), '-'])
            summary_data.append(['Έσοδα', '-', Paragraph(f"€{total_income:.2f}", amount_style_income)])
            summary_data.append(['Έξοδα', '-', Paragraph(f"€{total_expenses:.2f}", amount_style_expense)])
            
            # Use normal_style font for the table text as fallback, though font_name is defined.
            summary_table = Table(summary_data, colWidths=[40*mm, 20*mm, 30*mm])
            summary_table.setStyle(TableStyle([
                # Header
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), font_name),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('TOPPADDING', (0, 0), (-1, 0), 6),
                
                # Body
                ('FONTNAME', (0, 1), (-1, -1), font_name),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
                
                # Grid and Border
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#C8E6C9')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#388E3C')),
            ]))
            
            elements.append(summary_table)
        
        # Build PDF
        doc.build(elements)
        return True, f"Το PDF δημιουργήθηκε επιτυχώς: {filepath}"
        
    except Exception as e:
        return False, f"Σφάλμα δημιουργίας PDF: {e}"


def get_default_pdf_path() -> str:
    """Get default path for PDF export."""
    docs_dir = get_documents_dir()
    filename = f"subspy_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return os.path.join(docs_dir, filename)
