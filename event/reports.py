import io
from datetime import datetime
from django.utils import timezone
from django.utils.html import escape
from django.db.models import Min, Q

from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


def get_event_sales_report_data(event, is_paid=True):
    """
    Extracts and aggregates sales report data for an event,
    matching the logic and grouping of the Django Admin Sales Report (ReportAdmin / ReportResource).
    """
    from shop.models import Order, Donation

    # Filter orders belonging to fundraisers of this event
    orders_qs = Order.objects.filter(fundraiser__event=event)
    if is_paid is not None:
        orders_qs = orders_qs.filter(is_paid=is_paid)

    # Group orders by checkout session (stripe_session_id) as done in ReportAdmin
    session_rep_ids = (
        orders_qs.filter(stripe_session_id__isnull=False)
        .exclude(stripe_session_id='')
        .order_by()
        .values('stripe_session_id')
        .annotate(rep_id=Min('id'))
        .values_list('rep_id', flat=True)
    )
    no_session_ids = (
        orders_qs.filter(Q(stripe_session_id__isnull=True) | Q(stripe_session_id=''))
        .order_by()
        .values_list('id', flat=True)
    )
    all_rep_ids = list(session_rep_ids) + list(no_session_ids)

    rep_orders = (
        orders_qs.filter(id__in=all_rep_ids)
        .select_related('user', 'product', 'fundraiser', 'fundraiser__user')
        .order_by('-created_at', '-id')
    )

    sales_records = []
    total_sales_amount = 0.0
    total_due_organizer = 0.0
    total_due_treats = 0.0
    total_items_count = 0

    counter = 0
    for rep_order in rep_orders:
        counter += 1

        # Fetch all items in this checkout session
        if rep_order.stripe_session_id:
            session_items = list(
                Order.objects.filter(stripe_session_id=rep_order.stripe_session_id)
                .select_related('product', 'fundraiser', 'fundraiser__user', 'user')
            )
        else:
            session_items = [rep_order]

        # Supporter name matching ReportResource dehydrate_supporter_name
        name = (rep_order.name or '').strip()
        if not name and rep_order.user:
            name = (rep_order.user.full_name or '').strip()
        if not name:
            name = (rep_order.email or '').strip()
        if not name and rep_order.user and rep_order.user.email:
            name = rep_order.user.email.strip()
        supporter_name = name or "-"

        # Supporter email & phone
        supporter_email = rep_order.email or (rep_order.user.email if rep_order.user else "")
        supporter_phone = rep_order.phone or (rep_order.user.phone if rep_order.user else "")

        # Purchase date matching ReportResource dehydrate_purchase_date
        purchase_date_str = ""
        purchase_date_iso = None
        if rep_order.created_at:
            purchase_date_iso = rep_order.created_at.isoformat()
            dt = timezone.localtime(rep_order.created_at) if timezone.is_aware(rep_order.created_at) else rep_order.created_at
            purchase_date_str = f"{dt.month}/{dt.day}/{dt.strftime('%y')} {dt.hour}:{dt.strftime('%M')}"

        # Items purchased and candy price
        item_lines = []
        items_detail = []
        session_total = 0.0
        session_item_qty = 0

        for item in session_items:
            if item.product:
                try:
                    price = float(item.product.price)
                except (ValueError, TypeError):
                    price = 0.0
                qty = item.quantity or 1
                line_total = price * qty
                session_total += line_total
                session_item_qty += qty
                item_lines.append(f"{item.product.name} x {qty}")
                items_detail.append({
                    "product_id": item.product.id,
                    "product_name": item.product.name,
                    "quantity": qty,
                    "unit_price": round(price, 2),
                    "subtotal": round(line_total, 2),
                })

        total_items_count += session_item_qty
        total_sales_amount += session_total

        # Format candy price matching ReportResource dehydrate_candy_price
        if float(session_total).is_integer():
            candy_price_str = f"{int(session_total)}"
        else:
            candy_price_str = f"{session_total:.2f}"

        # 50/50 split matching ReportResource dehydrate_due_organizer & dehydrate_due_treats
        due_org_val = round(session_total * 0.5, 2)
        due_treats_val = round(session_total * 0.5, 2)
        total_due_organizer += due_org_val
        total_due_treats += due_treats_val

        # Popup Name matching ReportResource dehydrate_popup_name
        popup_name = "-"
        fundraiser_id = None
        if rep_order.fundraiser:
            fundraiser_id = rep_order.fundraiser.id
            if rep_order.fundraiser.name and rep_order.fundraiser.name.strip():
                popup_name = rep_order.fundraiser.name.strip()
            elif rep_order.fundraiser.user:
                u_name = rep_order.fundraiser.user.full_name.strip() if rep_order.fundraiser.user.full_name else ""
                if u_name:
                    popup_name = f"{u_name}'s Store"
                elif rep_order.fundraiser.user.email:
                    popup_name = f"{rep_order.fundraiser.user.email}'s Store"
                else:
                    popup_name = f"Store {rep_order.fundraiser.id}"
            else:
                popup_name = f"Store {rep_order.fundraiser.id}"

        sales_records.append({
            "number": counter,
            "order_id": rep_order.id,
            "stripe_session_id": rep_order.stripe_session_id or "",
            "supporter_name": supporter_name,
            "supporter_email": supporter_email,
            "supporter_phone": supporter_phone,
            "purchase_date": purchase_date_str,
            "purchase_date_iso": purchase_date_iso,
            "items_purchased": "\n".join(item_lines),
            "items_detail": items_detail,
            "candy_price": candy_price_str,
            "candy_price_val": round(session_total, 2),
            "due_organizer": f"$ {due_org_val:.2f}",
            "due_organizer_val": due_org_val,
            "due_treats": f"$ {due_treats_val:.2f}",
            "due_treats_val": due_treats_val,
            "popup_name": popup_name,
            "fundraiser_id": fundraiser_id,
        })

    # Donations summary for completeness (25% org, 75% treats)
    donations_qs = Donation.objects.filter(fundraiser__event=event)
    if is_paid is not None:
        donations_qs = donations_qs.filter(is_paid=is_paid)

    total_donations_amount = 0.0
    for donation in donations_qs:
        try:
            total_donations_amount += float(donation.amount)
        except (ValueError, TypeError):
            pass

    donations_due_org = round(total_donations_amount * 0.25, 2)
    donations_due_treats = round(total_donations_amount * 0.75, 2)

    total_due_org_combined = round(total_due_organizer + donations_due_org, 2)
    total_due_treats_combined = round(total_due_treats + donations_due_treats, 2)
    grand_total_revenue = round(total_sales_amount + total_donations_amount, 2)

    creator_name = "-"
    creator_email = "-"
    if event.creator:
        creator_name = event.creator.full_name or event.creator.phone or "-"
        creator_email = event.creator.email or "-"

    return {
        "event": {
            "id": event.id,
            "name": event.name or f"Event {event.id}",
            "code": event.code or "-",
            "organization_type": event.type.name if event.type else "-",
            "creator_name": creator_name,
            "creator_email": creator_email,
            "start_date": event.start_date.isoformat() if event.start_date else None,
            "end_date": event.end_date.isoformat() if event.end_date else None,
            "duration": event.duration,
        },
        "summary": {
            "total_transactions": len(sales_records),
            "total_items_sold": total_items_count,
            "total_sales": round(total_sales_amount, 2),
            "due_organizer_sales": round(total_due_organizer, 2),
            "due_treats_sales": round(total_due_treats, 2),
            "total_donations": round(total_donations_amount, 2),
            "due_organizer_donations": donations_due_org,
            "due_treats_donations": donations_due_treats,
            "grand_total_revenue": grand_total_revenue,
            "grand_total_due_organizer": total_due_org_combined,
            "grand_total_due_treats": total_due_treats_combined,
        },
        "sales": sales_records,
    }


def generate_event_sales_report_pdf(event, report_data=None):
    """
    Generates a PDF document matching the Django Admin Sales Report PDF format.
    Uses landscape Letter page size, emerald header table style, and summary totals.
    """
    if report_data is None:
        report_data = get_event_sales_report_data(event, is_paid=True)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=20,
        leftMargin=20,
        topMargin=25,
        bottomMargin=25
    )
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#1b4332'),
        alignment=0,
        spaceAfter=4
    )
    meta_style = ParagraphStyle(
        'ReportMeta',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#444444'),
        spaceAfter=12
    )

    event_info = report_data.get('event', {})
    summary = report_data.get('summary', {})
    sales = report_data.get('sales', [])

    event_name = escape(event_info.get('name') or "Treats Island")
    event_code = escape(event_info.get('code') or "-")
    creator_name = escape(event_info.get('creator_name') or "-")
    date_str = datetime.now().strftime("%B %d, %Y - %I:%M %p")

    elements.append(Paragraph(f"Treats Island - Sales Report: {event_name}", title_style))
    meta_text = (
        f"<b>Event Code:</b> {event_code} &nbsp;|&nbsp; "
        f"<b>Organizer:</b> {creator_name} &nbsp;|&nbsp; "
        f"<b>Generated on:</b> {date_str}"
    )
    elements.append(Paragraph(meta_text, meta_style))

    # Column headers exactly matching Django admin ReportResource
    headers = [
        '#',
        'Supporter name',
        'Purchase date',
        'Items purchased',
        'Candy price',
        'Due Organizer',
        'Due Treats',
        'Popup Name',
    ]

    header_style = ParagraphStyle(
        'HeaderStyle',
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=0
    )
    header_center_style = ParagraphStyle(
        'HeaderCenterStyle',
        parent=header_style,
        alignment=1
    )
    cell_style = ParagraphStyle(
        'CellStyle',
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#222222'),
        alignment=0
    )
    cell_center_style = ParagraphStyle(
        'CellCenterStyle',
        parent=cell_style,
        alignment=1
    )
    total_label_style = ParagraphStyle(
        'TotalLabelStyle',
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#1b4332'),
        alignment=2
    )
    total_val_style = ParagraphStyle(
        'TotalValStyle',
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#1b4332'),
        alignment=0
    )

    table_data = []

    # Header Row
    header_cells = []
    for h in headers:
        style = header_center_style if h == '#' else header_style
        header_cells.append(Paragraph(h, style))
    table_data.append(header_cells)

    # Data Rows
    for row in sales:
        items_html = escape(row.get('items_purchased', '')).replace('\n', '<br/>')
        supporter_text = escape(row.get('supporter_name', '-'))
        purchase_date_text = escape(row.get('purchase_date', ''))
        candy_price_text = escape(str(row.get('candy_price', '0')))
        due_org_text = escape(str(row.get('due_organizer', '$ 0.00')))
        due_treats_text = escape(str(row.get('due_treats', '$ 0.00')))
        popup_name_text = escape(row.get('popup_name', '-'))

        table_data.append([
            Paragraph(str(row.get('number', '')), cell_center_style),
            Paragraph(supporter_text, cell_style),
            Paragraph(purchase_date_text, cell_style),
            Paragraph(items_html, cell_style),
            Paragraph(candy_price_text, cell_style),
            Paragraph(due_org_text, cell_style),
            Paragraph(due_treats_text, cell_style),
            Paragraph(popup_name_text, cell_style),
        ])

    # If no sales rows exist
    if not sales:
        empty_style = ParagraphStyle(
            'EmptyStyle',
            parent=cell_style,
            alignment=1,
            textColor=colors.HexColor('#666666')
        )
        empty_row = [
            Paragraph("No sales records found for this event.", empty_style),
            Paragraph("", cell_style),
            Paragraph("", cell_style),
            Paragraph("", cell_style),
            Paragraph("", cell_style),
            Paragraph("", cell_style),
            Paragraph("", cell_style),
            Paragraph("", cell_style),
        ]
        table_data.append(empty_row)

    # Total Row matching ReportAdmin PDF export
    has_total_row = bool(sales)
    if has_total_row:
        due_org_total = summary.get('due_organizer_sales', 0.0)
        due_treats_total = summary.get('due_treats_sales', 0.0)
        total_row = [
            Paragraph("", cell_style),
            Paragraph("", cell_style),
            Paragraph("", cell_style),
            Paragraph("Total:", total_label_style),
            Paragraph("", cell_style),
            Paragraph(f"$ {due_org_total:.2f}", total_val_style),
            Paragraph(f"$ {due_treats_total:.2f}", total_val_style),
            Paragraph("", cell_style),
        ]
        table_data.append(total_row)

    # Exact column widths matching shop/admin.py PDF export (Sum = 752 points)
    col_widths = [28, 90, 72, 245, 55, 68, 64, 130]

    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1b4332')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1b4332')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1 if not has_total_row else -2), [colors.white, colors.HexColor('#f9f9f9')]),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
    ]

    if not sales:
        t_style.append(('SPAN', (0, 1), (-1, 1)))
        t_style.append(('TOPPADDING', (0, 1), (-1, 1), 14))
        t_style.append(('BOTTOMPADDING', (0, 1), (-1, 1), 14))

    if has_total_row:
        t_style.extend([
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#eef6f1')),
            ('LINEABOVE', (0, -1), (-1, -1), 1.2, colors.HexColor('#1b4332')),
            ('LINEBELOW', (0, -1), (-1, -1), 1.2, colors.HexColor('#1b4332')),
            ('TOPPADDING', (0, -1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 6),
        ])

    t.setStyle(TableStyle(t_style))
    elements.append(t)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
