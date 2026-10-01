import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# Add analysis directory to sys.path to import clean_and_eda
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / 'analysis'))
import clean_and_eda

def main():
    vis_dir = repo_root / 'visualizations'
    vis_dir.mkdir(exist_ok=True)
    
    # Recompute
    rates, series_clean, peak_clean, merged = clean_and_eda.run_all()
    
    # 1. Bar chart of return rate by cleaned payment_method
    rates_sorted = rates.sort_values(by='mean_pct', ascending=False)
    
    plt.figure(figsize=(8, 6))
    bars = plt.bar(rates_sorted.index, rates_sorted['mean_pct'], color='skyblue')
    
    # Add labels
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 0.5, f"{yval:.1f}%", ha='center', va='bottom')
        
    plt.xlabel('Payment Method')
    plt.ylabel('Return Rate (%)')
    
    cod_val = rates_sorted.loc['COD', 'mean_pct']
    card_val = rates_sorted.loc['CARD', 'mean_pct']
    ratio = round(cod_val / card_val, 1)
    
    title = f"COD Returns at {cod_val}% - {ratio}x Card"
    plt.title(title)
    
    plt.tight_layout()
    plt.savefig(vis_dir / 'return_rate_by_payment.png')
    plt.close()
    
    # 2. Line chart of OUTLIER-CORRECTED monthly revenue
    plt.figure(figsize=(10, 6))
    series_clean.index = series_clean.index.astype(str)
    plt.plot(series_clean.index, series_clean.values, marker='o', linestyle='-', color='coral')
    plt.xlabel('Month')
    plt.ylabel('Revenue (INR)')
    plt.title(f"Monthly Revenue Trend (Peak: {peak_clean})")
    plt.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(vis_dir / 'monthly_revenue_trend.png')
    plt.close()
    
    print("\nVisualizations saved successfully to visualizations/")

if __name__ == "__main__":
    main()
