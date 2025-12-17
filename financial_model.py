# Financial model for Alfa-Bank initiatives (BNPL + Subscription Financial Wellness + Marketplace + Restructuring savings)

# Assumptions are documented in the accompanying chat response and supported by cited sources.

import pandas as pd
import numpy as np

# Base assumptions (values in billion RUB where appropriate)
assumptions = {
    "customers_m": 37.0,  # Alfa customers, million (source)
    "retail_portfolio_trln": 8.9,  # trillion RUB (retail loan portfolio end-2024)
    "unsecured_share": 0.58,  # share of retail portfolio that is consumer/unsecured
    "usd_rub": 80.0,  # USD->RUB conversion for market-size estimates
    "bnpl_gmv_usd_2025": 9.56,  # ResearchAndMarkets BNPL 2025 market estimate (USD)
    
    # Subscription pricing and adoption
    "sub_monthly_rub": 199,
    "sub_take_rate": [0.005, 0.02, 0.05],  # % of customers subscribing in years 1..3
    
    # BNPL capture share of national GMV (years 1..3)
    "bnpl_share": [0.02, 0.05, 0.10],
    "bnpl_merchant_fee": 0.02,  # 2% merchant fee (take rate)
    
    # Marketplace GMV (bank's own marketplace in RUB)
    "mp_gmv_rub": [50, 120, 250],  # billion RUB years 1..3
    "mp_commission": 0.015,  # 1.5% commission
    
    # Credit-loss savings from restructuring/financial-wellness (applied to unsecured consumer portfolio)
    "credit_cost_of_risk": 0.04,  # 4% annual cost of risk on unsecured (baseline)
    "cr_savings_factor": [0.15, 0.25, 0.40],  # share of cost-of-risk reduced by initiatives
    
    # Costs and investments (billion RUB)
    "capex": [2.5, 1.0, 0.5],  # initial and follow-up platform investments
    "opex": [1.2, 1.5, 2.0],  # platform + marketing + partnerships running cost
    "tax_rate": 0.20,
    "discount_rate": 0.15
}

# Derived base numbers
unsecured_portfolio = assumptions["retail_portfolio_trln"] * 1000 * assumptions["unsecured_share"]  # in billion RUB
bnpl_gmv_rub = assumptions["bnpl_gmv_usd_2025"] * assumptions["usd_rub"]  # in billion RUB

# Year-by-year projection (3 years)
years = [2025, 2026, 2027]
rows = []

for i, y in enumerate(years):
    # Subscription revenue
    subs = assumptions["customers_m"] * 1e6 * assumptions["sub_take_rate"][i]  # number of subscribers
    sub_revenue = subs * (assumptions["sub_monthly_rub"] * 12) / 1e9  # in billion RUB (annual)
    
    # BNPL revenue (merchant fee on captured GMV)
    bnpl_revenue = bnpl_gmv_rub * assumptions["bnpl_share"][i] * assumptions["bnpl_merchant_fee"] / 1e9  # bn RUB
    
    # Marketplace revenue
    mp_revenue = assumptions["mp_gmv_rub"][i] * assumptions["mp_commission"]  # bn RUB (already in bn RUB)
    
    # Credit-loss savings (reduced provisions)
    baseline_provisions = unsecured_portfolio * assumptions["credit_cost_of_risk"] / 1e3  # bn RUB (portfolio in bn)
    cr_savings = baseline_provisions * assumptions["cr_savings_factor"][i]  # bn RUB saved
    
    # Total revenue (commissions + realized provisioning savings)
    total_revenue = sub_revenue + bnpl_revenue + mp_revenue
    
    # Cashflow before tax, before capex
    ebitda_like = total_revenue + cr_savings - assumptions["opex"][i]
    
    # Free cash flow (simplified): ebitda_like - capex (and apply tax to positive ebitda_like)
    tax = 0 if ebitda_like <= 0 else ebitda_like * assumptions["tax_rate"]
    fcff = ebitda_like - tax - assumptions["capex"][i]
    
    rows.append({
        "year": y,
        "subscribers_k": round(subs/1e3, 1),
        "sub_revenue_bn": round(sub_revenue, 3),
        "bnpl_revenue_bn": round(bnpl_revenue, 3),
        "mp_revenue_bn": round(mp_revenue, 3),
        "total_commission_revenue_bn": round(total_revenue, 3),
        "baseline_provisions_bn": round(baseline_provisions, 3),
        "cr_savings_bn": round(cr_savings, 3),
        "opex_bn": round(assumptions["opex"][i], 3),
        "capex_bn": round(assumptions["capex"][i], 3),
        "ebitda_like_bn": round(ebitda_like, 3),
        "tax_bn": round(tax, 3),
        "fcff_bn": round(fcff, 3)
    })

df = pd.DataFrame(rows)

# NPV and IRR of the projected 3-year cashflows (using discount rate)
cashflows = df["fcff_bn"].values.tolist()
# Add initial capex as negative up-front cashflow in year0 if desired. Here capex included in year1.
discount_rate = assumptions["discount_rate"]
npv = sum([cashflows[i] / ((1+discount_rate)**(i+1)) for i in range(len(cashflows))])

# IRR calculation using Newton-Raphson method
def irr(cfs, guess=0.1, max_iter=100, tol=1e-6):
    """Calculate Internal Rate of Return using Newton-Raphson method"""
    def npv_func(rate):
        return sum([cfs[i] / ((1 + rate) ** (i + 1)) for i in range(len(cfs))])
    
    def npv_derivative(rate):
        return sum([-cfs[i] * (i + 1) / ((1 + rate) ** (i + 2)) for i in range(len(cfs))])
    
    try:
        rate = guess
        for _ in range(max_iter):
            npv = npv_func(rate)
            if abs(npv) < tol:
                # Validate: IRR should be reasonable (between -1 and 10, for example)
                if -1 < rate < 10:
                    return rate
                else:
                    return None
            
            derivative = npv_derivative(rate)
            if abs(derivative) < tol:
                break
            
            rate = rate - npv / derivative
            # Keep rate in reasonable bounds
            if rate < -0.99 or rate > 10:
                return None
        
        # Final check
        if abs(npv_func(rate)) < tol and -1 < rate < 10:
            return rate
        return None
    except:
        return None

irr_val = irr(cashflows)

# Sensitivity: optimistic/pessimistic for subscription adoption and bnpl share
sens = []
for scenario in [("pessimistic", [0.002, 0.01, 0.02], [0.01, 0.03, 0.06]), 
                 ("optimistic", [0.01, 0.04, 0.09], [0.03, 0.08, 0.15])]:
    name, sub_rates, bnpl_shares = scenario
    rows_s = []
    for i in range(3):
        subs_s = assumptions["customers_m"] * 1e6 * sub_rates[i]
        sub_rev_s = subs_s * (assumptions["sub_monthly_rub"] * 12) / 1e9
        bnpl_rev_s = bnpl_gmv_rub * bnpl_shares[i] * assumptions["bnpl_merchant_fee"] / 1e9
        mp_rev_s = assumptions["mp_gmv_rub"][i] * assumptions["mp_commission"]
        total_rev_s = sub_rev_s + bnpl_rev_s + mp_rev_s
        baseline_provisions_s = baseline_provisions
        cr_savings_s = baseline_provisions_s * assumptions["cr_savings_factor"][i]
        ebitda_like_s = total_rev_s + cr_savings_s - assumptions["opex"][i]
        tax_s = 0 if ebitda_like_s <= 0 else ebitda_like_s * assumptions["tax_rate"]
        fcff_s = ebitda_like_s - tax_s - assumptions["capex"][i]
        rows_s.append(fcff_s)
    
    npv_s = sum([rows_s[i] / ((1+discount_rate)**(i+1)) for i in range(3)])
    irr_s = irr(rows_s)
    sens.append({
        "scenario": name, 
        "npv_bn": round(npv_s, 3), 
        "irr": round(irr_s, 3) if irr_s is not None else None
    })

# Display results
separator = "=" * 80
print("\n" + separator)
print("ALFA-BANK INITIATIVES FINANCIAL PROJECTION")
print(separator)
print("\nProjected Cashflows (3 years):")
print(df.to_string(index=False))
print("\n" + "-" * 80)
npv_text = f"NPV (15% discount rate): {npv:.3f} billion RUB"
print(npv_text)
if irr_val is not None:
    print(f"IRR: {irr_val:.3f} ({irr_val*100:.1f}%)")
else:
    print("IRR: Could not be calculated")
print("\nSensitivity Analysis:")
for s in sens:
    scenario_name = s['scenario'].capitalize()
    npv_val = s['npv_bn']
    if s['irr'] is not None:
        irr_pct = s['irr'] * 100
        print(f"  {scenario_name}: NPV = {npv_val:.3f} bn RUB, IRR = {s['irr']:.3f} ({irr_pct:.1f}%)")
    else:
        print(f"  {scenario_name}: NPV = {npv_val:.3f} bn RUB, IRR = N/A")
print(separator)

# Export to Excel
output_file = "alfa_bank_initiatives_projection.xlsx"
with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    df.to_excel(writer, sheet_name='Projection', index=False)
    
    # Create summary sheet
    summary_data = {
        "Metric": [
            "Unsecured Portfolio (bn RUB)",
            "BNPL Market Size (bn RUB)",
            "NPV (bn RUB)",
            "IRR (%)",
        ],
        "Value": [
            round(unsecured_portfolio/1e3, 3),
            round(bnpl_gmv_rub/1e3, 3),
            round(npv, 3),
            round(irr_val*100, 2) if irr_val is not None else "N/A",
        ]
    }
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    # Sensitivity analysis sheet
    sens_df = pd.DataFrame(sens)
    sens_df.to_excel(writer, sheet_name='Sensitivity', index=False)

print(f"\nResults exported to {output_file}")

# Return summary dictionary for programmatic access
summary = {
    "assumptions": assumptions,
    "unsecured_portfolio_bn": round(unsecured_portfolio/1e3, 3),
    "bnpl_gmv_rub_bn": round(bnpl_gmv_rub/1e3, 3),
    "npv_bn": round(npv, 3),
    "irr": round(irr_val, 3) if irr_val is not None else None,
    "sensitivity": sens
}

# Return both summary and dataframe records
print("\nSummary dictionary and dataframe records available for further processing.")