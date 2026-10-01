import pandas as pd
import numpy as np
from pathlib import Path
import json

def load_and_inspect():
    repo_root = Path(__file__).resolve().parent.parent
    data_dir = repo_root / 'data'
    
    customers = pd.read_csv(data_dir / 'customers.csv')
    products = pd.read_csv(data_dir / 'products.csv')
    orders = pd.read_csv(data_dir / 'orders.csv')
    
    print("--- Task 1: Load and inspect ---")
    print("Orders shape:", orders.shape)
    
    for name, df in [("Customers", customers), ("Products", products), ("Orders", orders)]:
        print(f"\n{name} Head:\n", df.head(3))
        print(f"\n{name} Dtypes:\n", df.dtypes)
        print(f"\n{name} Nulls:\n", df.isnull().sum())
        
    return customers, products, orders

def standardize_payment(orders):
    print("\n--- Task 2: Standardize payment_method ---")
    print("Unique payment methods BEFORE:", orders['payment_method'].unique())
    orders['payment_method'] = orders['payment_method'].str.strip().str.upper()
    print("Unique payment methods AFTER:", orders['payment_method'].unique())
    print("Value counts AFTER:\n", orders['payment_method'].value_counts())
    return orders

def remove_duplicates(orders):
    print("\n--- Task 3: Remove duplicates ---")
    dup_mask = orders.duplicated(subset=['customer_id', 'product_id', 'order_date', 'quantity', 'discount_pct', 'payment_method', 'rating', 'returned'], keep='first')
    dropped_orders = orders[dup_mask].copy()
    orders_clean = orders[~dup_mask].copy()
    print("Dropped order_ids:", dropped_orders['order_id'].tolist())
    print("Cleaned orders shape:", orders_clean.shape)
    print("Methodology: Duplicate rows were identified based on all columns except order_id, because order_id differs on the duplicate rows by design. These duplicates are kept in a separate DataFrame.")
    return orders_clean, dropped_orders

def impute_missing(orders_clean):
    print("\n--- Task 4: Impute (on deduplicated frame) ---")
    discount_nan_count = orders_clean['discount_pct'].isnull().sum()
    orders_clean['discount_pct'] = orders_clean['discount_pct'].fillna(0)
    
    median_rating = orders_clean['rating'].median()
    print("Median of non-null ratings BEFORE imputing:", median_rating)
    rating_nan_count = orders_clean['rating'].isnull().sum()
    orders_clean['rating'] = orders_clean['rating'].fillna(median_rating)
    
    print("Count of rows affected by discount imputation:", discount_nan_count)
    print("Count of rows affected by rating imputation:", rating_nan_count)
    print("Nulls after imputation:")
    print(orders_clean[['discount_pct', 'rating']].isnull().sum())
    return orders_clean

def merge_and_reconcile(orders_clean, dropped_orders, orders_raw, customers, products):
    print("\n--- Task 5: Merge and reconcile ---")
    # Cleaned
    merged = orders_clean.merge(products, on='product_id', how='left').merge(customers, on='customer_id', how='left')
    merged['order_value'] = merged['quantity'] * merged['price'] * (1 - merged['discount_pct']/100)
    cleaned_total = merged['order_value'].sum()
    
    # Raw
    raw_merged = orders_raw.merge(products, on='product_id', how='left')
    raw_merged['discount_pct_filled'] = raw_merged['discount_pct'].fillna(0)
    raw_merged['order_value'] = raw_merged['quantity'] * raw_merged['price'] * (1 - raw_merged['discount_pct_filled']/100)
    raw_total = raw_merged['order_value'].sum()
    
    # Dropped
    dropped_merged = dropped_orders.merge(products, on='product_id', how='left')
    dropped_merged['discount_pct_filled'] = dropped_merged['discount_pct'].fillna(0)
    dropped_merged['order_value'] = dropped_merged['quantity'] * dropped_merged['price'] * (1 - dropped_merged['discount_pct_filled']/100)
    dropped_total = dropped_merged['order_value'].sum()
    
    print(f"Total order_value (cleaned): {cleaned_total:.2f}")
    print(f"Total order_value (raw): {raw_total:.2f}")
    print(f"Total order_value (dropped): {dropped_total:.2f}")
    
    reconciliation = f"The delta between raw and cleaned totals ({raw_total:.2f} - {cleaned_total:.2f} = {(raw_total - cleaned_total):.2f}) equals the combined order_value of the {len(dropped_orders)} dropped duplicate rows ({dropped_total:.2f}). Note that the imputation step does not change any order_value total because discount NA was mapped to 0."
    print("Reconciliation note:", reconciliation)
    
    delta = raw_total - cleaned_total
    check_pass = np.isclose(delta, dropped_total)
    print(f"Computed check (raw - cleaned == dropped_total): {check_pass}")
    
    return merged, cleaned_total, raw_total, dropped_total

def iqr_outliers(merged):
    print("\n--- Task 6: IQR outliers on quantity ---")
    Q1 = merged['quantity'].quantile(0.25)
    Q3 = merged['quantity'].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    print(f"Q1: {Q1}, Q3: {Q3}, IQR: {IQR}, lower: {lower}, upper: {upper}")
    
    merged['is_outlier'] = (merged['quantity'] < lower) | (merged['quantity'] > upper)
    outliers = merged[merged['is_outlier']]
    print("Flagged rows (order_id, quantity):")
    for _, row in outliers.iterrows():
        print(f"  {row['order_id']}, {row['quantity']}")
    return merged

def hypothesis_testing(merged):
    print("\n--- Task 7: Hypothesis ---")
    print("Hypothesis: COD orders have a higher return rate than Card and UPI")
    rates = merged.groupby('payment_method')['returned'].agg(['count', 'mean'])
    rates['mean_pct'] = (rates['mean'] * 100).round(1)
    print(rates)
    
    cod_rate = rates.loc['COD', 'mean_pct']
    max_rate = rates['mean_pct'].max()
    result = "Confirmed" if cod_rate == max_rate else "Rejected"
    print(f"Result: {result}")
    return rates

def multilevel_segmentation(merged):
    print("\n--- Task 8: Multi-level segmentation ---")
    seg = merged.groupby(['payment_method', 'city_tier'])['returned'].agg(['count', 'mean'])
    seg['return_rate_pct'] = (seg['mean'] * 100).round(1)
    print("Segmentation:\n", seg)
    
    highest_risk_idx = seg['return_rate_pct'].idxmax()
    highest_risk_val = seg['return_rate_pct'].max()
    print(f"Highest-risk segment programmatically identified: {highest_risk_idx} with {highest_risk_val}% return rate")
    
    cod_t1 = seg.loc[('COD', 1)]
    cod_t2 = seg.loc[('COD', 2)]
    print(f"COD Tier-1: {cod_t1['return_rate_pct']}% ({int(cod_t1['count'])} orders) vs COD Tier-2: {cod_t2['return_rate_pct']}% ({int(cod_t2['count'])} orders)")
    return seg, highest_risk_idx, highest_risk_val

def correlation(merged):
    print("\n--- Task 9: Correlation ---")
    corr_vars = ['rating', 'returned', 'discount_pct', 'quantity']
    corr_matrix = merged[corr_vars].corr()
    print("Correlation matrix:\n", corr_matrix)
    
    print("\nPairwise correlations:")
    disc_ret_r = 0
    for i in range(len(corr_vars)):
        for j in range(i+1, len(corr_vars)):
            v1, v2 = corr_vars[i], corr_vars[j]
            r = corr_matrix.loc[v1, v2]
            abs_r = abs(r)
            if abs_r < 0.2:
                band = "negligible"
            elif abs_r < 0.4:
                band = "weak"
            elif abs_r < 0.7:
                band = "moderate"
            else:
                band = "strong"
            print(f"{v1} vs {v2}: r = {r:.4f} -> {band}")
            
            if (v1 == 'discount_pct' and v2 == 'returned') or (v2 == 'discount_pct' and v1 == 'returned'):
                disc_ret_r = abs_r
                
    result = "Busted" if disc_ret_r < 0.2 else "Supported"
    print(f"Hypothesis 'higher discounts reduce returns': {result}")
    return corr_matrix

def time_series(merged):
    print("\n--- Task 10: Outlier-corrected time series ---")
    merged['order_date'] = pd.to_datetime(merged['order_date'])
    merged['year_month'] = merged['order_date'].dt.to_period('M')
    
    series_all = merged.groupby('year_month')['order_value'].sum()
    series_clean = merged[~merged['is_outlier']].groupby('year_month')['order_value'].sum()
    
    df_ts = pd.DataFrame({'With Outliers': series_all, 'Corrected': series_clean})
    print("Monthly revenue:")
    print(df_ts)
    
    peak_all = series_all.idxmax()
    val_all = series_all.max()
    peak_clean = series_clean.idxmax()
    val_clean = series_clean.max()
    
    outliers = merged[merged['is_outlier']]
    outlier_details = []
    for _, row in outliers.iterrows():
        outlier_details.append(f"{row['order_id']} on {row['order_date'].date()}")
        
    explanation = f"The apparent peak in series with outliers ({peak_all}) is an artifact of the bulk orders (flagged rows: {', '.join(outlier_details)}). The true peak month is the corrected series peak: {peak_clean}."
    print("Explanation:", explanation)
    
    return series_all, series_clean, peak_clean, peak_all, val_clean, df_ts

def export_findings(cleaned_total, raw_total, dropped_total, rates, highest_risk_idx, highest_risk_val, peak_clean, val_clean, peak_all, df_ts):
    repo_root = Path(__file__).resolve().parent.parent
    narrator_dir = repo_root / 'narrator'
    narrator_dir.mkdir(exist_ok=True)
    
    def to_py(val):
        if pd.isna(val): return None
        return float(val) if isinstance(val, (np.floating, float)) else int(val) if isinstance(val, (np.integer, int)) else str(val)

    return_rate_dict = {
        pm: to_py(rates.loc[pm, 'mean_pct']) 
        for pm in rates.index
    }
    
    findings = {
        "cleaned_total_revenue_inr": to_py(round(cleaned_total, 2)),
        "raw_total_revenue_inr": to_py(round(raw_total, 2)),
        "duplicate_reconciliation_delta_inr": to_py(round(dropped_total, 2)),
        "return_rate_by_payment": return_rate_dict,
        "highest_risk_segment": {
            "payment_method": highest_risk_idx[0],
            "city_tier": to_py(highest_risk_idx[1]),
            "return_rate_pct": to_py(highest_risk_val)
        },
        "true_peak_month": {
            "month": str(peak_clean),
            "revenue_inr": to_py(round(val_clean, 2))
        },
        "outlier_inflated_month": {
            "month": str(peak_all),
            "apparent_revenue_inr": to_py(round(df_ts.loc[peak_all, 'With Outliers'], 2)),
            "corrected_revenue_inr": to_py(round(df_ts.loc[peak_all, 'Corrected'], 2))
        }
    }
    
    json_path = narrator_dir / 'findings.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(findings, f, indent=2)
    print(f"\nFindings written to {json_path}")

def run_all():
    c, p, o = load_and_inspect()
    o_raw = o.copy()
    o = standardize_payment(o)
    o_clean, o_dropped = remove_duplicates(o)
    o_clean = impute_missing(o_clean)
    merged, c_total, r_total, d_total = merge_and_reconcile(o_clean, o_dropped, o_raw, c, p)
    merged = iqr_outliers(merged)
    rates = hypothesis_testing(merged)
    seg, hr_idx, hr_val = multilevel_segmentation(merged)
    correlation(merged)
    s_all, s_clean, peak_c, peak_a, val_c, df_ts = time_series(merged)
    export_findings(c_total, r_total, d_total, rates, hr_idx, hr_val, peak_c, val_c, peak_a, df_ts)
    
    return rates, s_clean, peak_c, merged

if __name__ == "__main__":
    run_all()
