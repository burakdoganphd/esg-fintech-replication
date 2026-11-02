"""Build the markdown table blocks of the manuscript from the processed outputs.

Usage:  python code/02_make_tables.py [processed_directory] [output_file]
        defaults: data/processed and output/tables_md.txt  (run after code/01_index_level_and_market_panel.py)
"""
import pandas as pd, numpy as np, json, sys, os
R = (sys.argv[1] if len(sys.argv) > 1 else 'data/processed').rstrip('/') + '/'
ORDER = ['SPX', 'UBXXFINT', 'MLFINTEC', 'BIGLFPVP', 'JP2PMT', 'BEFAP', 'BFPAT', 'FGFBIP', 'SOLFINT', 'BFNQ', 'BEFFP', 'TradFi']
IDX = ORDER[1:-1]
out = []

def f(x, d):
    if pd.isna(x): return ''
    return f'{x:.{d}f}'

def header(first, cols):
    return [f'| {first} | ' + ' | '.join(cols) + ' |', '|:------------|' + '-----:|' * len(cols)]

def panel(label, ncols):
    return f'| *{label}* |' + ' |' * ncols

# ---- Table 1 ----
t1 = pd.read_csv(R + 'table1_descriptives.csv', index_col=[0, 1])
rows = header('Statistic', ORDER)
for scheme, lab in [('EW', 'Panel A: EW'), ('MCW', 'Panel B: MCW')]:
    rows.append(panel(lab, len(ORDER)))
    for stat in ['Mean', 'Median', 'Std. dev.', 'Minimum', 'Maximum', 'Skewness', 'Kurtosis']:
        rows.append(f'| {stat} | ' + ' | '.join(f(t1.loc[(scheme, stat), c], 4) for c in ORDER) + ' |')
out.append('<<T1>>\n' + '\n'.join(rows))

# ---- Table 2 ----
rows = header('Index', ORDER)
for scheme, lab in [('EW', 'Panel A: EW'), ('MCW', 'Panel B: MCW')]:
    c2 = pd.read_csv(R + f'table2_corr_{scheme}.csv', index_col=0)
    rows.append(panel(lab, len(ORDER)))
    for r in ['SPX', 'UBXXFINT', 'TradFi']:
        rows.append(f'| {r} | ' + ' | '.join(f(c2.loc[r, c], 2) for c in ORDER) + ' |')
out.append('<<T2>>\n' + '\n'.join(rows))

# ---- Table 3 ----
t3 = pd.read_csv(R + 'table3_risk_adjusted_averages.csv', index_col=0)
rows = header('Metric', ORDER)
for scheme, lab in [('EW', 'Panel A: EW'), ('MCW', 'Panel B: MCW')]:
    rows.append(panel(lab, len(ORDER)))
    rows.append('| Avg. Sharpe | ' + ' | '.join(f(t3.loc[c, f'Sharpe_{scheme}'], 3) for c in ORDER) + ' |')
    rows.append('| Avg. Treynor | ' + ' | '.join(f(t3.loc[c, f'Treynor_{scheme}'], 3) for c in ORDER) + ' |')
out.append('<<T3>>\n' + '\n'.join(rows))

# ---- Table 4 ----
rows = header('Benchmark / test', ORDER)
for scheme, lab in [('EW', 'Panel A: EW'), ('MCW', 'Panel B: MCW')]:
    rows.append(panel(lab, len(ORDER)))
    tt = pd.read_csv(R + f'table_4_ttest_{scheme}.csv', index_col=0)
    wx = pd.read_csv(R + f'table_4_wilcoxon_{scheme}.csv', index_col=0)
    for b in ['SPX', 'TradFi']:
        for name, df in [('paired t', tt), ('Wilcoxon', wx)]:
            rows.append(f'| {b}, {name} | ' + ' | '.join('--' if c == b else f(df.loc[b, c], 2) for c in ORDER) + ' |')
out.append('<<T4>>\n' + '\n'.join(rows))

# ---- Table 5 ----
t5 = pd.read_csv(R + 'table5_esg.csv', index_col=[0, 1])
cols5 = IDX + ['TradFi']
rows = header('Statistic', cols5)
for scheme, lab in [('EW', 'Panel A: EW'), ('MCW', 'Panel B: MCW')]:
    rows.append(panel(lab, len(cols5)))
    for stat in ['Mean', 'Median', 'Std. dev.']:
        rows.append(f'| {stat} | ' + ' | '.join(f(t5.loc[(scheme, stat), c], 2) for c in cols5) + ' |')
out.append('<<T5>>\n' + '\n'.join(rows))

# ---- Tables A2, A3 ----
for key, stem in [('A2', 'table_A2_sharpe'), ('A3', 'table_A3_treynor')]:
    rows = header('Quarter', ORDER)
    for scheme, lab in [('EW', 'Panel A: EW'), ('MCW', 'Panel B: MCW')]:
        q = pd.read_csv(R + f'{stem}_{scheme}.csv', index_col=0)
        rows.append(panel(lab, len(ORDER)))
        for qq in q.index:
            rows.append(f'| {qq} | ' + ' | '.join(f(q.loc[qq, c], 3) for c in ORDER) + ' |')
    out.append(f'<<{key}>>\n' + '\n'.join(rows))

# ---- Tables 8 and 9 ----
S = json.load(open(R + 'summary.json'))
reg = S['regressions']
def cell(res, k, d=3):
    if k not in res: return ''
    b, se, p = res[k]
    stars = '\\*\\*\\*' if p < 0.01 else '\\*\\*' if p < 0.05 else '\\*' if p < 0.10 else ''
    return f'{b:.{d}f}{stars} ({se:.{d}f})'
specs = [('ret_w:pooled_qFE', '(1) Return'), ('ret_w:firmFE_qFE', '(2) Return'), ('vol_w:pooled_qFE', '(3) Volatility'),
         ('vol_w:firmFE_qFE', '(4) Volatility'), ('sharpe_w:pooled_qFE', '(5) Sharpe'), ('sharpe_w:firmFE_qFE', '(6) Sharpe')]
rows = ['| | ' + ' | '.join(h for _, h in specs) + ' |', '|:-------------------|' + ':-----------:|' * len(specs)]
for k, lab in [('esg_lag', 'ESG (t-1)'), ('fintech', 'FinTech'), ('esg_x_ft', 'ESG (t-1) × FinTech'), ('lnmcap_lag', 'ln(MarketCap) (t-1)')]:
    rows.append(f'| {lab} | ' + ' | '.join(cell(reg[s], k) for s, _ in specs) + ' |')
rows.append('| Quarter effects | ' + ' | '.join('Yes' for _ in specs) + ' |')
rows.append('| Firm effects | ' + ' | '.join('Yes' if 'firmFE' in s else 'No' for s, _ in specs) + ' |')
rows.append('| Observations | ' + ' | '.join(f"{reg[s]['nobs']:,}" for s, _ in specs) + ' |')
rows.append('| Firms | ' + ' | '.join(str(reg[s]['firms']) for s, _ in specs) + ' |')
rows.append('| R-squared | ' + ' | '.join(f"{reg[s]['r2']:.3f}" for s, _ in specs) + ' |')
out.append('<<T8>>\n' + '\n'.join(rows))

specs9 = [('ret_w:pooled_qFE', '(1) 2022-Q1 to 2025-Q3'), ('ret_w:pooled_qFE:2022-2023', '(2) 2022-Q1 to 2023-Q4'),
          ('ret_w:pooled_qFE:2024-2025', '(3) 2024-Q1 to 2025-Q3'), ('ret_w:pooled_qFE:contemporaneous', '(4) Contemporaneous ESG')]
rows = ['| | ' + ' | '.join(h for _, h in specs9) + ' |', '|:-------------------|' + ':-----------:|' * len(specs9)]
rows.append('| ESG (t-1) | ' + ' | '.join(cell(reg[s], 'esg_lag') for s, _ in specs9) + ' |')
rows.append('| ESG (t) | ' + ' | '.join(cell(reg[s], 'esg_now') for s, _ in specs9) + ' |')
for k, lab in [('fintech', 'FinTech'), ('esg_x_ft', 'ESG × FinTech'), ('lnmcap_lag', 'ln(MarketCap) (t-1)')]:
    rows.append(f'| {lab} | ' + ' | '.join(cell(reg[s], k) for s, _ in specs9) + ' |')
rows.append('| Observations | ' + ' | '.join(f"{reg[s]['nobs']:,}" for s, _ in specs9) + ' |')
rows.append('| R-squared | ' + ' | '.join(f"{reg[s]['r2']:.3f}" for s, _ in specs9) + ' |')
out.append('<<T9>>\n' + '\n'.join(rows))

dst = sys.argv[2] if len(sys.argv) > 2 else 'output/tables_md.txt'
os.makedirs(os.path.dirname(dst) or '.', exist_ok=True)
open(dst, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print('written', dst)
