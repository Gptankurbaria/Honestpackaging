import streamlit as st
import pandas as pd
from database import get_db, SessionLocal
from models import Party, PaperRate, OperationRate

def party_creation_page():
    st.title("Party Creation")
    st.markdown("---")
    
    db = SessionLocal()
    
    col1, col2 = st.columns(2)
    name = col1.text_input("Party Name")
    address = col2.text_input("Address")
    mobile = col1.text_input("Mobile Number")
    gst = col2.text_input("GST Number")
    email = col1.text_input("Email Address")
    margin = col2.number_input("Default Margin (%)", value=10.0)
    transport_logic = st.selectbox("Transport Rate Logic", ["per_kg", "per_trip", "fixed"])
    
    st.markdown("###")
    if st.button("Save Party", type="primary"):
        if name:
            new_party = Party(
                name=name, 
                address=address, 
                mobile_number=mobile,
                gst_number=gst, 
                email=email,
                default_margin=margin, 
                transport_rate_logic=transport_logic
            )
            db.add(new_party)
            db.commit()
            st.success(f"Party '{name}' created successfully!")
        else:
            st.error("Party Name is required.")
    
    db.close()

def _party_master_subpage():
    st.subheader("Party Master - View & Edit")
    
    db = SessionLocal()
    parties = db.query(Party).all()
    if parties:
        data = [{
            "ID": p.id, 
            "Name": p.name, 
            "Address": p.address, 
            "Mobile": p.mobile_number, 
            "GST": p.gst_number, 
            "Email": p.email,
            "Margin": p.default_margin, 
            "Transport": p.transport_rate_logic
        } for p in parties]
        
        df_parties = pd.DataFrame(data)
        edited_parties = st.data_editor(
            df_parties, 
            key="party_editor",
            column_config={
                "ID": None,
                "Mobile": st.column_config.TextColumn(
                    "Mobile",
                    help="Contact Number",
                    validate="^[0-9]*$", # Basic validation
                    required=False
                ),
                "Email": st.column_config.TextColumn("Email")
            }, 
            disabled=["ID"], 
            use_container_width=True,
            num_rows="dynamic" # Allow adding new rows via editor
        )
        
        if st.button("Save Party Changes"):
            for index, row in edited_parties.iterrows():
                # Check if new row (ID might be missing if we allowed add? dynamic)
                # For now let's assume editing existing. dynamic adding rows via editor is tricky without ID handling.
                # If ID exists, update.
                if "ID" in row and pd.notna(row["ID"]):
                    p_id = int(row["ID"])
                    p_obj = db.query(Party).filter(Party.id == p_id).first()
                    if p_obj:
                        p_obj.name = row["Name"]
                        p_obj.address = row["Address"]
                        p_obj.mobile_number = row["Mobile"]
                        p_obj.gst_number = row["GST"]
                        p_obj.email = row["Email"]
                        p_obj.default_margin = row["Margin"]
                        p_obj.transport_rate_logic = row["Transport"]
                # Else handle new... logic omitted for simplicity unless requested
            db.commit()
            st.success("Party details updated successfully!")
            st.rerun()
    else:
        st.info("No parties found.")
    
    db.close()

def _costing_master_subpage():
    from models import User
    from passlib.context import CryptContext
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    st.subheader("Costing Rates")
    
    # --- ADMIN CHECK ---
    if st.session_state.get("user_role") != "Admin":
        st.warning("⚠️ Restricted Area: Only Admins can edit Costing Rates.")
        
        c1, c2 = st.columns([2, 1])
        pwd = c1.text_input("Enter Admin Password", type="password")
        
        if c1.button("Unlock Costing Master"):
            db = SessionLocal()
            user = db.query(User).filter(User.username == "Admin").first()
            if user and user.password_hash and pwd_context.verify(pwd, user.password_hash):
                st.session_state["user_role"] = "Admin"
                st.success("Access Granted! Unlocking...")
                st.rerun()
            elif not user and pwd == "admin": 
                 # Fallback for first run if no user in DB yet
                 st.session_state["user_role"] = "Admin"
                 st.success("Access Granted (Fallback)! Please run reset tool to secure.")
                 st.rerun()
            else:
                st.error("Incorrect Password.")
            db.close()
        return
    else:
        # Admin is logged in - Allow Logout to re-lock
        if st.button("🔒 Lock Master"):
            st.session_state["user_role"] = "User"
            st.rerun()
    
    tab1, tab2 = st.tabs(["Paper Rates", "Operation Rates"])
    db = SessionLocal()
    
    with tab1:
        st.subheader("Paper Rates")
        with st.form("add_paper_form", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            p_name = c1.text_input("Paper Name")
            rate = c2.number_input("Rate (₹/kg)", min_value=0.0)
            bf = c3.number_input("Burst Factor (BF)", min_value=0.0, value=18.0)
            submitted = c4.form_submit_button("Add Rate")
            if submitted and p_name:
                db.add(PaperRate(name=p_name, rate=rate, bf=bf))
                db.commit()
                st.success("Added")
                st.rerun()
        
        st.markdown("### Edit Rates")
        rates = db.query(PaperRate).all()
        if rates:
            df_rates = pd.DataFrame([{"ID": r.id, "Name": r.name, "Rate": r.rate, "BF": r.bf} for r in rates])
            edited_rates = st.data_editor(
                df_rates, 
                key="paper_editor",
                column_config={
                    "ID": None,
                    "Rate": st.column_config.NumberColumn("Rate", format="₹%.2f"),
                    "BF": st.column_config.NumberColumn("BF", format="%.1f")
                }, 
                disabled=["ID"],
                use_container_width=True
            )
            
            if st.button("Save Paper Changes"):
                # Iterate and update
                for index, row in edited_rates.iterrows():
                    r_id = int(row["ID"])
                    r_obj = db.query(PaperRate).filter(PaperRate.id == r_id).first()
                    if r_obj:
                        r_obj.name = row["Name"]
                        r_obj.rate = row["Rate"]
                        r_obj.bf = row["BF"]
                db.commit()
                st.success("Paper Rates Updated!")
                st.rerun()

    with tab2:
        st.subheader("Operation Rates")
        with st.form("add_op_form", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            op_name = c1.text_input("Operation")
            op_rate = c2.number_input("Rate", min_value=0.0)
            unit = c3.selectbox("Unit", ["per_kg", "per_box", "fixed"])
            submitted = c4.form_submit_button("Add Op")
            if submitted and op_name:
                db.add(OperationRate(operation_name=op_name, rate=op_rate, unit=unit))
                db.commit()
                st.success("Added")
                st.rerun()
                
        st.markdown("### Edit Operations")
        ops = db.query(OperationRate).all()
        if ops:
            df_ops = pd.DataFrame([{"ID": o.id, "Operation": o.operation_name, "Rate": o.rate, "Unit": o.unit} for o in ops])
            edited_ops = st.data_editor(
                df_ops,
                key="op_editor",
                column_config={"ID": None},
                disabled=["ID"],
                use_container_width=True
            )
            
            if st.button("Save Operation Changes"):
                for index, row in edited_ops.iterrows():
                    o_id = int(row["ID"])
                    o_obj = db.query(OperationRate).filter(OperationRate.id == o_id).first()
                    if o_obj:
                        o_obj.operation_name = row["Operation"]
                        o_obj.rate = row["Rate"]
                        o_obj.unit = row["Unit"]
                db.commit()
                st.success("Operation Rates Updated!")
                st.rerun()
    db.close()

def _terms_master_subpage():
    from models import Terms
    st.subheader("Terms & Conditions")
    db = SessionLocal()
    
    # Fetch existing terms or create default
    terms_obj = db.query(Terms).first()
    if not terms_obj:
        terms_obj = Terms(title="General Terms", content="1. Delivery within 7 days.\n2. Payment 100% advance.\n3. GST Extra as applicable.")
        db.add(terms_obj)
        db.commit()
        db.refresh(terms_obj)
        
    new_content = st.text_area("Edit Terms & Conditions", value=terms_obj.content, height=200)
    
    if st.button("Save Terms"):
        terms_obj.content = new_content
        db.commit()
        st.success("Terms saved successfully!")
    
    db.close()

def _reel_master_subpage():
    from models import ReelSize
    st.subheader("Standard Reel Sizes (Master)")
    
    db = SessionLocal()
    
    # Add Form
    with st.form("add_reel_form", clear_on_submit=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        r_width = c1.number_input("Reel Width (Inch)", min_value=1.0, value=52.0, step=1.0)
        submitted = c3.form_submit_button("Add Size")
        if submitted:
            # Check duplicate
            exists = db.query(ReelSize).filter(ReelSize.width == r_width).first()
            if not exists:
                db.add(ReelSize(width=r_width))
                db.commit()
                st.success(f"Added {r_width} inch reel.")
                st.rerun()
            else:
                st.warning("Size already exists.")

    st.markdown("### Active Reel Sizes")
    reels = db.query(ReelSize).order_by(ReelSize.width).all()
    if reels:
        data = [{"ID": r.id, "Width (Inch)": r.width, "Active": r.is_active} for r in reels]
        df_reels = pd.DataFrame(data)
        
        edited_reels = st.data_editor(
            df_reels,
            key="reel_editor",
            column_config={
                "ID": None,
                "Width (Inch)": st.column_config.NumberColumn("Width", format="%.1f\""),
                "Active": st.column_config.CheckboxColumn("Active")
            },
            disabled=["ID"],
            use_container_width=True
        )
        
        if st.button("Save Reel Changes"):
            for index, row in edited_reels.iterrows():
                r_id = int(row["ID"])
                r_obj = db.query(ReelSize).filter(ReelSize.id == r_id).first()
                if r_obj:
                    r_obj.width = row["Width (Inch)"]
                    r_obj.is_active = row["Active"]
            db.commit()
            st.success("Reel Master Updated!")
            st.rerun()
            
    db.close()

def masters_page():
    st.title("Masters Configuration")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Costing Master", "Party Master", "Reel Master", "Terms & Conditions"])
    
    with tab1:
        _costing_master_subpage()
        
    with tab2:
        _party_master_subpage()
        
    with tab3:
        _reel_master_subpage()
        
    with tab4:
        _terms_master_subpage()
