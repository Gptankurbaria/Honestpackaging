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
        
        quotations = db.query(Quotation).order_by(Quotation.created_date.desc()).all()
        
        if quotations:
            data = []
            for q in quotations:
                party_name = q.party.name if q.party else "Unknown"
                
                # aggregate sizes (Convert mm to inch for display)
                # Stored length is mm. Display format: LxWxH (Inch)
                sizes = ", ".join([f"{i.length/25.4:.1f}x{i.width/25.4:.1f}x{i.height/25.4:.1f}" for i in q.items])
                
                # Filter Logic
                if search_query:
                    # Generate initials for search (e.g. "Jyoti Electricals" -> "je")
                    initials = "".join([w[0] for w in party_name.split() if w]).lower()
                    search_str = f"{party_name} {q.quotation_number} {sizes} {initials}".lower()
                    if search_query not in search_str:
                        continue
                
                data.append({
                    "Date": q.created_date,
                    "Q Not": q.quotation_number,
                    "Party": party_name,
                    "Sizes": sizes,  # Added for visibility and search
                    "Total Amount": q.total_amount,
                    "Status": q.status,
                    "ID": q.id # Add ID here to match filtered data
                })
            df_q = pd.DataFrame(data)
            df_q["Delete"] = False # Checkbox for deletion
            
            edited_df = st.data_editor(
                df_q,
                key="quotation_status_editor",
                column_config={
                    "ID": None, # Hide ID
                    "Delete": st.column_config.CheckboxColumn(
                        "Delete",
                        help="Select to delete this quotation",
                        default=False
                    ),
                    "Status": st.column_config.SelectboxColumn(
                        "Status",
                        help="Update Quotation Status",
                        options=["Draft", "Finalised", "Dispatched", "Billed"],
                        required=True
                    )
                },
                disabled=["Date", "Q Not", "Party", "Sizes", "Total Amount"], # IDs and View data disabled
                use_container_width=True
            )
            
            col_act1, col_act2 = st.columns([1, 4])
            
            if col_act1.button("Save Changes"):
                # Detect changes
                changes_count = 0
                deletes_count = 0
                
                # We need to process deletes first to avoid status update errors on deleted items
                to_delete = []
                blocked_deletes = []
                
                for index, row in edited_df.iterrows():
                    if row["Delete"]:
                        # Enforce Delete only if Draft
                        if row["Status"] == "Draft":
                            to_delete.append(int(row["ID"]))
                        else:
                            blocked_deletes.append(row["Q Not"])
                        
                if blocked_deletes:
                    st.error(f"Cannot delete non-Draft quotations: {', '.join(blocked_deletes)}")
                
                if to_delete:
                    # Delete logic
                    db.query(QuotationItem).filter(QuotationItem.quotation_id.in_(to_delete)).delete(synchronize_session=False)
                    db.query(Quotation).filter(Quotation.id.in_(to_delete)).delete(synchronize_session=False)
                    deletes_count = len(to_delete)
                
                # Updates (skip deleted)
                for index, row in edited_df.iterrows():
                    q_id = int(row["ID"])
                    if q_id not in to_delete:
                        new_status = row["Status"]
                        q_obj = db.query(Quotation).filter(Quotation.id == q_id).first()
                        if q_obj and q_obj.status != new_status:
                            q_obj.status = new_status
                            changes_count += 1
                
                if changes_count > 0 or deletes_count > 0:
                    db.commit()
                    st.success(f"Updated {changes_count} statuses using, Deleted {deletes_count} quotations.")
                    st.rerun()
                else:
                    st.info("No changes detected.")
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
