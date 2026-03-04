import streamlit as st
import pandas as pd
import numpy as np
import base64
import os
import streamlit.components.v1 as components
import math
import altair as alt

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="HIA Intelligence Suite", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- BACKGROUND HELPER ---
def get_base64(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return ""

# --- NAVIGATION LOGIC ---
if 'page' not in st.session_state:
    st.session_state.page = 'home'

def change_page(new_page):
    st.session_state.page = new_page
    st.rerun()

# --- DYNAMIC STYLING ---
if st.session_state.page in ['bdwm', 'current_deal']:
    container_width = "95%"
else:
    container_width = "1150px"

st.markdown(f"""
    <style>
    footer {{ visibility: hidden; }}
    button[data-testid="stSidebarCollapseButton"] {{
        color: black !important;
        font-weight: bold !important;
    }}
    button[data-testid="stSidebarCollapseButton"] svg {{
        fill: black !important;
        stroke: black !important;
        stroke-width: 2px !important;
    }}
    .block-container {{ max-width: {container_width}; padding-top: 1.5rem; padding-bottom: 1rem; }}
    .excel-header {{ 
        background-color: #1e293b; color: white; font-weight: bold; 
        padding: 8px 12px; border: 1px solid #94a3b8; margin-top: 15px;
        font-size: 0.95rem; border-radius: 4px 4px 0 0;
    }}
    .stTable {{ border: 1px solid #94a3b8; background-color: white; margin-top: -1px; }}
    .quest-header {{
        background: linear-gradient(90deg, #3b82f6 0%, #1e3a8a 100%);
        color: white; padding: 10px 15px; border-radius: 8px;
        margin: 20px 0 10px 0; font-weight: bold; font-size: 1.2rem;
        display: flex; align-items: center;
    }}
    .quest-step {{ font-weight: bold; color: #3b82f6; margin-right: 10px; }}
    .casual-header {{
        background: linear-gradient(90deg, #8b5cf6 0%, #4c1d95 100%);
        color: white; padding: 10px 15px; border-radius: 8px;
        margin: 20px 0 10px 0; font-weight: bold; font-size: 1.2rem;
        display: flex; align-items: center;
    }}
    .expert-header {{
        background: linear-gradient(90deg, #10b981 0%, #064e3b 100%);
        color: white; padding: 10px 15px; border-radius: 8px;
        margin: 20px 0 10px 0; font-weight: bold; font-size: 1.2rem;
        display: flex; align-items: center;
    }}
    .pro-tip {{ background-color: #f0fdf4; border-left: 5px solid #22c55e; padding: 10px; margin: 10px 0; border-radius: 4px; color: #166534; }}
    .checklist-header {{ font-weight: bold; color: #1e3a8a; margin-top: 10px; text-decoration: underline; }}
    @media print {{
        @page {{ size: portrait; margin: 0.25in; }}
        /* Zoom slightly more out to ensure the 4 tables fit on Page 1 */
        .stApp {{ zoom: 60%; background-color: white !important; background-image: none !important; }}
        [data-testid="stSidebar"] {{ display: none !important; }}
        .main .block-container {{ max-width: 100% !important; padding: 0 !important; margin: 0 !important; }}
        div[data-testid="stTable"], .stTable {{ 
            display: block !important; 
            overflow: visible !important; 
            visibility: visible !important;
            page-break-inside: avoid !important; 
        }}
        .excel-header, .stMetric {{ page-break-inside: avoid !important; }}
        button, header, footer, .stActionButton {{ display: none !important; }}
        
        /* Forces the summary to always start on a new page */
        .print-only-summary {{ 
            display: block !important; 
            visibility: visible !important; 
            page-break-before: always !important;
        }}
        .page-break {{ display: block; page-break-before: always; }}
    }}
    @media screen {{ .print-only-summary {{ display: none !important; }} }}
    </style>
""", unsafe_allow_html=True)

# --- GLOBAL CALCULATORS ---
@st.cache_data
def calculate_canadian_ltt(price, is_first_buyer, province, city, loan_amt=0):
    tax = 0
    if province == "Ontario":
        if price > 2000000: tax += (price - 2000000) * 0.025 + 36475
        elif price > 400000: tax += (price - 400000) * 0.02 + 4475
        elif price > 250000: tax += (price - 250000) * 0.015 + 2225
        elif price > 55000: tax += (price - 55000) * 0.01 + 275
        else: tax += price * 0.005
        if is_first_buyer: tax = max(0, tax - 4000)
        if city == "Toronto":
            m_tax = 0
            temp_p = price
            m_tiers = [(20000000, 0.075), (10000000, 0.065), (5000000, 0.055), (4000000, 0.045), (3000000, 0.035), (2000000, 0.025), (400000, 0.02), (250000, 0.015), (55000, 0.01), (0, 0.005)]
            for thresh, rate in m_tiers:
                if temp_p > thresh:
                    m_tax += (temp_p - thresh) * rate
                    temp_p = thresh
            if is_first_buyer: m_tax = max(0, m_tax - 4475)
            tax += m_tax + 86.78
    elif province == "British Columbia":
        if price > 3000000: tax = (price - 3000000) * 0.05 + (1000000 * 0.03) + (1800000 * 0.02) + 2000
        elif price > 2000000: tax = (price - 2000000) * 0.03 + (1800000 * 0.02) + 2000
        elif price > 200000: tax = (price - 200000) * 0.02 + 2000
        else: tax = price * 0.01
    elif province == "Alberta":
        transfer_fee = 50 + (math.ceil(price / 5000) * 5)
        mortgage_fee = 50 + (math.ceil(loan_amt / 5000) * 5)
        tax = transfer_fee + mortgage_fee
    elif province == "Quebec":
        if city == "Montreal":
            if price > 3113000: tax = (price - 3113000) * 0.04 + 75150
            elif price > 500000: tax = (price - 500000) * 0.02 + 6395
            else: tax = price * 0.01
        else:
            if price > 254400: tax = (price - 254400) * 0.015 + 2800
            else: tax = price * 0.01
    elif province == "Nova Scotia":
        tax = price * (0.015 if city == "Halifax" else 0.01)
    elif province in ["New Brunswick", "PEI"]:
        tax = price * 0.01
    elif province == "Manitoba":
        if price > 200000: tax = (price - 200000) * 0.02 + 1650
        else: tax = price * 0.01
    elif province == "Saskatchewan":
        tax = price * 0.003
    elif province == "Newfoundland and Labrador":
        tax = 100 + (max(0, price - 500) / 100 * 0.40)
    elif province == "Northwest Territories":
        tax = max(100, (price / 1000) * 1.5) + max(80, (loan_amt / 1000) * 1.0)
    elif province == "Yukon":
        if price <= 100000: tax = 50
        elif price <= 500000: tax = 150
        elif price <= 1000000: tax = 250
        else: tax = 500
        tax += 50
    elif province == "Nunavut":
        tax = max(60, (price / 1000) * 1.5) + 40
    return tax

def calc_stats(loan_amt, amort, h_rate, heloc_used, tax_bracket, claim_cca, p_price, legal_closing, ltt_val, renos, prop_tax, ins, equip_rent, condo_fees, utilities, other_mo, rate, rent):
    i = rate / 12
    pi = loan_amt * (i * (1 + i)**(amort*12)) / ((1 + i)**(amort*12) - 1)
    int_mo = (loan_amt * rate) / 12
    op_ex_mo = prop_tax + ins + equip_rent + condo_fees + utilities + other_mo
    heloc_mo = (heloc_used * h_rate) / 12
    ann_cash = (rent - (pi + op_ex_mo + heloc_mo)) * 12
    ann_prin = (pi - int_mo) * 12
    profit_pre_cca = (rent * 12) - (int_mo * 12 + op_ex_mo * 12 + heloc_mo * 12)
    if claim_cca:
        building_base = (p_price + legal_closing + ltt_val + renos) * 0.70
        cca_max = (building_base * 0.04) * 0.5
        cca_claimed = max(0, min(profit_pre_cca, cca_max))
    else:
        cca_claimed = 0
    taxable_income = max(0, profit_pre_cca - cca_claimed)
    at_cash_only = ann_cash - (taxable_income * tax_bracket)
    at_total = at_cash_only + ann_prin
    bt_total = ann_cash + ann_prin
    return ann_cash, ann_prin, at_total, bt_total, at_cash_only

# --- PAGE ROUTING ---

if st.session_state.page == 'home':
    # REINSTATED LARGE BUTTON HOME PAGE DESIGN
    home_style = """
    <style>
        div.stButton > button {
            height: 140px !important;
            border-radius: 15px !important;
            border: 2px solid #1e3a8a !important;
            background-color: rgba(255, 255, 255, 0.9) !important;
            transition: all 0.3s ease;
        }
        div.stButton > button:hover {
            border-color: #3b82f6 !important;
            background-color: #ffffff !important;
            transform: scale(1.02);
        }
        div.stButton > button p {
            font-size: 22px !important;
            font-weight: 800 !important;
            color: #1e3a8a !important;
            line-height: 1.1 !important;
            text-align: center !important;
            white-space: normal !important;
        }
    </style>
    """
    
    if os.path.exists("background.png"):
        bin_str = get_base64("background.png")
        st.markdown(f"""<style>.stApp {{ background-image: url("data:image/png;base64,{bin_str}"); background-size: cover; background-position: center; }}</style>""", unsafe_allow_html=True)
    
    st.markdown(home_style, unsafe_allow_html=True)
    st.markdown("<div style='margin-top: 120px;'></div>", unsafe_allow_html=True)

    # ROW 1: ANALYSIS TOOLS
    r1c1, r1c2, r1c3 = st.columns(3)
    if r1c1.button("📊 MARKET\nINTELLIGENCE", use_container_width=True): change_page('bdwm')
    if r1c2.button("🏠 NEW RENTAL\nANALYSIS", use_container_width=True): change_page('rental')
    # CHANGED NAME TO CURRENT RENTAL ANALYSIS BELOW
    if r1c3.button("📈 CURRENT RENTAL\nANALYSIS", use_container_width=True): change_page('current_deal')

    st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)

    # ROW 2: WALKTHROUGHS
    r2c1, r2c2, r2c3 = st.columns(3)
    if r2c1.button("🎮 NOOB\nWALKTHROUGH", use_container_width=True): change_page('noob')
    if r2c2.button("⚔️ CASUAL\nWALKTHROUGH", use_container_width=True): change_page('casual')
    if r2c3.button("👑 EXPERT\nWALKTHROUGH", use_container_width=True): change_page('expert')

elif st.session_state.page == 'bdwm':
    if st.button("← Back"): change_page('home')
    csv_file = "BDWM Analysis Summary.csv"
    if os.path.exists(csv_file):
        try:
            df = pd.read_csv(csv_file)
            df['PPSF'] = df['Price'] / df['SqFt']
            mean_ppsf = df['PPSF'].mean()
            std_ppsf = df['PPSF'].std()
            df['Z-Score'] = (df['PPSF'] - mean_ppsf) / std_ppsf
            m1, m2 = st.columns([1, 2])
            with m1:
                st.markdown("<div class='excel-header'>MARKET OVERVIEW</div>", unsafe_allow_html=True)
                st.metric("Avg Price / SqFt", f"${mean_ppsf:,.2f}")
                st.metric("Total Listings Analyzed", len(df))
                st.write("**Top Value Opportunities**")
                st.dataframe(df[['Address', 'Price', 'Z-Score']].sort_values('Z-Score').head(5), hide_index=True)
            with m2:
                st.markdown("<div class='excel-header'>VALUE SCATTER MAP (Z-SCORE)</div>", unsafe_allow_html=True)
                chart = alt.Chart(df).mark_circle(size=100).encode(
                    x=alt.X('SqFt', title='Square Footage'),
                    y=alt.Y('Price', title='Listing Price'),
                    color=alt.Color('Z-Score', scale=alt.Scale(scheme='redblue', reverse=True)),
                    tooltip=['Address', 'Price', 'SqFt', 'PPSF']
                ).interactive().properties(height=400)
                st.altair_chart(chart, use_container_width=True)
        except:
            st.warning("Found CSV but columns 'Price' or 'SqFt' might be missing.")
    
    pdf_path = "analysis summary.pdf"
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}#toolbar=0" style="width:100%; height:1200px;" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)

elif st.session_state.page == 'rental':
    if st.button("← Back"): change_page('home')
    
    with st.sidebar:
        st.subheader("PROPERTY DETAILS")
        prov = st.selectbox("Province/Territory", ["Ontario", "Quebec", "British Columbia", "Alberta", "Manitoba", "Saskatchewan", "Nova Scotia", "New Brunswick", "PEI", "Newfoundland", "Yukon", "Northwest Territories", "Nunavut"])
        city_options = ["Other"]
        if prov == "Ontario": city_options = ["Outside Toronto", "Toronto"]
        elif prov == "Quebec": city_options = ["Outside Montreal", "Montreal"]
        elif prov == "Nova Scotia": city_options = ["Outside Halifax", "Halifax"]
        city = st.selectbox("City", city_options)
        is_first_buyer = st.radio("First Home Buyer?", ["No", "Yes"], horizontal=True) == "Yes"
        p_price = st.number_input("Purchase price", value=280000)
        down_pct = st.number_input("Downpayment (%)", value=5.0) / 100
        m_rate = st.number_input("Mortgage rate (%)", value=4.98) / 100
        h_rate = st.number_input("HELOC rate (%)", value=6.0) / 100
        amort = st.number_input("Amortization (Yrs)", value=25)
        tax_bracket = st.number_input("Marginal Tax (%)", value=44.97) / 100
        claim_cca = st.radio("Claim CCA Deduction?", ["No", "Yes"], horizontal=True) == "Yes"
        st.subheader("REVENUE")
        target_rent = st.number_input("Current Rental Rate", value=1800)
        st.subheader("UP FRONT COSTS")
        renos = st.number_input("Renovations (Capitalized)", value=15000)
        legal_closing = st.number_input("Legal/Closing", value=3500)
        heloc_used = st.number_input("HELOC Used", value=15000)
        other_upfront = st.number_input("Other Upfront", value=0)
        st.subheader("MONTHLY EXPENSES")
        prop_tax = st.number_input("Property tax", value=125)
        ins = st.number_input("Insurance", value=65)
        equip_rent = st.number_input("Equip. rental", value=56)
        condo_fees = st.number_input("Condo Fees", value=0)
        utilities = st.number_input("Utilities", value=0)
        other_mo = st.number_input("Other Monthly", value=0)

    if down_pct >= 0.20: cmhc_p = 0.0
    else: cmhc_p = 0.04 if down_pct <= 0.05 else 0.031 if down_pct <= 0.1 else 0.028 if down_pct <= 0.15 else 0.024
    temp_loan = (p_price * (1 - down_pct)) * (1 + cmhc_p)
    ltt_val = calculate_canadian_ltt(p_price, is_first_buyer, prov, city, temp_loan)
    loan_amt = temp_loan
    down_amt = p_price * down_pct
    invested_cap = (down_amt + legal_closing + ltt_val + renos + other_upfront) - heloc_used
    calc_params = [loan_amt, amort, h_rate, heloc_used, tax_bracket, claim_cca, p_price, legal_closing, ltt_val, renos, prop_tax, ins, equip_rent, condo_fees, utilities, other_mo]

    st.title(f"🏠 New Rental Analysis: {city if city != 'Other' else prov}")
    st.markdown("<div class='excel-header'>CAPITAL COMMITMENT</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.write(f"**Downpayment:** ${down_amt:,.2f}")
        st.write(f"**Legal/Closing:** ${legal_closing:,.2f}")
    with c2:
        st.write(f"**Registration Fees / LTT:** ${ltt_val:,.2f}")
        st.write(f"**Renovations:** ${renos:,.2f}")
    with c3:
        st.write(f"**Other:** ${other_upfront:,.2f}")
        st.write(f"**HELOC Used:** :red[- ${heloc_used:,.2f}]")
    st.success(f"### **Net Cash Invested: ${invested_cap:,.2f}**")

    st.markdown("<div class='excel-header'>NET CASH RETURN (AFTER-TAX POCKET MONEY)</div>", unsafe_allow_html=True)
    rent_steps = [target_rent - 200, target_rent - 100, target_rent, target_rent + 100, target_rent + 200]
    at_net_rows = []
    for r in rent_steps:
        _, _, _, _, pocket_money = calc_stats(*calc_params, m_rate, r)
        mo_at_cash = pocket_money / 12
        at_net_rows.append([r, mo_at_cash, mo_at_cash * 12])
    df_at_net = pd.DataFrame(at_net_rows, columns=["Rental Rate", "Monthly Net (AT)", "Annual Net (AT)"])
    st.table(df_at_net.style.format("${:,.2f}").apply(lambda x: ['background-color: yellow' if x.name == 2 else '' for _ in x], axis=1))

    st.markdown("<div class='excel-header'>MONTHLY COST</div>", unsafe_allow_html=True)
    mort_pi = loan_amt * ((m_rate/12) * (1 + (m_rate/12))**(amort*12)) / ((1 + (m_rate/12))**(amort*12) - 1)
    total_mo_ex = mort_pi + prop_tax + ins + equip_rent + condo_fees + utilities + other_mo + ((heloc_used * h_rate) / 12)
    cost_rows = pd.DataFrame([
        ["Mortgage (P&I / Interest Only)", mort_pi, (loan_amt * m_rate) / 12],
        ["Property Tax", prop_tax, prop_tax],
        ["Insurance", ins, ins],
        ["Equip/Condo/Util/Other", equip_rent+condo_fees+utilities+other_mo, equip_rent+condo_fees+utilities+other_mo],
        ["HELOC Interest", (heloc_used * h_rate)/12, (heloc_used * h_rate)/12],
        ["TOTAL", total_mo_ex, ((loan_amt * m_rate)/12) + prop_tax + ins + equip_rent + condo_fees + utilities + other_mo + ((heloc_used * h_rate)/12)]
    ], columns=["Item", "Real Cost", "Deductible Cost"])
    st.table(cost_rows.style.format({"Real Cost": "${:,.2f}", "Deductible Cost": "${:,.2f}"}).apply(
        lambda x: ['border-top: 1px solid black; border-bottom: 3px double black; font-weight: bold' if x.name == 5 else '' for _ in x], axis=1
    ))

    st.markdown("<div class='excel-header'>RETURN METRIC MATRIX - INTEREST RATE SENSITIVITY</div>", unsafe_allow_html=True)
    shifts = [x / 1000 for x in range(-20, 25, 5)]
    labels = ["Rate change", "Mortgage rate", "Net cash return ($)", "Repayment of mortgage ($)", "After tax total ($)", "Before tax total ($)", "Net cash return (%)", "Repayment of mortgage (%)", "After tax total (%)", "Before tax total (%)", "Repayment period (years)"]
    matrix_df = pd.DataFrame({"Metric": labels})
    for s in shifts:
        cash, prin, at, bt, _ = calc_stats(*calc_params, m_rate + s, target_rent)
        repay_val = "99.00+" if bt <= 0 else ("0.00 (Infinite)" if invested_cap <= 0 else f"{invested_cap/bt:.2f}")
        if invested_cap <= 0: cash_p, prin_p, at_p, bt_p = "∞", "∞", "∞", "∞"
        else:
            cash_p = f"{(cash/invested_cap)*100:.2f}%"; prin_p = f"{(prin/invested_cap)*100:.2f}%"; at_p = f"{(at/invested_cap)*100:.2f}%"; bt_p = f"{(bt/invested_cap)*100:.2f}%"
        matrix_df[f"{s*100:+.1f}%"] = [f"{s*100:+.1f}%", f"{(m_rate+s)*100:.2f}%", f"${cash:,.0f}", f"${prin:,.0f}", f"${at:,.0f}", f"${bt:,.0f}", cash_p, prin_p, at_p, bt_p, repay_val]
    st.table(matrix_df.style.apply(lambda row: ['background-color: yellow;' if row.name in [4, 5, 8, 9] else '' for _ in row], axis=1))

    # PRINT ONLY SUMMARY - PAGE 2 START
    st.markdown("<div class='print-only-summary'><div class='excel-header'>ANALYSIS INPUT SUMMARY</div>", unsafe_allow_html=True)
    summary_df = pd.DataFrame({
        "Variable": ["Province", "City", "Purchase Price", "Downpayment %", "Mortgage Rate", "Target Rent", "Property Tax", "Renovations"],
        "Value": [prov, city, f"${p_price:,.0f}", f"{down_pct*100:.1f}%", f"{m_rate*100:.2f}%", f"${target_rent:,.0f}", f"${prop_tax:,.0f}", f"${renos:,.0f}"]
    })
    st.table(summary_df)
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.page == 'current_deal':
    if st.button("← Back"): change_page('home')
    
    with st.sidebar:
        st.subheader("LOAN BALANCE DETAILS")
        p_price = st.number_input("Purchase price", value=330000)
        down_pct = st.number_input("Downpayment (%)", value=20.0) / 100
        m_rate = st.number_input("Mortgage rate (%)", value=4.5) / 100
        amort = st.number_input("Amortization (Yrs)", value=25)
        heloc_bal = st.number_input("HELOC balance", value=0)
        h_rate = st.number_input("HELOC rate (%)", value=0.0) / 100
        tax_bracket = st.number_input("Marginal Tax (%)", value=29.65) / 100
        
        st.subheader("MONTHLY COST")
        prop_tax = st.number_input("Property tax", value=125)
        ins = st.number_input("Insurance", value=65)
        equip_rent = st.number_input("Equip. rental", value=56)
        condo_fees = st.number_input("Condo Fees", value=0)
        utilities = st.number_input("Utilities", value=0)
        other_mo = st.number_input("Other Monthly", value=0)
        depreciation = st.number_input("Depreciation (Non-Cash)", value=1100)

        st.subheader("CAPITAL COMMITMENT")
        legal_closing = st.number_input("Legal/Closing", value=3500)
        ltt_val = st.number_input("Land Transfer Tax", value=3425)
        renos = st.number_input("Renovation", value=15000)
        other_cap = st.number_input("Other Capital", value=0)
        
        st.subheader("REVENUE")
        target_rent = st.number_input("Select Base Rent", value=2200)

    # Derived Logic
    loan_amt = p_price * (1 - down_pct)
    down_amt = p_price * down_pct
    invested_cap = down_amt + legal_closing + ltt_val + renos + other_cap - heloc_bal

    st.title("📈 Current Deal Analysis: Property Performance")
    
    # PAGE 1 START
    st.markdown("<div class='excel-header'>CAPITAL COMMITMENT</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.write(f"**Downpayment:** ${down_amt:,.2f}")
        st.write(f"**Legal + disbursement:** ${legal_closing:,.2f}")
    with c2:
        st.write(f"**Land transfer tax:** ${ltt_val:,.2f}")
        st.write(f"**Renovation:** ${renos:,.2f}")
    with c3:
        st.write(f"**Other:** ${other_cap:,.2f}")
        st.write(f"**HELOC Funding:** :red[- ${heloc_bal:,.2f}]")
    st.success(f"### **Net Cash Invested: ${invested_cap:,.2f}**")

    st.markdown("<div class='excel-header'>NET CASH RETURN</div>", unsafe_allow_html=True)
    rent_steps = [target_rent - 200, target_rent - 100, target_rent, target_rent + 100, target_rent + 200]
    rent_rows = []
    mort_pi = loan_amt * ((m_rate/12) * (1 + (m_rate/12))**(amort*12)) / ((1 + (m_rate/12))**(amort*12) - 1)
    total_real_mo = mort_pi + prop_tax + ins + equip_rent + condo_fees + utilities + other_mo + ((heloc_bal * h_rate) / 12)
    
    for r in rent_steps:
        mo_return = r - total_real_mo
        rent_rows.append([r, mo_return, mo_return * 12])
    
    df_rent = pd.DataFrame(rent_rows, columns=["Rental Rate", "Monthly net return", "Annual net return"])
    st.table(df_rent.style.format("${:,.2f}").apply(lambda x: ['background-color: yellow' if x.name == 2 else '' for _ in x], axis=1))

    st.markdown("<div class='excel-header'>MONTHLY COST</div>", unsafe_allow_html=True)
    int_mo = (loan_amt * m_rate) / 12
    deductible_mo = int_mo + prop_tax + ins + equip_rent + condo_fees + utilities + other_mo + ((heloc_bal * h_rate) / 12)
    
    cost_rows = pd.DataFrame([
        ["Mortgage (p/i)", mort_pi, int_mo],
        ["Property tax", prop_tax, prop_tax],
        ["Insurance", ins, ins],
        ["Equipment rental", equip_rent, equip_rent],
        ["Condo fees", condo_fees, condo_fees],
        ["Utility", utilities, utilities],
        ["HELOC interest cost", (heloc_bal * h_rate)/12, (heloc_bal * h_rate)/12],
        ["Other", other_mo, other_mo],
        ["Depreciation (4% of cb)", 0, depreciation],
        ["TOTAL", total_real_mo, deductible_mo + depreciation]
    ], columns=["Item", "Real Cost", "Deductible Cost"])
    st.table(cost_rows.style.format({"Real Cost": "${:,.2f}", "Deductible Cost": "${:,.2f}"}).apply(
        lambda x: ['font-weight: bold; border-top: 2px solid black' if x.name == 9 else '' for _ in x], axis=1
    ))

    st.markdown("<div class='excel-header'>RETURN METRIC MATRIX - INTEREST RATE SENSITIVITY</div>", unsafe_allow_html=True)
    shifts = [x / 1000 for x in range(-20, 25, 5)] 
    labels = ["Rate change", "Mortgage rate", "HELOC rate", "Net cash return ($)", "Repayment of mortgage ($)", "After tax total ($)", "Before tax total ($)", "Net cash return (%)", "After tax total (%)", "Before tax total (%)", "Repayment period (years)"]
    matrix_df = pd.DataFrame({"Metric": labels})
    
    for s in shifts:
        current_m_rate = m_rate + s
        i_s = current_m_rate / 12
        pi_s = loan_amt * (i_s * (1 + i_s)**(amort*12)) / ((1 + i_s)**(amort*12) - 1)
        int_s = (loan_amt * current_m_rate) / 12
        
        ann_cash = (target_rent - (pi_s + prop_tax + ins + equip_rent + condo_fees + utilities + other_mo + ((heloc_bal * (h_rate+s))/12))) * 12
        ann_prin = (pi_s - int_s) * 12
        taxable_profit = (target_rent * 12) - ((int_s * 12) + (prop_tax*12) + (ins*12) + (equip_rent*12) + (condo_fees*12) + (utilities*12) + (other_mo*12) + (heloc_bal * (h_rate+s)) + depreciation)
        tax_bill = max(0, taxable_profit * tax_bracket)
        at_total = ann_cash + ann_prin - tax_bill
        at_total = ann_cash + ann_prin - tax_bill
        bt_total = ann_cash + ann_prin
        
        if invested_cap <= 0:
            cash_p, at_p, bt_p = "∞", "∞", "∞"
        else:
            cash_p = f"{(ann_cash/invested_cap)*100:.2f}%"
            at_p = f"{(at_total/invested_cap)*100:.2f}%"
            bt_p = f"{(bt_total/invested_cap)*100:.2f}%"

        repay_period = f"{invested_cap/bt_total:.2f}" if bt_total > 0 else "99+"
        
        matrix_df[f"{s*100:+.1f}%"] = [
            f"{s*100:+.1f}%", f"{current_m_rate*100:.2f}%", f"{(h_rate+s)*100:.2f}%",
            f"${ann_cash:,.0f}", f"${ann_prin:,.0f}", f"${at_total:,.0f}", f"${bt_total:,.0f}",
            cash_p, at_p, bt_p,
            repay_period
        ]
    st.table(matrix_df.style.apply(lambda row: ['background-color: #fef9c3;' if row.name in [5, 6, 8, 9] else '' for _ in row], axis=1))

    # PRINT ONLY SUMMARY - PAGE 2 START
    st.markdown("<div class='print-only-summary'><div class='excel-header'>ANALYSIS INPUT SUMMARY</div>", unsafe_allow_html=True)
    summary_df = pd.DataFrame({
        "Variable": ["Purchase Price", "Downpayment %", "Mortgage Rate", "Target Rent", "Property Tax", "HELOC Balance", "Renovation"],
        "Value": [f"${p_price:,.0f}", f"{down_pct*100:.1f}%", f"{m_rate*100:.2f}%", f"${target_rent:,.0f}", f"${prop_tax:,.0f}", f"${heloc_bal:,.0f}", f"${renos:,.0f}"]
    })
    st.table(summary_df)
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.page == 'noob':
    if st.button("← Back to Hub"): change_page('home')
    st.title("🎮 Financial Quest Log: Mastering the Game")
    st.progress(0.15, text="Main Quest Progress: 15%")
    st.markdown("""
    Welcome to the **Financial MMO**. Most people play without a tutorial. You're smarter. 
    Wealth planning is a long-term RPG where you're building a character that **cannot fail the late game**.
    It doesn't matter when you start; it matters that you follow the meta.
    """)

    st.markdown('<div class="quest-header"><span class="quest-step">QUEST 1:</span> Building Your Base Stats</div>', unsafe_allow_html=True)
    with st.expander("Expand for Class Details & Stat Buffs"):
        st.write("""
        The first stage of any wealth plan is optimizing your **Active Income (Human Capital)**.
        - **Primary Stat:** High-Value Skills. A significant salary bump is the most effective "gold farm" early in your journey.
        - **Buffs:** Invest gold in yourself first. Certifications, specialized training, and networking are multipliers for your earning potential.
        - **Goal:** Increase your "Base DPS" (Active Income) to fund the more complex gear in later quests.
        """)
        st.markdown('<div class="pro-tip">💡 <b>PRO-TIP:</b> Treat your career as your primary business. Every $1,000 spent on high-ROI training can yield $10,000+ in annual salary gains.</div>', unsafe_allow_html=True)
        st.markdown('<div class="checklist-header">Quest Requirements:</div>', unsafe_allow_html=True)
        st.write("* [ ] Identify top 3 skills in your industry with the highest pay gap.\n* [ ] Set a 12-month target for salary growth or side-income generation.")

    st.markdown('<div class="quest-header"><span class="quest-step">QUEST 2:</span> Stability and Defense Zone</div>', unsafe_allow_html=True)
    with st.expander("Expand for Survival Guide"):
        st.write("""
        You can't raid high-level dungeons (Large Investments) with 1 HP. Build your defensive wall:
        - **Positive Cash Flow:** Income must exceed Expenses. If you leak gold every month, no investment can save you.
        - **Anti-Curse Shield:** Purge high-interest debt. Interest payments are a "leech" debuff that drains your progress.
        - **Emergency Potion:** Maintain a liquid reserve for 3-6 months. This prevents a "Game Over" when unexpected events hit.
        """)
        st.markdown('<div class="pro-tip">💡 <b>PRO-TIP:</b> Automated transfers are your best friend. Set your "defense" to auto-pilot so you never forget to pay your future self.</div>', unsafe_allow_html=True)
        st.markdown('<div class="checklist-header">Quest Requirements:</div>', unsafe_allow_html=True)
        st.write("* [ ] Eliminate all debt with >10% interest.\n* [ ] Fund an 'Emergency Potion' account with at least $5,000.")

    st.markdown('<div class="quest-header"><span class="quest-step">QUEST 3:</span> Equipment Slots (Tax Shelters)</div>', unsafe_allow_html=True)
    with st.expander("Expand for Equipment Specs"):
        st.write("""
        In the Canadian meta, accounts are your **Gear Slots**. They aren't the investment; they are the containers that determine your tax resistance.
        - **TFSA (Tax-Free Savings Account):** The legendary slot. Gains are never taxed. Perfect for long-term compounding growth.
        - **RRSP (Registered Retirement Savings Plan):** A tactical slot. Reduces your current taxable income, deferred until later levels.
        - **FHSA (First Home Savings Account):** The ultimate starter bonus for real estate. Tax-deductible contributions and tax-free withdrawals for a home purchase.
        """)
        st.markdown('<div class="pro-tip">💡 <b>PRO-TIP:</b> Maximize the FHSA if you plan to buy property. It combines the tax-deduction of an RRSP with the tax-free growth of a TFSA. It is essentially "God Tier" gear.</div>', unsafe_allow_html=True)
        st.markdown('<div class="checklist-header">Quest Requirements:</div>', unsafe_allow_html=True)
        st.write("* [ ] Open an FHSA if property ownership is a goal.\n* [ ] Audit current TFSA/RRSP contributions vs. annual limits.")

    st.markdown('<div class="quest-header"><span class="quest-step">QUEST 4:</span> The Time-Multiplier Buff</div>', unsafe_allow_html=True)
    with st.expander("Expand for Leveling Mechanics"):
        st.write("""
        Compounding is an **exponential XP multiplier**. 
        - **Start Now:** The earlier you begin, the less "grinding" you have to do later. Time does the heavy lifting for you.
        - **RNG Protection:** Consistency beats timing. Regular contributions protect you from market volatility (bad RNG).
        """)
        st.markdown('<div class="pro-tip">💡 <b>PRO-TIP:</b> The "Rule of 72" helps you estimate doubling time. Divide 72 by your expected return rate to see how fast your gold grows.</div>', unsafe_allow_html=True)
        st.markdown('<div class="checklist-header">Quest Requirements:</div>', unsafe_allow_html=True)
        st.write("* [ ] Set up a recurring investment (even if small) to trigger the 'Compounding' buff.\n* [ ] Review portfolio fees—low-cost ETFs are the most efficient gear for this quest.")

    st.markdown('<div class="quest-header" style="background: linear-gradient(90deg, #ef4444 0%, #7f1d1d 100%);">⚠️ NOOB TRAPS (AVOID AT ALL COSTS)</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.error("**Lifestyle Inflation:** Leveling up your overhead every time you level up your income. It keeps your net worth stuck at Level 1.")
        st.error("**The Comparison Lag:** Watching other players' highlight reels on social media. Play your own game at your own pace.")
    with c2:
        st.error("**Toxic Debt:** Financing a lifestyle you haven't farmed for yet. This is playing the game on 'Hard Mode' with no reward.")
        st.error("**Gold Decay:** Leaving your entire stash in a 0% interest account. Inflation is a 'Burn' effect that slowly erodes your purchasing power.")
    st.success("### 🏆 Final Objective: Financial Optionality")
    st.write("The goal of the game isn't just to hoard gold—it's to reach a level where you have the freedom to choose your own quests. Stay disciplined, optimize your gear, and play the long game.")

elif st.session_state.page == 'casual':
    if st.button("← Back to Hub"): change_page('home')
    st.title("⚔️ Casual Player Walkthrough: Mid-Game Strategies")
    st.markdown("<div class='excel-header'>📊 BUILD PERFORMANCE SCORECARDS</div>", unsafe_allow_html=True)
    s1, s2 = st.columns(2)
    with s1:
        st.subheader("🛡️ Tax Efficiency Scorecard")
        st.markdown("""
        | Efficiency Tier | Strategy Coverage Description |
        | :--- | :--- |
        | **S-Tier** | **Structural Shielding:** Advanced maneuvers that convert non-deductible expenses into tax advantages. |
        | **A-Tier** | **Optimized Shelters:** Utilizing specialized accounts and asset location to minimize leakage. |
        | **B-Tier** | **Standard Protection:** Using core registered accounts to protect growth from immediate taxation. |
        | **C-Tier** | **Unshielded:** Operating primarily in taxable accounts with no specific tax-reduction plan. |
        """)
    with s2:
        st.subheader("📈 Profit Efficiency Scorecard")
        st.markdown("""
        | Efficiency Tier | Wealth Velocity Description |
        | :--- | :--- |
        | **Hyper-Growth** | **High Velocity:** Strategies utilizing leverage or active business models to accelerate capital. |
        | **Market-Beater** | **Enhanced Growth:** Strategies aimed at reducing friction (fees) and maximizing market capture. |
        | **Stable-Build** | **Core Growth:** Diversified, low-cost approaches designed for long-term steady accumulation. |
        | **Inflation-Hedge**| **Capital Preservation:** Low-risk strategies focused on maintaining purchasing power. |
        """)

    st.markdown("""
    Below is a breakdown of 20 maneuvers. Each one is tagged with its **Scorecard Tier** so you know how it upgrades your build.
    """)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🛡️ Standard Gear (Simpler)")
        simpler = [
            ("TFSA Maxing", "**[B-Tier: Tax Efficiency]** Standard Protection. Tax-free growth and withdrawals. Prioritize this for long-term compounding growth."),
            ("RRSP Deduction", "**[B-Tier: Tax Efficiency]** Standard Protection. Tactical tax deferral to shift burden to lower-income years."),
            ("FHSA Starter", "**[A-Tier: Tax Efficiency]** Optimized Shelter. The ultimate real estate entry buff; tax-deductible in, tax-free out."),
            ("RESP (CESG Match)", "**[Stable-Build: Profit Efficiency]** Core Growth. Government-assisted education build via 20% grant matching."),
            ("RDSP (Disability)", "**[Market-Beater: Profit Efficiency]** Enhanced Growth. Specialized grants and bonds for eligible players."),
            ("Employer Match", "**[Hyper-Growth: Profit Efficiency]** High Velocity. Immediate ROI via workplace benefits; never leave gold on the table."),
            ("HBP (Home Buyers' Plan)", "**[B-Tier: Tax Efficiency]** Standard Protection. Utilizing RRSP capital to fund property entry without tax penalty."),
            ("LLP (Lifelong Learning)", "**[B-Tier: Tax Efficiency]** Standard Protection. Deploying RRSP funds tax-free for career-based stat upgrades."),
            ("House Hacking", "**[Market-Beater: Profit Efficiency]** Enhanced Growth. Reducing housing overhead by converting space into income."),
            ("Low-MER Indexing", "**[Stable-Build: Profit Efficiency]** Core Growth. Eliminating fee-based friction to ensure market performance.")
        ]
        for title, desc in simpler:
            with st.expander(f"**{title}**"): st.write(desc)
    with col2:
        st.markdown("### 🔥 Advanced Enchants (Complex)")
        complex_s = [
            ("The Smith Maneuver", "**[S-Tier: Tax Efficiency]** Structural Shielding. Converting personal debt interest into tax deductions."),
            ("Spousal Loan Strategy", "**[S-Tier: Tax Efficiency]** Structural Shielding. Income splitting between spouses at prescribed rates."),
            ("The BRRRR Method", "**[Hyper-Growth: Profit Efficiency]** High Velocity. Scaling real estate via forced appreciation and equity recycling."),
            ("Corporate Wealth Injection", "**[A-Tier: Tax Efficiency]** Optimized Shelter. Using small business tax rates to maximize investment capital."),
            ("Asset Location Optimization", "**[A-Tier: Tax Efficiency]** Optimized Shelter. Placing assets strategically to avoid foreign withholding taxes."),
            ("Dividend Tax Harvesting", "**[A-Tier: Tax Efficiency]** Optimized Shelter. Maximizing the Canadian Dividend Tax Credit in taxable accounts."),
            ("Principal Residence Flipping", "**[S-Tier: Tax Efficiency]** Structural Shielding. Utilizing the PRE to generate 100% tax-free capital gains."),
            ("Leveraged ETF Rotation", "**[Hyper-Growth: Profit Efficiency]** High Velocity. Using leverage to outpace standard index returns in bull cycles."),
            ("The FHSA-RRSP Double Dip", "**[A-Tier: Tax Efficiency]** Optimized Shelter. Pivoting real estate deductions into retirement shelters."),
            ("Capital Gain Harvesting", "**[A-Tier: Tax Efficiency]** Optimized Shelter. Realizing gains in low-income years to step-up cost basis.")
        ]
        for title, desc in complex_s:
            with st.expander(f"**{title}**"): st.write(desc)
    st.info("💡 **Casual Player Walkthrough Tip:** These strategies carry higher risk/complexity. Always consult with a CPA or Fee-Only advisor before executing high-level maneuvers.")

elif st.session_state.page == 'expert':
    if st.button("← Back to Hub"): change_page('home')
    st.title("👑 Expert Player: Structural Arbitrage & Wealth Preservation")
    st.markdown("""
    At this level, "picking stocks" is irrelevant. You are now competing on **Structural Advantage**. 
    The goal is to move wealth into silos where the government has no "share" of the growth, utilizing complex legal and corporate frameworks.
    """)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="expert-header">🛡️ Infrastructure & Tax Arbitrage</div>', unsafe_allow_html=True)
        infra = [
            ("The 3-Tier Corporate Purge", "**Strategy:** Cleaning 'tainted' active business assets into a HoldCo to maintain LCGE eligibility. Decouples operations from passive investments."),
            ("Prescribed Rate Spousal Trusts", "**Strategy:** Locking in low interest rates via formal loans to shift high-yield income from 54% brackets to lower spouse brackets perpetually."),
            ("The Capital Class Swap", "**Strategy:** Utilizing Corporate Class investment funds to convert taxable interest/dividends into deferred capital gains within non-registered environments."),
            ("Individual Pension Plans (IPP)", "**Strategy:** A 'Super-RRSP' for business owners. Allows for significantly higher contribution limits and corporate tax deductions for management fees."),
            ("The Pipeline Maneuver", "**Strategy:** Post-mortem tax planning to avoid double taxation on corporate shares upon death, extracting cash at capital gains rates vs. dividend rates."),
            ("Estate Freezing & Refreezing", "**Strategy:** Capping current tax liability at today's value and passing future growth to the next generation via a Family Trust."),
            ("Passive Income Grind-Down Mitigation", "**Strategy:** Managing the $50k passive income threshold in a Corp to prevent the loss of the Small Business Deduction (SBD)."),
            ("Health Welfare Trusts (HWT/PHSP)", "**Strategy:** Converting personal family medical expenses into 100% tax-deductible business expenses for the corporation."),
            ("Inter-Vivos Asset Transfers", "**Strategy:** Utilizing 'Living Trusts' to manage asset distribution outside of probate, ensuring privacy and immediate control for heirs."),
            ("Capital Dividend Account (CDA) Flushing", "**Strategy:** Strategically paying out tax-free dividends from the non-taxable portion of corporate capital gains to clear the CDA.")
        ]
        for title, desc in infra:
            with st.expander(f"**{title}**"): st.write(desc)
    with col2:
        st.markdown('<div class="expert-header">🔥 Advanced Capital & Estate Enchants</div>', unsafe_allow_html=True)
        cap = [
            ("Immediate Financing Arrangement (IFA)", "**Strategy:** Using corporate dollars to fund a large permanent policy, then immediately borrowing the CSV back to reinvest in the business."),
            ("Cash Surrender Value (CSV) Lending", "**Strategy:** Using life insurance cash values as collateral for low-interest bank loans to fund acquisitions without triggering tax on gains."),
            ("Cascading Life Insurance", "**Strategy:** Funding policies on children/grandchildren to move wealth down generations tax-free, effectively bypassing the 21-year trust rule."),
            ("The 'Smith' with Multiplier", "**Strategy:** Leveraging primary residence equity into a corporate-owned investment portfolio to create deductible interest at the highest corporate rate."),
            ("Grantor Retained Income Trusts (GRIT)", "**Strategy:** Advanced succession planning where the grantor retains income for a term before the principal passes to beneficiaries tax-efficiently."),
            ("Donation of Publicly Traded Securities", "**Strategy:** Donating appreciated stocks to charity to eliminate the capital gains tax entirely while receiving a full FMV tax credit."),
            ("Alternative Minimum Tax (AMT) Optimization", "**Strategy:** Timing large charitable donations and capital gain realizations to navigate the restrictive 2024 AMT rules."),
            ("Shared Ownership Life Insurance", "**Strategy:** Splitting the cost/benefit of a policy between a Corp and a Shareholder to optimize estate liquidity and personal access."),
            ("Derivative-Based Yield Enhancement", "**Strategy:** Using covered call overlays or collar structures within a Corp to manufacture 'synthetic' capital gains over interest."),
            ("Private Health Services Plan (PHSP)", "**Strategy:** Structuring executive compensation to include tax-free health spending accounts that bypass payroll and income taxes.")
        ]
        for title, desc in cap:
            with st.expander(f"**{title}**"): st.write(desc)
    st.warning("⚠️ **EXPERT LEVEL ADVISORY:** These maneuvers require a 'Tax Dream Team' (CPA, Tax Lawyer, and Estate Specialist). Execution errors at this level can trigger GAAR (General Anti-Avoidance Rule) penalties.")
