import streamlit as st
import pandas as pd
from database import SessionLocal
from models import Quotation, QuotationItem, Party

def reports_page():
    st.title("Reports & History")
    
    db = SessionLocal()
    
    tab1, tab2 = st.tabs(["All Quotations", "Party-wise History"])
    
    with tab1:
        st.subheader("Recent Quotations")
        
        # Search Filter
        search_query = st.text_input("🔍 Search by Party Name, Box Size, or Quotation Number", "").lower()
        
        # Fetch Data
        quotations = db.query(Quotation).order_by(Quotation.created_date.desc()).all()
        
        # --- HEADER ---
        # Adjust column ratios using st.columns
        # Actions | Date | Q No | Party | Sizes | Qty | Amount | Status | Del
        h_cols = st.columns([2.5, 1.2, 1, 2, 2, 0.8, 1, 1.5, 0.5])
        h_cols[0].markdown("**Actions**")
        h_cols[1].markdown("**Date**")
        h_cols[2].markdown("**Q No**")
        h_cols[3].markdown("**Party**")
        h_cols[4].markdown("**Sizes**")
        h_cols[5].markdown("**Qty**")
        h_cols[6].markdown("**Amount**")
        h_cols[7].markdown("**Status**")
        h_cols[8].markdown("**Del**")
        
        st.divider()
        
        if quotations:
            count = 0
            for q in quotations:
                party_name = q.party.name if q.party else "Unknown"
                
                # aggregate sizes and qtys
                size_list = []
                qty_list = []
                for i in q.items:
                     size_list.append(f"{i.length/25.4:.1f}x{i.width/25.4:.1f}x{i.height/25.4:.1f}")
                     qty_list.append(str(i.quantity))
                sizes = ", ".join(size_list)
                qtys = ", ".join(qty_list)
                
                # Filter Logic
                if search_query:
                    initials = "".join([w[0] for w in party_name.split() if w]).lower()
                    search_str = f"{party_name} {q.quotation_number} {sizes} {initials}".lower()
                    if search_query not in search_str:
                        continue
                
                count += 1
                if count > 50 and not search_query:
                    # Limit display for performance if not searching
                    if count == 51:
                         st.caption("Showing first 50 results. Use search to find older quotations.")
                    continue

                # --- ROW RENDER ---
                with st.container():
                    c = st.columns([2.5, 1.2, 1, 2, 2, 0.8, 1, 1.5, 0.5])
                    
                    # 1. Actions (PDF, WA, Email) - View removed
                    with c[0]:
                        ac_cols = st.columns([1, 1, 1])
                        
                        # PDF
                        from modules.pdf_utils import generate_quotation_pdf
                        pdf_bytes = generate_quotation_pdf(q, q.items, q.party)
                        
                        ac_cols[0].download_button(
                            label="📄",
                            data=pdf_bytes,
                            file_name=f"{q.quotation_number}.pdf",
                            mime="application/pdf",
                            key=f"pdf_{q.id}",
                            help="Download PDF"
                        )
                        
                        # WhatsApp
                        from modules.pdf_utils import generate_whatsapp_link
                        wa_link = generate_whatsapp_link(q, q.party, q.total_amount)
                        if wa_link:
                            ac_cols[1].link_button("💬", wa_link, help="Share on WhatsApp")
                        else:
                            ac_cols[1].caption("🚫")
                            
                        # Email
                        with ac_cols[2].popover("📧", help="Send Email"):
                            default_email = q.party.email if q.party and q.party.email else ""
                            rec_email = st.text_input("To:", value=default_email, key=f"email_in_{q.id}")
                            if st.button("Send", key=f"btn_email_{q.id}"):
                                if rec_email:
                                    from modules.email_utils import send_email_with_pdf
                                    import os
                                    pdf_dir = "PDF"
                                    if not os.path.exists(pdf_dir):
                                        os.makedirs(pdf_dir)
                                    temp_path = os.path.join(pdf_dir, f"{q.quotation_number}.pdf")
                                    with open(temp_path, "wb") as f:
                                        f.write(pdf_bytes.getvalue())
                                        
                                    subj = f"Quotation {q.quotation_number}"
                                    body = f"Please find attached quotation {q.quotation_number}."
                                    if send_email_with_pdf(rec_email, subj, body, temp_path):
                                        st.toast(f"Sent to {rec_email}!", icon="📧")
                                    else:
                                        st.error("Failed.")
                    
                    # 2. Date
                    c[1].write(q.created_date.strftime("%Y-%m-%d"))
                    
                    # 3. Q No
                    c[2].write(q.quotation_number)
                    
                    # 4. Party
                    c[3].write(party_name)
                    
                    # 5. Sizes
                    c[4].caption(sizes)
                    
                    # 6. Qty
                    c[5].write(qtys)
                    
                    # 7. Amount
                    c[6].write(f"{q.total_amount:.0f}")
                    
                    # 8. Status
                    current_status = q.status
                    status_opts = ["Draft", "Finalised", "Dispatched", "Billed"]
                    if current_status not in status_opts:
                        status_opts.append(current_status)
                        
                    new_status = c[7].selectbox(
                        "Status", 
                        status_opts, 
                        index=status_opts.index(current_status), 
                        key=f"status_{q.id}", 
                        label_visibility="collapsed"
                    )
                    
                    if new_status != current_status:
                        q.status = new_status
                        db.commit()
                        st.toast(f"Updated status to {new_status}")
                    
                    # 9. Delete
                    if c[8].button("🗑️", key=f"del_{q.id}", help="Delete Quotation"):
                         if q.status == "Draft":
                             db.query(QuotationItem).filter(QuotationItem.quotation_id == q.id).delete(synchronize_session=False)
                             db.query(Quotation).filter(Quotation.id == q.id).delete(synchronize_session=False)
                             db.commit()
                             st.success("Deleted!")
                             st.rerun()
                         else:
                             st.error("Only Drafts!")
                    
                st.divider() # Row separator
                
        else:
            st.info("No quotations found.")
            
    with tab2:
        st.subheader("Select Party to View History")
        parties = db.query(Party).all()
        party_names = [p.name for p in parties]
        sel_party = st.selectbox("Party", party_names)
        
        if sel_party:
            selected_p_obj = next(p for p in parties if p.name == sel_party)
            qs = db.query(Quotation).filter(Quotation.party_id == selected_p_obj.id).all()
            
            if qs:
                # Get item details
                history_data = []
                for q in qs:
                    for item in q.items:
                        history_data.append({
                            "Date": q.created_date.date(),
                            "Q No": q.quotation_number,
                            "Box Size": f"{item.length/25.4:.1f}x{item.width/25.4:.1f}x{item.height/25.4:.1f}",
                            "Ply": item.ply,
                            "Cost": item.cost_per_box,
                            "Selling Price": item.selling_price,
                            "Margin %": item.margin_percent
                        })
                st.dataframe(pd.DataFrame(history_data))
            else:
                st.info("No history for this party.")
    
    db.close()
