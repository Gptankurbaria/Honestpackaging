import streamlit as st
import pandas as pd
from database import SessionLocal
from models import Party, PaperRate, OperationRate
from modules.pdf_utils import generate_quotation_pdf, generate_whatsapp_link

def calculator_page():
    st.title("Cost Calculator")
    
    db = SessionLocal()
    
    # --- Handle Optimization Updates (Fix for StreamlitAPIException) ---
    if "pending_gsm_updates" in st.session_state:
        updates = st.session_state.pop("pending_gsm_updates")
        for key, val in updates.items():
            st.session_state[key] = val
        # No need to rerun again, we are already in the rerun and updated *before* widgets
            
    # 1. Select Party
    parties = db.query(Party).filter(Party.is_active == True).all()
    party_names = [p.name for p in parties]
    # Updated options to include create new
    options = ["General"] + party_names + ["+ Create New Party"]
    selected_party_name = st.selectbox("Select Party", options)
    
    selected_party = None
    default_margin = 10.0

    if selected_party_name == "+ Create New Party":
        with st.expander("Create New Party Details", expanded=True):
            with st.form("new_party_form"):
                new_p_name = st.text_input("Party Name")
                new_p_mobile = st.text_input("Mobile Number")
                new_p_address = st.text_area("Address", height=100)
                new_p_margin = st.number_input("Default Margin (%)", value=10.0, step=0.5)
                submit_new_party = st.form_submit_button("Save New Party")
                
                if submit_new_party:
                    if new_p_name:
                        try:
                            new_party = Party(
                                name=new_p_name,
                                mobile_number=new_p_mobile,
                                address=new_p_address,
                                default_margin=new_p_margin,
                                is_active=True
                            )
                            db.add(new_party)
                            db.commit()
                            st.success(f"Party '{new_p_name}' created! Please select it from the dropdown.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creating party: {e}")
                    else:
                        st.error("Party Name is required.")
                        
    elif selected_party_name != "General":
        selected_party = next((p for p in parties if p.name == selected_party_name), None)
        if selected_party:
            default_margin = selected_party.default_margin
            st.info(f"Default Margin for {selected_party_name}: {default_margin}%")

    # Create Main Layout Containers
    results_container = st.container()
    st.markdown("---")
    inputs_container = st.container()

    # --- INPUTS SECTION ---
    with inputs_container:
        # Layout: Split Screen
        left_col, right_col = st.columns(2, gap="medium")
        
        with left_col:
            # 2. Box Specifications
            st.subheader("Box Specifications")
            
            # Unit Switcher
            unit_selection = st.radio("Input Unit", ["Inch", "mm"], horizontal=True)
            
            # Advanced Box Specs (Style & Allowances)
            st.markdown("###")
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            
            # Defaults based on unit
            default_cutting = 1.5 if unit_selection == "Inch" else 40.0
            default_decel = 0.0
            
            box_style = col_s1.selectbox("Box Style", ["REGULAR", "OVER FLIP"])
            joint_type = col_s2.selectbox("Joint Type", ["1PC", "2PC"])
            cutting_plus = col_s3.number_input(f"CUTTING+", value=default_cutting)
            decel_plus = col_s4.number_input(f"DECEL+", value=default_decel)
            
            col1, col2, col3, col4 = st.columns(4)
            
            if unit_selection == "Inch":
                length_in = col1.number_input("Length (in)", min_value=0.0, value=12.0)
                width_in = col2.number_input("Width (in)", min_value=0.0, value=8.0)
                height_in = col3.number_input("Height (in)", min_value=0.0, value=6.0)
                
                # Convert to mm for internal approx formulas
                length = length_in * 25.4
                width = width_in * 25.4
                height = height_in * 25.4
            else:
                length = col1.number_input("Length (mm)", min_value=0.0, value=300.0)
                width = col2.number_input("Width (mm)", min_value=0.0, value=200.0)
                height = col3.number_input("Height (mm)", min_value=0.0, value=150.0)

            ply = col4.selectbox("Ply", [3, 5, 7, 9])
        
        with right_col:
            # 3. Paper Specifications (Dynamic based on Ply)
            st.subheader("Paper Specifications")
            
            # Fetch paper rates for dropdown
            paper_rates = db.query(PaperRate).all()
            if not paper_rates:
                st.warning("No Paper Rates found. Please add them in Master Data.")
                paper_options = {} 
                paper_details = {}
            else:
                # Update options to store more data
                paper_options = {f"{p.name} ({p.rate}/kg)": p.rate for p in paper_rates}
                # Store full objects for lookup
                paper_details = {f"{p.name} ({p.rate}/kg)": p for p in paper_rates}
            
            layers = []
            if ply == 3:
                layers = ["Top Liner", "Flute", "Bottom Liner"]
            elif ply == 5:
                layers = ["Top Liner", "Flute 1", "Middle Liner", "Flute 2", "Bottom Liner"]
            elif ply == 7:
                layers = ["Top Liner", "Flute 1", "Middle Liner 1", "Flute 2", "Middle Liner 2", "Flute 3", "Bottom Liner"]
            elif ply == 9:
                layers = ["Top Liner", "Flute 1", "Middle Liner 1", "Flute 2", "Middle Liner 2", "Flute 3", "Middle Liner 3", "Flute 4", "Bottom Liner"]
            
            # --- Flute Factor Input ---
            c_f1, c_f2 = st.columns(2)
            flute_factor = c_f1.number_input("Flute Factor (Take-up)", value=1.40, step=0.05, min_value=1.0)
            wastage_pct = c_f2.number_input("Wastage %", value=5.0, step=0.5, min_value=0.0)
            
            total_effective_gsm = 0.0
            total_material_cost_per_sqm = 0.0 # Based on effective weight
            total_theoretical_bs = 0.0 # Bursting Strength
            current_layer_details = [] # Capture for PDF
            
            if paper_options:
                with st.expander(f"Layer Details ({len(layers)} Layers)", expanded=True):
                    # Data collection for optimization
                    selected_layer_configs = []
                    
                    for layer in layers:
                        c1, c2, c3 = st.columns([2, 1, 1])
                        # use session state keys for papers to persist selections
                        sel_paper = c1.selectbox(f"{layer}", list(paper_options.keys()), key=layer, label_visibility="visible")
                        gsm = c2.number_input(f"GSM", min_value=60, value=120, key=f"gsm_{layer}", label_visibility="visible")
                        
                        if sel_paper:
                            # Extract just name for cleaner save (remove rate info if possible, or keep full)
                            # sel_paper string format: "Name (Rate/kg)"
                            paper_name_only = sel_paper.split(' (')[0] if '(' in sel_paper else sel_paper
                            
                            p_obj = paper_details[sel_paper]
                            rate = p_obj.rate
                            bf = p_obj.bf if p_obj.bf else 18.0
                            
                            current_layer_details.append({
                                "layer": layer,
                                "paper": paper_name_only,
                                "gsm": gsm,
                                "bf": bf
                            })
                            
                            # Apply flute factor ONLY to flute layers
                            if "Flute" in layer:
                                effective_gsm = gsm * flute_factor
                                layer_bs = (bf * gsm) / 1000
                                is_flute = True
                            else:
                                effective_gsm = gsm
                                layer_bs = (bf * gsm) / 1000
                                is_flute = False
                                
                            total_effective_gsm += effective_gsm
                            total_theoretical_bs += layer_bs
                            
                            # Cost = Effective GSM (kg/sqm) * Rate (per kg)
                            total_material_cost_per_sqm += (effective_gsm * rate)
                            
                            selected_layer_configs.append({
                                "layer": layer,
                                "bf": bf,
                                "rate": rate,
                                "flute_factor": flute_factor if is_flute else 1.0
                            })
                            
                        # Show BS contribution
                        c3.markdown(f"<small>BS: {layer_bs:.2f}</small>", unsafe_allow_html=True)
            else:
                total_effective_gsm = 0

            # --- Strength Display & Optimization ---
            c_bs1, c_bs2 = st.columns([2, 1])
            c_bs1.info(f"⚡ Theoretical Box Bursting Strength (BS): {total_theoretical_bs:.2f} kg/cm²")
            
            with c_bs2:
                target_bs = st.number_input("Target Strength (BS)", min_value=1.0, value=6.0, step=0.5)
            
            if st.button("✨ Optimize GSM for Cost"):
                import itertools
                standard_gsms = [80, 100, 120, 140, 150, 180, 200, 230, 250]
                
                best_combo = None
                min_cost = float('inf')
                
                # Progress bar for visual feedback
                prog_bar = st.progress(0)
                
                # Solver: Iterate combinations of GSMs for the selected papers
                # Limit search if too huge (e.g. 5 ply = 32k ops, fast enough in python usually)
                combinations = list(itertools.product(standard_gsms, repeat=len(selected_layer_configs)))
                total_combos = len(combinations)
                
                for idx, combo in enumerate(combinations):
                    # Check validity
                    if idx % 1000 == 0:
                        prog_bar.progress(min(idx / total_combos, 1.0))
                    
                    calc_bs = 0.0
                    calc_cost = 0.0
                    
                    for i, layer_gsm in enumerate(combo):
                        cfg = selected_layer_configs[i]
                        # BS = BF * GSM / 1000
                        calc_bs += (cfg['bf'] * layer_gsm) / 1000
                        # Cost = GSM * Factor * Rate
                        calc_cost += (layer_gsm * cfg['flute_factor'] * cfg['rate'])
                        
                    if calc_bs >= target_bs:
                        if calc_cost < min_cost:
                            min_cost = calc_cost
                            best_combo = combo
                
                prog_bar.empty()
                
                if best_combo:
                    st.success(f"Optimal Solution Found! Cost Indicator: {min_cost:.2f}")
                    # Apply logic
                    # We can't set nested key directly in a button callback easily without rerun or session state
                    # We will store suggestion in session state and show an "Apply" button or just apply?
                    # Streamlit logic: Update state keys then rerun.
                    
                    updates = {}
                    for i, best_gsm in enumerate(best_combo):
                        layer_name = selected_layer_configs[i]['layer']
                        updates[f"gsm_{layer_name}"] = best_gsm
                    
                    st.session_state["pending_gsm_updates"] = updates
                    
                    st.toast("GSMs Updated! Rerunning...", icon="✅")
                    st.rerun()
                else:
                    st.error("No combination met the Target BS with available GSMs.")
            
        
        with left_col: # Reel suggestion uses sheet info from left col logic, but we are inside 'right_col' currently?
             # No, inputs_container -> two cols.
             # Wait, logic flow issue. Sheet Size determines Reel Size.
             # Sheet Size logic is BELOW input section. We need to move it UP or calculate it independently.
             pass 

        # -- LOWER INPUT SECTION (Sheet Calc & Ops) --
        # 4. Sheet Size Calculation & Weight
        st.subheader("Sheet Size & Weight")
        
        # Custom Styling for the Gold Box look
        st.markdown("""
        <style>
        .allowance-box {
            background-color: #FFF8E1; /* Light Amber/Gold */
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #FFECB3;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        .allowance-val {
            font-size: 1.5rem;
            font-weight: bold;
            color: #FF6F00; /* Dark Amber */
        }
        .allowance-label {
            font-size: 0.9rem;
            color: #6D4C41;
            font-weight: 500;
        }
        </style>
        """, unsafe_allow_html=True)
        
        calc_method = st.radio("Calculation Method", ["Auto-Calculate (RSC)", "Manual Sheet Size"])
        
        if calc_method == "Auto-Calculate (RSC)":
            # Calculations of Sheet Size (Per Die/Per Piece)
            # Sheet Length:
            if joint_type == "1PC":
                # Standard: (L + W) * 2 + Cutting
                base_len = (length_in + width_in) * 2 if unit_selection == "Inch" else (length + width) * 2
                sheets_per_box = 1
            else: # 2PC
                # Split: (L + W) + Cutting (One piece covers half perimeter)
                base_len = (length_in + width_in) if unit_selection == "Inch" else (length + width)
                sheets_per_box = 2
                
            calc_sheet_len = base_len + cutting_plus
            
            # Sheet Width calculation based on Style
            if box_style == "OVER FLIP":
                 # Width + Width + Height
                 base_width_allowance = width_in * 2 if unit_selection == "Inch" else width * 2
            else:
                 # Width + Height (Standard RSC)
                 base_width_allowance = width_in if unit_selection == "Inch" else width
                 
            calc_sheet_wid = height_in + base_width_allowance + decel_plus if unit_selection == "Inch" else height + base_width_allowance + decel_plus
            
            # Display nicely in columns
            c1, c2 = st.columns(2)
            c1.markdown(f"""
            <div class="allowance-box">
                <div class="allowance-label">Cutting Size (Length)</div>
                <div class="allowance-val">{calc_sheet_len:.2f}</div>
            </div>
            """, unsafe_allow_html=True)
            
            c2.markdown(f"""
            <div class="allowance-box">
                <div class="allowance-label">Cutting Size (Width)</div>
                <div class="allowance-val">{calc_sheet_wid:.2f}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Set values for downstream
            if unit_selection == "Inch":
                sheet_length = calc_sheet_len * 25.4
                sheet_width = calc_sheet_wid * 25.4
            else:
                sheet_length = calc_sheet_len
                sheet_width = calc_sheet_wid
            
            if sheets_per_box > 1:
                st.info(f"ℹ️ 2PC Box Selected: Calculation is for 1 piece. Total cost will include 2 pieces.")
                
        else:
            sheets_per_box = 1 # Default manual
            c1, c2 = st.columns(2)
            if unit_selection == "Inch":
                sl_in = c1.number_input("Sheet Cutting Length (inch)", value=40.0)
                sw_in = c2.number_input("Sheet Cutting Width (inch)", value=20.0)
                sheet_length = sl_in * 25.4
                sheet_width = sw_in * 25.4
            else:
                sheet_length = c1.number_input("Sheet Cutting Length (mm)", value=1000.0)
                sheet_width = c2.number_input("Sheet Cutting Width (mm)", value=1000.0)
        
        # Weight Calculation (REVISED)
        # Area in sq m for ONE sheet
        area_sqm = (sheet_length * sheet_width) / 1_000_000
        
        # Gross Weight including Wastage
        # Effective GSM already includes Flute Factor
        # Divide by 1000 to get kg
        
        weight_per_sheet_kg = (area_sqm * total_effective_gsm) / 1000
        total_weight_kg = weight_per_sheet_kg * sheets_per_box
        
        # Apply Wastage
        final_weight_kg = total_weight_kg * (1 + wastage_pct/100)
        
        # 5. Operations
        # Operations calculation
        ops = db.query(OperationRate).filter(OperationRate.is_active==True).all()
        # Split costs
        variable_conversion_cost = 0.0
        total_fixed_cost = 0.0
        selected_ops = []
        
        with st.expander("Operations & Conversion Details", expanded=False):
            for op in ops:
                cost = 0
                use_op = st.checkbox(f"{op.operation_name} ({op.rate} {op.unit})", value=True)
                if use_op:
                    if op.unit == "per_kg":
                        cost = final_weight_kg * op.rate
                        variable_conversion_cost += cost
                        selected_ops.append((op.operation_name, cost, 'per_box'))
                    elif op.unit == "per_box":
                        cost = op.rate
                        variable_conversion_cost += cost
                        selected_ops.append((op.operation_name, cost, 'per_box'))
                    elif op.unit == "fixed":
                        cost = op.rate
                        total_fixed_cost += cost
                        selected_ops.append((op.operation_name, cost, 'fixed'))
        
        # After sheet size:
        
        # --- Reel Size Suggestion ---
        # Logic: Reel Width = Sheet Width + Trim (e.g. 50mm) OR Sheet Length + Trim
        # Usually corrugation runs perpendicular to flute?
        st.caption(f"Final Sheet Size: {sheet_length:.0f} x {sheet_width:.0f} mm")
        
        # --- REEL SIZE OPTIMIZATION (DB DRIVEN) ---
        with st.expander("Reel Size Suggestion (Deckle Optimization)", expanded=True):
            from models import ReelSize
            
            # Assumption: Deckle matches Sheet Width implicitly
            deckle_needed_mm = sheet_width
            trim_allowance_mm = 50 # Standard trim
            
            st.caption(f"Calculated based on Cutting Size (Width): {sheet_width:.1f} mm")
            
            min_reel_mm = deckle_needed_mm + trim_allowance_mm
            min_reel_inch = min_reel_mm / 25.4
            
            # Fetch Active Reels from Master
            active_reels = db.query(ReelSize).filter(ReelSize.is_active == True).order_by(ReelSize.width).all()
            
            if not active_reels:
                st.warning("No Active Reel Sizes found in Master. Please configure 'Reel Master'.")
                suggested_reel_inch = 0
                trim_percent = 0
            else:
                # 1. Single Up Logic
                best_reel = None
                best_trim_pct = 100.0
                
                # Find smallest reel that fits
                for r in active_reels:
                    if r.width >= min_reel_inch:
                        best_reel = r
                        
                        calc_trim_mm = (r.width * 25.4) - deckle_needed_mm
                        best_trim_pct = (calc_trim_mm / (r.width * 25.4)) * 100
                        break # Since ordered by width, first match is smallest capable
                
                r1, r2, r3, r4 = st.columns(4)
                r1.metric("Min Required", f"{min_reel_inch:.2f}\"")
                
                if best_reel:
                    r2.metric(f"Suggested Reel", f"{best_reel.width}\"")
                    r3.metric("Wastage", f"{best_trim_pct:.1f}%")
                    
                    if best_trim_pct > 10.0:
                        r4.error("High Wastage! (>10%)")
                    elif best_trim_pct > 5.0:
                        r4.warning(" Moderate Wastage")
                    else:
                        r4.success("Good Fit")
                else:
                    r2.error("No suitable reel found!")
                    r3.caption("(Need larger reel)")
                
                # 2. Double Up Logic (Improved Productivity)
                if min_reel_inch < 40: # Only relevant if single is small
                    double_deckle_mm = (sheet_width * 2) + trim_allowance_mm
                    double_required_inch = double_deckle_mm / 25.4
                    
                    best_double_reel = None
                    double_trim_pct = 100.0
                    
                    for r in active_reels:
                        if r.width >= double_required_inch:
                            best_double_reel = r
                            calc_trim = (r.width * 25.4) - (sheet_width * 2)
                            double_trim_pct = (calc_trim / (r.width * 25.4)) * 100
                            break
                    
                    if best_double_reel:
                        st.markdown("---")
                        c_d1, c_d2, c_d3 = st.columns([2,1,1])
                        c_d1.info(f"💡 **Double Up Strategy**: Run 2 sheets side-by-side.")
                        c_d2.metric("2-Up Reel", f"{best_double_reel.width}\"")
                        c_d3.metric("2-Up Wastage", f"{double_trim_pct:.1f}%")
                        
                        if best_reel and double_trim_pct < best_trim_pct:
                            c_d1.success(f"✅ Double Up saves {best_trim_pct - double_trim_pct:.1f}% material!")
        
        material_cost_per_sheet = (area_sqm * total_material_cost_per_sqm) / 1000
        material_cost = material_cost_per_sheet * sheets_per_box * (1 + wastage_pct/100) # Include wastage in cost

        st.subheader("Pricing Tiers")
        
        # Default tier data
        if "pricing_tiers" not in st.session_state:
             st.session_state["pricing_tiers"] = pd.DataFrame([
                {"Quantity": 1000, "Margin (%)": default_margin},
                {"Quantity": 2000, "Margin (%)": default_margin},
                {"Quantity": 5000, "Margin (%)": default_margin - 2.0}
             ])

        edited_tiers = st.data_editor(st.session_state["pricing_tiers"], num_rows="dynamic", use_container_width=True)
        st.session_state["pricing_tiers"] = edited_tiers

        # Calculate Results for Tiers
        tier_results = []
        
        for index, row in edited_tiers.iterrows():
            qty = row["Quantity"]
            margin_pct = row["Margin (%)"]
            
            # Amortize Fixed Cost
            amortized_fixed = total_fixed_cost / qty if qty > 0 else 0
            
            # Total Cost Per Box = Material + Variable Ops + Amortized Fixed
            total_cost_per_box = material_cost + variable_conversion_cost + amortized_fixed
            
            selling_price = total_cost_per_box / (1 - (margin_pct/100)) if margin_pct < 100 else 0
            profit = selling_price - total_cost_per_box
            total_value = selling_price * qty
            
            tier_results.append({
                "Quantity": int(qty),
                "Base Cost/Box": round(total_cost_per_box, 2),
                "Margin (%)": margin_pct,
                "Selling Price": round(selling_price, 2),
                "Profit/Box": round(profit, 2),
                "Total Value": round(total_value, 2)
            })
            
        results_df = pd.DataFrame(tier_results)
        
        # Display Results Table
        st.markdown("### Cost Analysis")
        st.dataframe(results_df, use_container_width=True)

        # Select Quantity for final context
        st.subheader("Select Quantity for Quotation")
        selected_qty = st.selectbox("Select Quantity", results_df["Quantity"].tolist())
        
        # Get selected row
        sel_row = results_df[results_df["Quantity"] == selected_qty].iloc[0]
        
        # Assign to variables compatible with downstream logic
        selling_price = sel_row["Selling Price"]
        total_cost = sel_row["Base Cost/Box"]
        profit = sel_row["Profit/Box"]
        margin_input = sel_row["Margin (%)"]
        conversion_cost = variable_conversion_cost + (total_fixed_cost / selected_qty if selected_qty > 0 else 0)

    # --- RESULTS SECTION (Top) ---
    with results_container:
        st.subheader("Quotation Summary")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric(f"Weight ({sheets_per_box} PC)", f"{final_weight_kg:.3f} kg")
        m2.metric("Total Cost", f"₹{total_cost:.2f}")
        m3.metric("Selling Price", f"₹{selling_price:.2f}")
        m4.metric("Profit", f"₹{profit:.2f}")
    
    # 8. Save Quotation
    st.divider()
    if st.button("Save Quotation"):
        if not selected_party:
            st.error("Please select a Party to save the quotation.")
        else:
            try:
                from models import Quotation, QuotationItem
                from datetime import datetime
                
                # --- GENERATE CUSTOM QUOTATION NUMBER ---
                # 1. Get Initials
                # e.g. "Jyoti Electrical Industries" -> "JEI"
                words = selected_party.name.strip().split()
                initials = "".join([w[0].upper() for w in words if w])[:4] # Max 4 chars
                if not initials:
                    initials = "GEN" # Fallback
                
                # 2. Find last number for these initials
                last_q = db.query(Quotation).filter(Quotation.quotation_number.like(f"{initials}-%"))\
                           .order_by(Quotation.id.desc()).first()
                
                if last_q:
                    # Extract number part
                    try:
                        last_num = int(last_q.quotation_number.split("-")[-1])
                        new_num = last_num + 1
                    except:
                        new_num = 1
                else:
                    new_num = 1
                
                q_number = f"{initials}-{new_num:04d}"
                
                # Create Header
                new_quotation = Quotation(
                    quotation_number=q_number,
                    party_id=selected_party.id,
                    status="Draft",
                    total_amount=selling_price * selected_qty
                )
                db.add(new_quotation)
                db.flush() # Get ID
                
                # Create Item
                new_item = QuotationItem(
                    quotation_id=new_quotation.id,
                    box_type="RSC", # Default for now
                    length=length,
                    width=width,
                    height=height,
                    unit=unit_selection,
                    ply=ply,
                    quantity=selected_qty,
                    layer_details=current_layer_details, # Save Specs
                    sheet_weight=final_weight_kg,
                    box_weight=final_weight_kg,
                    material_cost=material_cost,
                    conversion_cost=conversion_cost,
                    cost_per_box=total_cost,
                    margin_percent=margin_input,
                    selling_price=selling_price
                )
                db.add(new_item)
                db.commit()
                
                st.session_state['last_saved_q_id'] = new_quotation.id
                st.success(f"Quotation {new_quotation.quotation_number} saved successfully!")
                
            except Exception as e:
                st.error(f"Error saving quotation: {e}")

    # --- Post-Save Actions (PDF & WhatsApp) ---
    if 'last_saved_q_id' in st.session_state:
        saved_q_id = st.session_state['last_saved_q_id']
        # Retrieve fresh from DB to prevent detachment issues
        from models import Quotation
        saved_q = db.query(Quotation).filter(Quotation.id == saved_q_id).first()
        
        if saved_q:
            st.markdown("### Export & Share")
            c1, c2, c3 = st.columns([1, 1, 2])
            
            # PDF Generation
            pdf_bytes = generate_quotation_pdf(saved_q, saved_q.items, saved_q.party)
            
            # Use 'E:/0 Prexa/BOX Costing/PDF' as requested. Using forward slashes for python compatibility.
            # Ideally verify OS but user environment is known.
            save_path = f"E:\\0 Prexa\\BOX Costing\\PDF\\{saved_q.quotation_number}.pdf"
            try:
                with open(save_path, "wb") as f:
                    f.write(pdf_bytes.getvalue())
                st.success(f"PDF automatically saved to: {save_path}")
            except Exception as e:
                st.warning(f"Could not auto-save to E: drive: {e}")
            
            c1.download_button(
                label="📄 Download PDF",
                data=pdf_bytes,
                file_name=f"{saved_q.quotation_number}.pdf",
                mime="application/pdf"
            )
            
            # WhatsApp Link
            wa_link = generate_whatsapp_link(saved_q, saved_q.party, saved_q.total_amount)
            if wa_link:
                c2.markdown(f'<a href="{wa_link}" target="_blank" style="text-decoration:none;"><button style="background-color:#25D366; color:white; border:none; padding:0.5rem 1rem; border-radius:4px; font-weight:bold;">Example: Share on WhatsApp</button></a>', unsafe_allow_html=True)
                c2.caption("Note: Attach PDF manually.")
                
                # Helper to open folder
                if st.button("📂 Open PDF Folder"):
                    import os
                    folder_path = r"E:\0 Prexa\BOX Costing\PDF"
                    try:
                        os.startfile(folder_path)
                        st.toast("Folder Opened!", icon="📂")
                    except Exception as e:
                        st.error(f"Could not open folder: {e}")
            else:
                c2.info("No mobile number for party.")
                
            if c3.button("Start New Quotation"):
                del st.session_state['last_saved_q_id']
                st.rerun()

    db.close()
