from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import io
import os

def generate_quotation_pdf(quotation, items, party):
    """
    Generates a PDF for the quotation and returns it as a BytesIO object.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            topMargin=0.5*inch, bottomMargin=0.5*inch, 
                            leftMargin=0.5*inch, rightMargin=0.5*inch)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # --- Header Image ---
    if os.path.exists("header.jpg"):
        # Width of letter is 8.5 inch. Margins are 0.5 each -> 7.5 inch usable.
        # Image aspect ratio check? Let's assume banner.
        # Set width to 7.5 inch, allow height to scale (preserveRatio)
        im = Image("header.jpg", width=7.5*inch, height=2.5*inch)
        im.hAlign = 'CENTER'
        elements.append(im)
        elements.append(Spacer(1, 0.2 * inch))
    else:
        # Fallback text
        elements.append(Paragraph("HONEST PACKAGING", title_style))
        elements.append(Spacer(1, 0.2 * inch))
    
    # --- Quotation Details ---
    # Organized in a small grid or just lines
    elements.append(Paragraph(f"<b>Quotation No:</b> {quotation.quotation_number}", normal_style))
    elements.append(Paragraph(f"<b>Date:</b> {quotation.created_date.strftime('%Y-%m-%d')}", normal_style))
    elements.append(Spacer(1, 0.2 * inch))
    
    # --- Party Details ---
    elements.append(Paragraph("<b>To:</b>", heading_style))
    elements.append(Paragraph(f"{party.name}", normal_style))
    if party.address:
        elements.append(Paragraph(f"{party.address}", normal_style))
    if party.mobile_number:
        elements.append(Paragraph(f"Mobile: {party.mobile_number}", normal_style))
    elements.append(Spacer(1, 0.3 * inch))
    
    # --- Items Table ---
    # Columns: SN, Size (LxWxH) [Inch], Specification, Ply, Qty, Rate, Amount
    data = [['SN', 'Size (Inch)', 'Specification', 'Ply', 'Qty', 'Rate (Rs)', 'Amount (Rs)']]
    
    for idx, item in enumerate(items, 1):
        # Size Logic: stored values (item.length, etc.) are always in MM.
        # We want to display in Inches.
        l = item.length / 25.4
        w = item.width / 25.4
        h = item.height / 25.4
        
        # .0f to avoid 12.0 if user wants clean 12, or .2g? 
        # User asked for "12X8X6", implies integers if possible or clean float.
        # .1f is safe usually. 12.0
        # Let's try to format nicely: if integer, show int.
        def fmt(val):
            return f"{val:.0f}" if val.is_integer() else f"{val:.2f}"

        # Actually user example was 12X8X6, so let's stick to .1f or .0f if close.
        # Re-reading prompt "it must be 12X8X6".
        size_str = f"{l:.1f} x {w:.1f} x {h:.1f}"
        
        # Specification Logic (Paper Type + GSM)
        # item.layer_details is a list of dicts or None
        spec_text = ""
        if item.layer_details:
            # We want a concise list: "120 Golden / 100 Flute / ..."
            # item.layer_details might be a list of dicts.
            try:
                # If it's stored as JSON, it comes out as list
                specs = []
                for ld in item.layer_details:
                    # ld: {'layer':..., 'paper':..., 'gsm':...}
                    # Format: Top Liner: 120 Golden
                    specs.append(f"{ld['layer']} {ld['gsm']} {ld['paper']}")
                spec_text = " / ".join(specs)
            except:
                spec_text = f"{item.box_type} Box" # Fallback
        else:
             spec_text = f"{item.box_type} Box" # Fallback

        # Use Paragraph for wrapping text in Specification column
        spec_para = Paragraph(spec_text, normal_style)

        amount = item.selling_price * item.quantity if item.quantity else 0
        
        row = [
            str(idx),
            size_str,
            spec_para, # Wrapped
            str(item.ply),
            str(item.quantity) if item.quantity else "1000",
            f"{item.selling_price:.2f}",
            f"{amount:.2f}"
        ]
        data.append(row)
        
    # Total Row
    # Need to sum the last column carefully
    total_amount = 0
    for r in data[1:]:
        try:
            total_amount += float(r[-1])
        except:
            pass # Paragraph or other issue

    data.append(['', '', '', '', 'Total', '', f"{total_amount:.2f}"])

    # Table Styling
    # Adjust widths: SN, Size, Spec, Ply, Qty, Rate, Amount
    # Total width ~ 7.5 inch
    col_widths = [0.4*inch, 1.5*inch, 2.5*inch, 0.5*inch, 0.8*inch, 0.9*inch, 1.0*inch]
    
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.orange),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'), # Total Info Bold
    ]))
    elements.append(t)
    
    # --- Footer ---
    elements.append(Spacer(1, 0.5 * inch))
    # --- Footer (Terms) ---
    elements.append(Spacer(1, 0.5 * inch))
    
    # Fetch Terms
    from database import SessionLocal
    from models import Terms
    
    db = SessionLocal()
    terms_obj = db.query(Terms).first()
    db.close()
    
    if terms_obj and terms_obj.content:
        elements.append(Paragraph("<b>Terms & Conditions:</b>", heading_style))
        # Convert newlines to breaks for PDF
        terms_html = terms_obj.content.replace('\n', '<br/>')
        elements.append(Paragraph(terms_html, normal_style))
        elements.append(Spacer(1, 0.2 * inch))

    elements.append(Paragraph("Thank you for your business!", normal_style))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

def generate_whatsapp_link(quotation, party, total_amount):
    """
    Generates a WhatsApp click-to-chat link.
    """
    if not party.mobile_number:
        return None
        
    # Helpers
    def clean_phone(number):
        # Remove spaces, dashes, parentheses
        return ''.join(c for c in number if c.isdigit())
        
    phone = clean_phone(party.mobile_number)
    if len(phone) == 10:
        phone = "91" + phone # Assuming India default if 10 digits
        
    # Create Item Summary (e.g. 12x8x6 5 Ply)
    item_summaries = []
    for item in quotation.items:
        size_str = f"{item.length/25.4:.1f}x{item.width/25.4:.1f}x{item.height/25.4:.1f}"
        item_summaries.append(f"{size_str} ({item.ply} Ply)")
    
    item_text = ", ".join(item_summaries)

    text = f"""*Quotation from Honest Packaging*
Quotation No: {quotation.quotation_number}
Date: {quotation.created_date.strftime('%Y-%m-%d')}

Hello {party.name},

As discussed, please find attached our quotation for {item_text}.

Price is based on current specifications and is valid for 15 days.
For any clarification, feel free to connect.

Thank you.
    """
    
    import urllib.parse
    encoded_text = urllib.parse.quote(text)
    
    return f"https://wa.me/{phone}?text={encoded_text}"
