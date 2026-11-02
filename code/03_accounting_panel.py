"""
Accounting panel: Tables 6 and 7 of the paper (and the Hausman test and the FE interaction estimate of Section 4.7).

Does ESG Performance Pay Differently for FinTech Firms? Evidence from U.S. FinTech and Non-FinTech Companies, 2021-2025
Sedghiani N, Dogan B (Bahcesehir University)

Usage:  python code/03_accounting_panel.py [path/to/panel_dataset.csv] [output_dir]
        defaults: data/raw/panel_dataset.csv and data/processed

Input: one CSV with one row per firm-quarter and the columns below (names are case-insensitive):
    firm_id         firm identifier (ticker or anonymous id)
    quarter         e.g. 2021Q1
    fintech         1 if the firm is a constituent of at least one of the ten FinTech indices, else 0
    roa             return on assets, percent        (Bloomberg RETURN_ON_ASSET)
    roe             return on common equity, percent (Bloomberg RETURN_COM_EQY)
    pb              price-to-book ratio              (Bloomberg PX_TO_BOOK_RATIO)
    esg_percentile  Bloomberg ESG Score Percentile   (ESG_SCORE_PERCENTILE, 0-100)
    esg_rank        S&P Global ESG Rank              (SP_R_ESG_RANK, 0-100)
    market_cap      market capitalization            (CUR_MKT_CAP)
    total_debt      total debt                       (BS_TOT_LIAB2 or SHORT_AND_LONG_TERM_DEBT)
    total_assets    total assets                     (BS_TOT_ASSET)
Raw Bloomberg data cannot be redistributed, so this file is not part of the repository.

Outputs: table6_main.csv, table7_robustness_roa.csv, fe_interaction_roa.csv, hausman.txt, vif.csv
Requires pandas, numpy, statsmodels; linearmodels only for the Hausman test (optional).
"""
import sys, os
import numpy as np, pandas as pd
import statsmodels.formula.api as smf
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

src = sys.argv[1] if len(sys.argv) > 1 else 'data/raw/panel_dataset.csv'
out = sys.argv[2] if len(sys.argv) > 2 else 'data/processed'
os.makedirs(out, exist_ok=True)

# ---------- 1. data ----------
df = pd.read_csv(src)
df.columns = [c.strip().lower() for c in df.columns]
need = ['firm_id', 'quarter', 'fintech', 'roa', 'roe', 'pb', 'esg_percentile', 'esg_rank', 'market_cap', 'total_debt', 'total_assets']
missing = [c for c in need if c not in df.columns]
if missing:
    raise SystemExit(f'missing columns in {src}: {missing}')
df['quarter'] = df['quarter'].astype(str)
df['fintech'] = df['fintech'].astype(int)
df['avg_esg'] = df[['esg_percentile', 'esg_rank']].mean(axis=1)          # composite ESG (equation 2)
df['esg_x_ft'] = df['avg_esg'] * df['fintech']
df['ln_mcap'] = np.log(df['market_cap'])
df['debt_assets'] = 100 * df['total_debt'] / df['total_assets']          # leverage in percent

def winsorize(s, lo=0.01, hi=0.99):
    return s.clip(s.quantile(lo), s.quantile(hi))

for v in ['roa', 'roe', 'pb']:
    df[v + '_w'] = winsorize(df[v])

def fit(formula, data, clustered=True):
    cols = [t.strip() for t in formula.replace('~', '+').split('+') if t.strip() and not t.strip().startswith('C(')]
    data = data.dropna(subset=cols)
    m = smf.ols(formula, data=data)
    if clustered:
        return m.fit(cov_type='cluster', cov_kwds={'groups': data['firm_id']}), data
    return m.fit(), data

def row(res, data, label, keys):
    r = {'model': label, 'observations': int(res.nobs), 'firms': int(data['firm_id'].nunique()), 'r_squared': float(res.rsquared)}
    for k in keys:
        if k in res.params:
            r[f'{k}_coef'] = float(res.params[k]); r[f'{k}_se'] = float(res.bse[k]); r[f'{k}_p'] = float(res.pvalues[k])
    return r

keys = ['Intercept', 'avg_esg', 'fintech', 'esg_x_ft', 'ln_mcap', 'debt_assets']

# ---------- 2. Table 6: pooled OLS, winsorized DV, leverage control, firm-clustered SE ----------
t6 = []
for dv, label in [('roa_w', 'Model 1: ROA'), ('roe_w', 'Model 2: ROE'), ('pb_w', 'Model 3: P/B ratio')]:
    res, d = fit(f'{dv} ~ avg_esg + fintech + esg_x_ft + ln_mcap + debt_assets', df)
    t6.append(row(res, d, label, keys))
    print(f'\n== {label} ==\n', res.summary().tables[1])
pd.DataFrame(t6).to_csv(f'{out}/table6_main.csv', index=False)

# ---------- 3. Table 7: four specifications for ROA ----------
t7 = []
res, d = fit('roa ~ avg_esg + fintech + esg_x_ft + ln_mcap', df);                      t7.append(row(res, d, '(1) Baseline, clustered SE', keys))
res, d = fit('roa ~ avg_esg + fintech + esg_x_ft + ln_mcap + debt_assets', df);        t7.append(row(res, d, '(2) + Leverage', keys))
res, d = fit('roa_w ~ avg_esg + fintech + esg_x_ft + ln_mcap + debt_assets', df);      t7.append(row(res, d, '(3) Winsorized DV (= Table 6, Model 1)', keys))
res, d = fit('roa ~ avg_esg + fintech + esg_x_ft + ln_mcap', df, clustered=False);     t7.append(row(res, d, '(4) Non-clustered SE', keys))
pd.DataFrame(t7).to_csv(f'{out}/table7_robustness_roa.csv', index=False)
print('\nTable 7 (ROA):\n', pd.DataFrame(t7)[['model', 'esg_x_ft_coef', 'esg_x_ft_se', 'esg_x_ft_p', 'r_squared']].to_string(index=False))

# ---------- 4. Firm fixed effects (within) estimate of the interaction, Section 4.7 ----------
res_fe, d = fit('roa ~ avg_esg + esg_x_ft + ln_mcap + C(firm_id)', df)
fe = {'esg_x_ft_coef': float(res_fe.params['esg_x_ft']), 'esg_x_ft_se': float(res_fe.bse['esg_x_ft']), 'esg_x_ft_p': float(res_fe.pvalues['esg_x_ft']),
      'avg_esg_coef': float(res_fe.params['avg_esg']), 'observations': int(res_fe.nobs), 'firms': int(d['firm_id'].nunique())}
pd.DataFrame([fe]).to_csv(f'{out}/fe_interaction_roa.csv', index=False)
print('\nFE interaction (ROA):', fe)

# ---------- 5. VIF (Section 3.5) ----------
X = sm.add_constant(df[['avg_esg', 'fintech', 'esg_x_ft', 'ln_mcap', 'debt_assets']].dropna())
vif = pd.DataFrame({'variable': X.columns, 'VIF': [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]})
vif[vif.variable != 'const'].to_csv(f'{out}/vif.csv', index=False)
print('\nVIF:\n', vif[vif.variable != 'const'].to_string(index=False))

# ---------- 6. Hausman test, FE vs RE for equation (9) (Section 4.5) ----------
try:
    from linearmodels.panel import PanelOLS, RandomEffects
    p = df.dropna(subset=['roa_w', 'avg_esg', 'esg_x_ft', 'ln_mcap', 'debt_assets']).copy()
    p['t'] = pd.PeriodIndex(p['quarter'], freq='Q').to_timestamp()
    p = p.set_index(['firm_id', 't'])
    X = sm.add_constant(p[['avg_esg', 'esg_x_ft', 'ln_mcap', 'debt_assets']])
    fe_res = PanelOLS(p['roa_w'], X.drop(columns='const'), entity_effects=True).fit()
    re_res = RandomEffects(p['roa_w'], X).fit()
    common = ['avg_esg', 'esg_x_ft', 'ln_mcap', 'debt_assets']
    b_fe, b_re = fe_res.params[common], re_res.params[common]
    V = fe_res.cov.loc[common, common] - re_res.cov.loc[common, common]
    diff = (b_fe - b_re).values
    stat = float(diff @ np.linalg.pinv(V.values) @ diff)
    from scipy import stats
    pval = float(1 - stats.chi2.cdf(stat, len(common)))
    txt = f'Hausman test (FE vs RE), ROA: chi-squared = {stat:.2f}, df = {len(common)}, p = {pval:.4f}\n'
except ImportError:
    txt = 'Hausman test skipped: pip install linearmodels to run it.\n'
open(f'{out}/hausman.txt', 'w').write(txt); print('\n' + txt)
print('done; outputs in', out)
