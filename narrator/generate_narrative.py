import os
import json
import argparse
from pathlib import Path
import calendar
import datetime

def load_findings(path=None):
    if path is None:
        repo_root = Path(__file__).resolve().parent.parent
        path = repo_root / 'narrator' / 'findings.json'
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def build_system_instruction():
    return (
        "You are a senior data analyst writing for Mamaearth's regional ops and finance heads. "
        "Your task is to write a business report using exactly three labeled sections: "
        "Situation, Complication, and Resolution. The total length should be about 250 words. "
        "Every number you include must come exactly from the supplied findings and appear with the same value; "
        "do not invent or estimate any statistics. "
        "Format all monetary values in INR with thousands separators and two decimals, and percentages with one decimal."
    )

def _format_money(val):
    return f"{val:,.2f}"

def _format_month(ym_str):
    try:
        dt = datetime.datetime.strptime(ym_str, '%Y-%m')
        return f"{calendar.month_name[dt.month]} {dt.year}"
    except:
        return ym_str

def build_user_prompt(findings):
    return (
        f"Please write the SCR narrative based on the following findings:\n\n"
        f"1. Cleaned Total Revenue: INR {_format_money(findings['cleaned_total_revenue_inr'])}\n"
        f"2. Raw Total Revenue: INR {_format_money(findings['raw_total_revenue_inr'])}\n"
        f"3. Duplicate Reconciliation Delta: INR {_format_money(findings['duplicate_reconciliation_delta_inr'])}\n"
        f"4. Return Rates by Payment: {findings['return_rate_by_payment']}\n"
        f"5. Highest-Risk Segment: {findings['highest_risk_segment']['payment_method']} in Tier {findings['highest_risk_segment']['city_tier']} with {findings['highest_risk_segment']['return_rate_pct']:.1f}% return rate.\n"
        f"6. True Peak Month: {_format_month(findings['true_peak_month']['month'])} with revenue INR {_format_money(findings['true_peak_month']['revenue_inr'])}\n"
        f"7. Outlier-Inflated Month: {_format_month(findings['outlier_inflated_month']['month'])} had an apparent revenue of INR {_format_money(findings['outlier_inflated_month']['apparent_revenue_inr'])}, but its corrected revenue is INR {_format_money(findings['outlier_inflated_month']['corrected_revenue_inr'])}.\n"
    )

def generate_scr_narrative(findings):
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return generate_scr_narrative_offline(findings)
    
    model_name = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash')
    
    try:
        from google import genai
        from google.genai import types
        
        client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=30000))
        system_instruction = build_system_instruction()
        user_prompt = build_user_prompt(findings)
        
        # deterministic output because this is a factual business report, not creative writing
        # max_output_tokens is set explicitly and generously because the model's internal thinking tokens can count against the budget
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.0,
            max_output_tokens=2048
        )
        
        response = client.models.generate_content(
            model=model_name,
            contents=user_prompt,
            config=config
        )
        
        text = response.text
        if not text:
            raise ValueError("Empty response text from Gemini API")
            
        tokens = None
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            tokens = response.usage_metadata.total_token_count
            
        return {
            "status": "success",
            "narrative": text,
            "tokens": tokens,
            "source": "gemini"
        }
    except Exception as e:
        offline_result = generate_scr_narrative_offline(findings)
        offline_result["message"] = f"Fell back to offline mode due to error: {str(e)}"
        return offline_result

def generate_scr_narrative_offline(findings):
    rev_str = _format_money(findings['cleaned_total_revenue_inr'])
    cod_rate = f"{findings['return_rate_by_payment']['COD']:.1f}"
    
    seg = findings['highest_risk_segment']
    seg_rate = f"{seg['return_rate_pct']:.1f}"
    seg_name = f"{seg['payment_method']} in Tier {seg['city_tier']}"
    
    delta = _format_money(findings['duplicate_reconciliation_delta_inr'])
    
    peak_month = _format_month(findings['true_peak_month']['month'])
    peak_rev = _format_money(findings['true_peak_month']['revenue_inr'])
    
    narrative = f"""Situation
The business generated a cleaned total revenue of INR {rev_str} during the period. The true peak month for revenue was {peak_month} at INR {peak_rev}. Data cleaning identified duplicate records representing INR {delta}, which were successfully reconciled.

Complication
The primary issue affecting profitability is the elevated return rate associated with certain payment methods. The overall COD return rate stands at {cod_rate}%. Furthermore, the highest-risk segment identified is {seg_name}, exhibiting a severe return rate of {seg_rate}%.

Resolution
Regional ops and finance heads should investigate the fulfillment and customer verification processes for COD orders, particularly in Tier {seg['city_tier']} cities. Correcting the outlier-inflated sales data is essential for accurate revenue forecasting."""

    return {
        "status": "success",
        "narrative": narrative,
        "tokens": None,
        "source": "offline"
    }

def check_numeric_accuracy(narrative, findings):
    normalized_narrative = narrative.replace(',', '')
    
    c_rev = str(findings['cleaned_total_revenue_inr'])
    c_rev_f = f"{findings['cleaned_total_revenue_inr']:.2f}"
    
    cod_r = f"{findings['return_rate_by_payment']['COD']:.1f}"
    seg_r = f"{findings['highest_risk_segment']['return_rate_pct']:.1f}"
    
    delta = str(findings['duplicate_reconciliation_delta_inr'])
    delta_f = f"{findings['duplicate_reconciliation_delta_inr']:.2f}"
    
    peak_month = _format_month(findings['true_peak_month']['month'])
    peak_rev = str(findings['true_peak_month']['revenue_inr'])
    peak_rev_f = f"{findings['true_peak_month']['revenue_inr']:.2f}"
    
    checks = [
        ("Cleaned Total Revenue", [c_rev, c_rev_f]),
        ("COD Return Rate", [cod_r]),
        ("Highest-Risk Segment Rate", [seg_r]),
        ("Duplicate Delta", [delta, delta_f]),
        ("Peak Month Name & Revenue", [peak_month], [peak_rev, peak_rev_f])
    ]
    
    all_pass = True
    print("\n--- Numeric Accuracy Check ---")
    for check in checks:
        name = check[0]
        vals1 = check[1]
        pass1 = any(v in normalized_narrative for v in vals1) or any(v in narrative for v in vals1)
        
        if len(check) > 2:
            vals2 = check[2]
            pass2 = any(v in normalized_narrative for v in vals2) or any(v in narrative for v in vals2)
            passed = pass1 and pass2
        else:
            passed = pass1
            
        status = "PASS" if passed else "FAIL"
        print(f"{name}: {status}")
        if not passed:
            all_pass = False
            
    return all_pass

def main():
    parser = argparse.ArgumentParser(description="Generate SCR narrative")
    parser.add_argument("--offline", action="store_true", help="Force offline mode")
    parser.add_argument("--save", action="store_true", help="Save output to sample_output.txt if online")
    args = parser.parse_args()
    
    repo_root = Path(__file__).resolve().parent.parent
    findings = load_findings()
    
    if args.offline:
        result = generate_scr_narrative_offline(findings)
    else:
        result = generate_scr_narrative(findings)
        
    print(f"Narrative Source: {result['source']}")
    if 'message' in result:
        print(f"Message: {result['message']}")
        
    print("\n" + "="*40 + "\n" + result['narrative'] + "\n" + "="*40)
    
    all_pass = check_numeric_accuracy(result['narrative'], findings)
    print(f"Overall Check: {'PASS' if all_pass else 'FAIL'}")
    
    if args.save:
        if result['source'] == 'gemini':
            out_path = repo_root / 'narrator' / 'sample_output.txt'
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(result['narrative'])
            print(f"Saved Gemini output to {out_path}")
        else:
            print("Refusing to save: Source is offline. Only genuine Gemini output should be saved.")

if __name__ == "__main__":
    main()
