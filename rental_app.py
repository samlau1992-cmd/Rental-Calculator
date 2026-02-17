import streamlit as st
import pandas as pd
import numpy as np
import base64
import os
import streamlit.components.v1 as components
import math

# --- PAGE CONFIG ---
st.set_page_config(page_title="HIA Intelligence Suite", layout="wide")

# --- BACKGROUND HELPER ---
def get_base64(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return ""

# --- STYLING ---
st.markdown("""
    <style>
    header, footer, [data-testid="stHeader"] { visibility: hidden; height: 0; }
    .block-container { max-width: 1100px; padding-top: 1.5rem; padding-bottom: 1rem; }
    .excel-header { 
        background-color: #cbd5e1; color: #1e293b; font-weight: bold; 
        padding: 4px 8px; border: 1px solid #94a3b8; margin-top: 10px;
        font-size: 0.9rem;
    }
    .stTable { border: 1px solid #94a3b8; background-color: white; }
    [data-testid="stSidebar"] .stNumberInput, [data-testid="stSidebar"] .stSelectbox, [data-testid="stSidebar"] .stRadio {
        margin-bottom: -15px !important;
    }
    @media print {
        @page { size: portrait; margin: 0.25in; }
        .stApp { zoom: 70%; background-color: white !important; background-image: none !important; }
        [data-testid="stSidebar"] { display: none !important; }
        .main .block-container { max-width: 100% !important; padding: 0 !important; margin: 0 !important; }
        div[data-testid="stTable"], .stTable { 
            display: block !important; 
            overflow: visible !important; 
            visibility: visible !important;
            page-break-inside: avoid !important; 
        }
        .excel-header, .stMetric { page-break-inside: avoid !important; }
        button, header, footer, .stActionButton { display: none !important; }
        .print-only-summary { display: block !important; visibility: visible !important; }
        .page-break { display: block; page-break-before: always; }
    }
    @media screen { .print-only-summary { display: none !important; } }
    </style>
""", unsafe_allow_html=True)

# --- GLOBAL CALCULATORS ---

@st.cache_data
def calculate_canadian_ltt(price, is_first_buyer, province, city, loan_amt=0):
    tax = 0
    
    if province == "Ontario":
        # PROVINCIAL
        if price > 2000000: tax += (price - 2000000) * 0.025 + 36475
        elif price > 400000: tax += (price - 400000) * 0.02 + 4475
        elif price > 250000: tax += (price - 250000) * 0.015 + 2225
        elif price > 55000: tax += (price - 55000) * 0.01 + 275
        else: tax += price * 0.005
        
        if is_first_buyer: tax = max(0, tax - 4000)

        # TORONTO MUNICIPAL
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

    # --- TERRITORIES ADDED ---
    elif province == "Northwest Territories":
        # $1.50 per $1,000 of value (min $100) + Mortgage fee (~$1 per $1,000)
        tax = max(100, (price / 1000) * 1.5) + max(80, (loan_amt / 1000) * 1.0)

    elif province == "Yukon":
        # Tiered registration fees (Approximate scale for common ranges)
        if price <= 100000: tax = 50
        elif price <= 500000: tax = 150
        elif price <= 1000000: tax = 250
        else: tax = 500
        tax += 50 # Standard mortgage registration fee

    elif province == "Nunavut":
        # Similar to NWT: $1.50 per $1,000 (min $60)
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

# --- NAVIGATION ---
def change_page(new_page):
    st.session_state.page = new_page
    st.rerun()

if 'page' not in st.session_state: st.session_state.page = 'home'

if st.session_state.page == 'home':
    if os.path.exists("background.png"):
        bin_str = get_base64("background.png")
        st.markdown(f"""<style>.stApp {{ background-image: url("data:image/png;base64,{bin_str}"); background-size: cover; background-position: center; }} div.stButton > button p {{ font-size: 24px !important; font-weight: bold !important; }} div.stButton > button {{ height: 100px !important; }}</style>""", unsafe_allow_html=True)
    else:
        st.markdown("<style>.stApp { background-color: #f8fafc; } div.stButton > button p { font-size: 24px !important; font-weight: bold !important; } div.stButton > button { height: 100px !important; }</style>", unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 200px;'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    if c1.button("📊 MARKET INTELLIGENCE", use_container_width=True): change_page('bdwm')
    if c2.button("🏠 RENTAL ANALYSIS", use_container_width=True): change_page('rental')

elif st.session_state.page == 'bdwm':
    if st.button("← Back"): change_page('home')
    st.title("📊 Market Intelligence Overview")
    market_html = """<div class="tradingview-widget-container"><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-market-overview.js" async>{"colorTheme": "light", "dateRange": "12M", "showChart": true, "locale": "en", "width": "100%", "height": "600", "largeChartUrl": "", "isTransparent": false, "showSymbolLogo": true, "tabs": [{"title": "Indices", "symbols": [{"s": "TSX:XIU", "d": "TSX 60"}, {"s": "FOREXCOM:SPXUSD", "d": "S&P 500"}, {"s": "FOREXCOM:NSXUSD", "d": "Nasdaq 100"}]}]}</script></div>"""
    components.html(market_html, height=650)

elif st.session_state.page == 'rental':
    if st.button("← Back"): change_page('home')
    
    with st.sidebar:
        st.subheader("PROPERTY DETAILS")
        prov = st.selectbox("Province/Territory", [
            "Ontario", "Quebec", "British Columbia", "Alberta", "Manitoba", "Saskatchewan", 
            "Nova Scotia", "New Brunswick", "PEI", "Newfoundland", 
            "Yukon", "Northwest Territories", "Nunavut"
        ])
        
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

    # --- MATH ENGINE ---
    if down_pct >= 0.20: cmhc_p = 0.0
    else: cmhc_p = 0.04 if down_pct <= 0.05 else 0.031 if down_pct <= 0.1 else 0.028 if down_pct <= 0.15 else 0.024
    temp_loan = (p_price * (1 - down_pct)) * (1 + cmhc_p)
    ltt_val = calculate_canadian_ltt(p_price, is_first_buyer, prov, city, temp_loan)
    loan_amt = temp_loan
    down_amt = p_price * down_pct
    invested_cap = (down_amt + legal_closing + ltt_val + renos + other_upfront) - heloc_used

    calc_params = [loan_amt, amort, h_rate, heloc_used, tax_bracket, claim_cca, p_price, legal_closing, ltt_val, renos, prop_tax, ins, equip_rent, condo_fees, utilities, other_mo]

    st.title(f"🏠 Rental Analysis: {city if city != 'Other' else prov}")

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

    # ... Rest of the tables/logic (at_net_rows, cost_rows, matrix_df) remains exactly the same as previous version ...
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
    labels = ["Rate change", "Mortgage rate", "Net cash return ($)", "Repayment of mortgage ($)", 
              "After tax total ($)", "Before tax total ($)", "Net cash return (%)", 
              "Repayment of mortgage (%)", "After tax total (%)", "Before tax total (%)", "Repayment period (years)"]
    matrix_df = pd.DataFrame({"Metric": labels})
    
    for s in shifts:
        cash, prin, at, bt, _ = calc_stats(*calc_params, m_rate + s, target_rent)
        if bt <= 0: repay_val = "99.00+"
        elif invested_cap <= 0: repay_val = "0.00 (Infinite)"
        else: repay_val = f"{invested_cap/bt:.2f}"

        if invested_cap <= 0: cash_p, prin_p, at_p, bt_p = "∞", "∞", "∞", "∞"
        else:
            cash_p = f"{(cash/invested_cap)*100:.2f}%"
            prin_p = f"{(prin/invested_cap)*100:.2f}%"
            at_p = f"{(at/invested_cap)*100:.2f}%"
            bt_p = f"{(bt/invested_cap)*100:.2f}%"

        matrix_df[f"{s*100:+.1f}%"] = [f"{s*100:+.1f}%", f"{(m_rate+s)*100:.2f}%", f"${cash:,.0f}", f"${prin:,.0f}", f"${at:,.0f}", f"${bt:,.0f}", cash_p, prin_p, at_p, bt_p, repay_val]
    
    st.table(matrix_df.style.apply(lambda row: ['background-color: yellow;' if row.name in [4, 5, 8, 9] else '' for _ in row], axis=1))

    # --- PRINT ONLY SUMMARY ---
    st.markdown("<div class='page-break print-only-summary'></div><div class='print-only-summary'><div class='excel-header'>ANALYSIS INPUT SUMMARY</div>", unsafe_allow_html=True)
    summary_df = pd.DataFrame({
        "Variable": ["Province", "City", "Purchase Price", "Downpayment %", "Mortgage Rate", "Target Rent", "Property Tax", "Renovations"],
        "Value": [prov, city, f"${p_price:,.0f}", f"{down_pct*100:.1f}%", f"{m_rate*100:.2f}%", f"${target_rent:,.0f}", f"${prop_tax:,.0f}", f"${renos:,.0f}"]
    })
    st.table(summary_df)
    st.markdown("</div>", unsafe_allow_html=True)
