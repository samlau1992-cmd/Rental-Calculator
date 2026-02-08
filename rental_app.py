import streamlit as st
import pandas as pd

# --- APP CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Rental Profit Sensitivity Calculator")

# --- CALCULATION FUNCTIONS ---

def calculate_ontario_ltt(price, city):
    """Calculates Ontario Provincial LTT and adds Toronto Municipal LTT if selected."""
    prov_ltt = 0
    if price > 0:
        prov_ltt += min(price, 55000) * 0.005
    if price > 55000:
        prov_ltt += (min(price, 250000) - 55000) * 0.01
    if price > 250000:
        prov_ltt += (min(price, 400000) - 250000) * 0.015
    if price > 400000:
        prov_ltt += (min(price, 2000000) - 400000) * 0.02
    if price > 2000000:
        prov_ltt += (price - 2000000) * 0.025

    toronto_ltt = 0
    if city == "Toronto":
        if price > 0:
            toronto_ltt += min(price, 55000) * 0.005
        if price > 55000:
            toronto_ltt += (min(price, 250000) - 55000) * 0.01
        if price > 250000:
            toronto_ltt += (min(price, 400000) - 250000) * 0.015
        if price > 400000:
            toronto_ltt += (min(price, 2000000) - 400000) * 0.02
        if price > 2000000:
            toronto_ltt += (price - 2000000) * 0.025
            
    return prov_ltt + toronto_ltt

def get_cmhc_rate(down_percent):
    if down_percent >= 0.20: return 0.0
    if down_percent < 0.10: return 0.040
    if down_percent < 0.15: return 0.031
    if down_percent < 0.20: return 0.028
    return 0.024

st.title("🏠 Rental Profit Sensitivity Calculator")

# --- SIDEBAR: FILLABLE FIELDS ---
st.sidebar.header("PROPERTY PURCHASE DETAILS")
purchase_price = st.sidebar.number_input("Purchase Price ($)", value=280000.00, step=1000.00, format="%.2f")
down_percent = st.sidebar.number_input("Downpayment (as decimal, e.g. 0.05)", value=0.05, step=0.01, format="%.2f")
mortgage_rate = st.sidebar.number_input("Mortgage rate (as decimal, e.g. 0.0498)", value=0.0498, format="%.4f")
heloc_rate = st.sidebar.number_input("HELOC rate (as decimal, e.g. 0.06)", value=0.0600, format="%.4f")
amortization = st.sidebar.number_input("Amortization period (Years)", value=25)
marginal_tax_rate = st.sidebar.number_input("Marginal tax rate (as decimal, e.g. 0.4497)", value=0.4497, format="%.4f")

st.sidebar.header("CAPITAL COMMITMENT")
city_list = ["Windsor", "Toronto", "Ottawa", "Mississauga", "Brampton", "Hamilton", "London", "Markham", "Vaughan", "Kitchener"]
selected_city = st.sidebar.selectbox("Select Ontario City (For Land Transfer Tax)", options=sorted(city_list))

legal_disbursements = st.sidebar.number_input("Legal + disbursement", value=3500.00, format="%.2f")
renovation_cost = st.sidebar.number_input("Renovation", value=0.00, format="%.2f")
other_capital = st.sidebar.number_input("Other Capital Costs", value=0.00, format="%.2f")

# Auto-LTT
auto_ltt = calculate_ontario_ltt(purchase_price, selected_city)
st.sidebar.info(f"Auto-calculated Land Transfer Tax: ${auto_ltt:,.2f}")

st.sidebar.header("MONTHLY COST")
prop_tax = st.sidebar.number_input("Property tax", value=125.00, format="%.2f")
insurance = st.sidebar.number_input("Insurance", value=65.00, format="%.2f")
equip_rental = st.sidebar.number_input("Equipment rental", value=56.00, format="%.2f")
condo_fees = st.sidebar.number_input("Condo fees", value=0.00, format="%.2f")
utility = st.sidebar.number_input("Utility", value=0.00, format="%.2f")
other_monthly = st.sidebar.number_input("Other Monthly Cost", value=0.00, format="%.2f")

st.sidebar.header("FUNDING BREAKDOWN")
heloc_funding = st.sidebar.number_input("HELOC Funding", value=15000.00, format="%.2f")

# --- CALCULATIONS ---
down_amt = purchase_price * down_percent
loan_base = purchase_price - down_amt
cmhc_premium = loan_base * get_cmhc_rate(down_percent)
total_mortgage = loan_base + cmhc_premium

m_int = mortgage_rate / 12
n_pay = amortization * 12
monthly_pi = total_mortgage * (m_int * (1 + m_int)**n_pay) / ((1 + m_int)**n_pay - 1)

total_capital_req = down_amt + legal_disbursements + auto_ltt + renovation_cost + other_capital
invested_capital = total_capital_req - heloc_funding

heloc_monthly_int = (heloc_funding * heloc_rate) / 12
total_monthly_cost = monthly_pi + prop_tax + insurance + equip_rental + condo_fees + utility + other_monthly + heloc_monthly_int

# --- MAIN DISPLAY ---
col1, col2, col3 = st.columns(3)
col1.metric("Invested Capital", f"${invested_capital:,.2f}")
col2.metric("Monthly P&I", f"${monthly_pi:,.2f}")
col3.metric("Total Monthly Cost", f"${total_monthly_cost:,.2f}")

st.markdown("---")

# Rental Scenarios Table
st.subheader("NET CASH RETURN")
rental_rates = [1800, 1900, 2000, 2100, 2200]
scenario_list = []
for r in rental_rates:
    m_net = r - total_monthly_cost
    scenario_list.append({
        "Rental Rate": f"${r:,.2f}",
        "Monthly Net Return": f"${m_net:,.2f}",
        "Annual Net Return": f"${m_net*12:,.2f}"
    })
st.table(pd.DataFrame(scenario_list))

# Sensitivity Matrix
st.subheader("RETURN METRIC MATRIX - INTEREST RATE SENSITIVITY")
rate_changes = [-0.025, -0.02, -0.015, -0.01, -0.005, 0, 0.005, 0.01, 0.015, 0.02, 0.025]
matrix_data = []

for change in rate_changes:
    s_m_rate = (mortgage_rate + change) / 12
    s_h_rate = (heloc_rate + change) / 12
    
    # Mortgage P&I with Rate Change
    s_pi = total_mortgage * (s_m_rate * (1 + s_m_rate)**n_pay) / ((1 + s_m_rate)**n_pay - 1)
    s_heloc_int = (heloc_funding * s_h_rate) / 12
    s_total_monthly = s_pi + prop_tax + insurance + equip_rental + condo_fees + utility + other_monthly + s_heloc_int
    
    # Annual Net Cash Flow
    ann_cash = (1800 - s_total_monthly) * 12
    
    # Principal Repayment
    first_month_interest = total_mortgage * s_m_rate
    ann_principal = (s_pi - first_month_interest) * 12
    
    # Before Tax Total logic (Tax Shield + Gains)
    cca = purchase_price * 0.04
    deductions = (first_month_interest * 12) + ((prop_tax + insurance + equip_rental + condo_fees + utility + other_monthly + s_heloc_int) * 12) + cca
    taxable_income = (1800 * 12) - deductions
    # Tax savings if negative taxable income
    tax_impact = taxable_income * marginal_tax_rate
    before_tax_total = (ann_cash + ann_principal) - tax_impact
    
    matrix_data.append({
        "Rate Change": f"{change*100:+.2f}%",
        "Mortgage Rate": f"{(mortgage_rate + change)*100:.2f}%",
        "Net Cash Return ($)": f"${ann_cash:,.2f}",
        "Principal Repayment ($)": f"${ann_principal:,.2f}",
        "Total Return (%)": f"{(before_tax_total / invested_capital)*100:.2f}%" if invested_capital != 0 else "0.00%"
    })

st.dataframe(pd.DataFrame(matrix_data), use_container_width=True)