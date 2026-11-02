"""
Re-run of the index-level and market-panel methodology for the ESG-FinTech paper, from the raw Bloomberg exports.

Does ESG Performance Pay Differently for FinTech Firms? Evidence from U.S. FinTech and Non-FinTech Companies, 2021-2025
Sedghiani N, Dogan B (Bahcesehir University)

Usage:  python code/01_index_level_and_market_panel.py [data_directory] [output_directory]
        defaults: data/raw and data/processed
The data directory must contain the Bloomberg export workbooks described in data/raw/README.md
(file names may carry a date prefix):
  *Original_Price_Data.xlsx, *Original_Marketcap_Data.xlsx, *Original_Time_and_Country_Restrictions.xlsx,
  *BD_v4.xlsx (sheets EW and Risk-free), *ESG.xlsx
Outputs: CSV files and summary.json in the output directory (Tables 1-5, 8, 9, A2, A3 of the paper).
Requires pandas, numpy, scipy, statsmodels, openpyxl.
"""
import pandas as pd, numpy as np, json, os, re, sys, glob, warnings
from scipy import stats
warnings.filterwarnings("ignore")
A = (sys.argv[1] if len(sys.argv) > 1 else 'data/raw').rstrip('/') + '/'
OUT = (sys.argv[2] if len(sys.argv) > 2 else 'data/processed').rstrip('/'); os.makedirs(OUT, exist_ok=True)
IDX = ['UBXXFINT', 'MLFINTEC', 'BIGLFPVP', 'JP2PMT', 'BEFAP', 'BFPAT', 'FGFBIP', 'SOLFINT', 'BFNQ', 'BEFFP']
ORDER = ['SPX'] + IDX + ['TradFi']
base = lambda s: str(s).split()[0]

def find(pattern):
    hits = sorted(glob.glob(os.path.join(A, '*' + pattern)))
    if not hits:
        raise SystemExit(f'file not found in {A}: *{pattern}')
    return hits[0]

def load_wide(path):
    """One sheet per index: first row = tickers, first column = dates; non-date rows (flags) are dropped."""
    x = pd.ExcelFile(path); out = {}
    for sh in x.sheet_names:
        df = x.parse(sh, header=None)
        cols = df.iloc[0].tolist()
        body = df.iloc[1:]
        body = body[pd.to_datetime(body[0], errors='coerce').notna()]
        d = body.set_index(pd.to_datetime(body[0])).drop(columns=[0])
        d.columns = [str(c).strip() for c in cols[1:]]
        d = d.apply(pd.to_numeric, errors='coerce'); d.index.name = 'Date'
        out[sh.strip()] = d
    return out

# ---------- 1. raw data ----------
prices = load_wide(find('Original_Price_Data.xlsx'))
mcaps = load_wide(find('Original_Marketcap_Data.xlsx'))
bd_file = find('BD_v4.xlsx')
dates = pd.DatetimeIndex(pd.to_datetime(pd.read_excel(bd_file, sheet_name='EW')['Date']))   # 964 trading days, 2021-11-30 .. 2025-10-02
first_day = prices['SPX'].index[prices['SPX'].index < dates[0]].max()   # 2021-11-29 (base day for the first return)
win = [first_day] + list(dates)

restr = pd.read_excel(find('Original_Time_and_Country_Restrictions.xlsx'),
                      sheet_name='Time+Country restriction', header=None)
country = {}
c = 0
while c < restr.shape[1]:
    name = restr.iloc[0, c]
    if isinstance(name, str) and name.strip():
        sub = restr.iloc[1:, c:c + 3].dropna(subset=[c])
        for t, _, co in sub.itertuples(index=False):
            country[t] = co
    c += 4

# risk-free: US 2-year Treasury yield (annual, decimal) -> daily
rf = pd.read_excel(bd_file, sheet_name='Risk-free')
rf['Date'] = pd.to_datetime(rf['Date']); rf = rf.set_index('Date')['US2Y'].astype(float)
rf_d = ((1 + rf) ** (1 / 252) - 1).reindex(dates).ffill()

# ---------- 2. universes: U.S.-listed and complete price history over the window ----------
def universe(name):
    p = prices[name].reindex(win)
    ok = [t for t in p.columns if country.get(t) == 'US' and p[t].notna().all()]
    return ok
uni = {n: universe(n) for n in ['SPX'] + IDX}
# TradFi: the 71 S&P 500 financials listed in ESG.xlsx (matched on base ticker), same filters, minus FinTech-index members
esg_nf = pd.read_excel(find('ESG.xlsx'), sheet_name='Nonficntech', header=None)
nf_tickers = [t for t in esg_nf.iloc[3, 1:].tolist() if isinstance(t, str)]
spx_by_base = {base(t): t for t in prices['SPX'].columns}
tradfi_all = [spx_by_base[base(t)] for t in nf_tickers if base(t) in spx_by_base]
# a firm is FinTech if it is in at least one (filtered) FinTech index; such firms are removed from TradFi
fintech_bases = set(base(t) for n in IDX for t in uni[n])
tradfi_filtered = [t for t in tradfi_all if t in uni['SPX']]
uni['TradFi'] = [t for t in tradfi_filtered if base(t) not in fintech_bases]
removed_from_tradfi = [base(t) for t in tradfi_filtered if base(t) in fintech_bases]
counts = {n: len(v) for n, v in uni.items()}
print('universe sizes:', counts, '| TradFi listed/matched/filtered:', len(nf_tickers), len(tradfi_all), len(tradfi_filtered),
      '| removed because in a FinTech index:', removed_from_tradfi)
print('distinct FinTech firms:', len(fintech_bases))

# ---------- 3. daily log returns and indices ----------
def logret(name):
    p = prices[name].reindex(win)[uni[name]]
    return np.log(p / p.shift(1)).reindex(dates)
R = {n: logret(n) for n in ['SPX'] + IDX}
R['TradFi'] = R['SPX'][uni['TradFi']]
M = {n: mcaps[n].reindex(win).ffill() for n in ['SPX'] + IDX}   # carry the last market cap over days missing in the export
M['TradFi'] = M['SPX']
EW, MCW = {}, {}
for n in ORDER:
    r = R[n]
    EW[n] = r.mean(axis=1)
    src = 'SPX' if n == 'TradFi' else n
    Ms = M[src]; w = Ms.shift(1).fillna(Ms).reindex(dates)[uni[n]].where(r.notna())   # previous-day market cap as weight (same-day on the first day)
    MCW[n] = (r * w).sum(axis=1) / w.sum(axis=1)
EW = pd.DataFrame(EW); MCW = pd.DataFrame(MCW)
EW.to_csv(f'{OUT}/index_returns_EW.csv'); MCW.to_csv(f'{OUT}/index_returns_MCW.csv')

# ---------- 4. Table 1: descriptive statistics ----------
def desc(df):
    out = pd.DataFrame(index=['Mean', 'Median', 'Std. dev.', 'Minimum', 'Maximum', 'Skewness', 'Kurtosis'])
    for c in df.columns:
        x = df[c].dropna()
        out[c] = [x.mean(), x.median(), x.std(ddof=1), x.min(), x.max(),
                  stats.skew(x, bias=False), stats.kurtosis(x, bias=False)]   # Excel-style sample skew / excess kurtosis
    return out
T1 = pd.concat({'EW': desc(EW), 'MCW': desc(MCW)}); T1.to_csv(f'{OUT}/table1_descriptives.csv')

# ---------- 5. Table 2: correlations; cumulative returns ----------
C_EW = EW.corr(); C_MCW = MCW.corr()
C_EW.to_csv(f'{OUT}/table2_corr_EW.csv'); C_MCW.to_csv(f'{OUT}/table2_corr_MCW.csv')
cum_EW = 100 * np.exp(EW.cumsum()); cum_MCW = 100 * np.exp(MCW.cumsum())
cum_end = pd.DataFrame({'EW': cum_EW.iloc[-1], 'MCW': cum_MCW.iloc[-1]}); cum_end.to_csv(f'{OUT}/cumulative_end_levels.csv')
maxdd = {}
for n in ORDER:
    lvl = cum_EW[n]; maxdd[n] = float((lvl / lvl.cummax() - 1).min())
# ---------- 6. Tables 3, A2, A3: quarterly Sharpe and Treynor ----------
q = pd.PeriodIndex(dates, freq='Q')
quarters = [p for p in sorted(set(q)) if str(p) >= '2022Q1' and str(p) <= '2025Q3']
def qstats(df, mkt):
    sh = pd.DataFrame(index=[str(p).replace('Q', '-Q') for p in quarters], columns=df.columns, dtype=float)
    tr = sh.copy(); beta = sh.copy()
    for p in quarters:
        sel = (q == p)
        ex = df[sel].sub(rf_d[sel], axis=0)
        mex = df[mkt][sel] - rf_d[sel]
        for c in df.columns:
            e = ex[c]
            sh.loc[str(p).replace('Q', '-Q'), c] = e.mean() / e.std(ddof=1) * np.sqrt(252)
            b = np.cov(e, mex, ddof=1)[0, 1] / mex.var(ddof=1)
            beta.loc[str(p).replace('Q', '-Q'), c] = b
            tr.loc[str(p).replace('Q', '-Q'), c] = e.mean() * 252 / b
    return sh, tr, beta
SH_EW, TR_EW, B_EW = qstats(EW, 'SPX'); SH_MCW, TR_MCW, B_MCW = qstats(MCW, 'SPX')
for name, df in [('A2_sharpe_EW', SH_EW), ('A2_sharpe_MCW', SH_MCW), ('A3_treynor_EW', TR_EW), ('A3_treynor_MCW', TR_MCW), ('beta_EW', B_EW), ('beta_MCW', B_MCW)]:
    df.to_csv(f'{OUT}/table_{name}.csv')
T3 = pd.DataFrame({'Sharpe_EW': SH_EW.mean(), 'Treynor_EW': TR_EW.mean(), 'Sharpe_MCW': SH_MCW.mean(), 'Treynor_MCW': TR_MCW.mean()})
T3.to_csv(f'{OUT}/table3_risk_adjusted_averages.csv')

# ---------- 7. Table 4: normality, paired t-tests and Wilcoxon on daily returns ----------
jb = {}
for scheme, df in [('EW', EW), ('MCW', MCW)]:
    for c in df.columns:
        s, pv = stats.jarque_bera(df[c].dropna()); jb[f'{scheme}:{c}'] = (float(s), float(pv))
def pairtests(df):
    tt = pd.DataFrame(index=['SPX', 'TradFi'], columns=df.columns, dtype=float); wx = tt.copy()
    for b in ['SPX', 'TradFi']:
        for c in df.columns:
            if c == b: continue
            x = df[b]; y = df[c]
            tt.loc[b, c] = stats.ttest_rel(x, y).pvalue
            wx.loc[b, c] = stats.wilcoxon(x, y).pvalue
    return tt, wx
T4t_EW, T4w_EW = pairtests(EW); T4t_MCW, T4w_MCW = pairtests(MCW)
for name, df in [('4_ttest_EW', T4t_EW), ('4_wilcoxon_EW', T4w_EW), ('4_ttest_MCW', T4t_MCW), ('4_wilcoxon_MCW', T4w_MCW)]:
    df.to_csv(f'{OUT}/table_{name}.csv')

# ---------- 8. ESG indices (quarterly) ----------
def read_esg(sheet):
    df = pd.read_excel(find('ESG.xlsx'), sheet_name=sheet, header=None)
    tick_row = df.iloc[3, :].tolist(); field_row = df.iloc[5, :].tolist()
    data = df.iloc[6:, :].copy(); data = data[data[0].notna()]
    qdates = pd.to_datetime(data[0]); data = data.iloc[:, 1:]
    recs = []
    cur = None
    for j in range(1, df.shape[1]):
        if isinstance(tick_row[j], str): cur = tick_row[j]
        f = field_row[j]
        if cur is None or not isinstance(f, str): continue
        col = pd.to_numeric(df.iloc[6:6 + len(qdates), j], errors='coerce').values
        for d, v in zip(qdates, col):
            recs.append((cur, d, f, v))
    long = pd.DataFrame(recs, columns=['ticker', 'qdate', 'field', 'value'])
    wide = long.pivot_table(index=['ticker', 'qdate'], columns='field', values='value', aggfunc='first').reset_index()
    wide['base'] = wide['ticker'].map(base)
    wide['composite'] = wide[['ESG_SCORE_PERCENTILE', 'SP_R_ESG_RANK']].mean(axis=1)   # mean of the available indicators
    return wide, [t for t in tick_row if isinstance(t, str)]
esg_ft, ft_order = read_esg('Fintech'); esg_tf, tf_order = read_esg('Nonficntech')
# the Fintech sheet lists tickers index by index, in the same order and counts as the filtered constituents
pos = 0; ft_members = {}
for n in IDX:
    k = len(uni[n]) if False else None
flag_counts = {'UBXXFINT': 25, 'MLFINTEC': 38, 'BIGLFPVP': 16, 'JP2PMT': 19, 'BEFAP': 45, 'BFPAT': 74, 'FGFBIP': 40, 'SOLFINT': 32, 'BFNQ': 33, 'BEFFP': 37}
for n in IDX:
    ft_members[n] = ft_order[pos:pos + flag_counts[n]]; pos += flag_counts[n]
assert pos == len(ft_order) == 359
# sanity: membership from the ESG sheet vs our price-based universe (base tickers)
for n in IDX:
    a = set(base(t) for t in ft_members[n]); b = set(base(t) for t in uni[n])
    if a != b: print(f'  note {n}: ESG-sheet members {len(a)}, price universe {len(b)}, overlap {len(a & b)}')
esg_ft = esg_ft.drop_duplicates(['base', 'qdate'])
esg_tf = esg_tf.drop_duplicates(['base', 'qdate'])
qd = sorted(esg_ft['qdate'].unique())
def esg_index(members_base, table):
    sub = table[table['base'].isin(members_base)]
    g = sub.groupby('qdate')
    ew = g['composite'].mean()
    def mcw(x):
        x = x.dropna(subset=['composite', 'CUR_MKT_CAP'])
        return np.nan if x['CUR_MKT_CAP'].sum() == 0 else (x['composite'] * x['CUR_MKT_CAP']).sum() / x['CUR_MKT_CAP'].sum()
    mc = g.apply(mcw)
    n = g['composite'].count()
    return ew, mc, n
ESG_EW, ESG_MCW, ESG_N = {}, {}, {}
for n in IDX:
    ESG_EW[n], ESG_MCW[n], ESG_N[n] = esg_index(set(base(t) for t in uni[n]), esg_ft)
ESG_EW['TradFi'], ESG_MCW['TradFi'], ESG_N['TradFi'] = esg_index(set(base(t) for t in uni['TradFi']), esg_tf)
ESG_EW = pd.DataFrame(ESG_EW); ESG_MCW = pd.DataFrame(ESG_MCW); ESG_N = pd.DataFrame(ESG_N)
# keep quarters inside the return sample (2021-12-31 .. 2025-09-30)
ESG_EW = ESG_EW[(ESG_EW.index >= '2021-12-31') & (ESG_EW.index <= '2025-09-30')]
ESG_MCW = ESG_MCW.loc[ESG_EW.index]; ESG_N = ESG_N.loc[ESG_EW.index]
ESG_EW.to_csv(f'{OUT}/esg_index_EW.csv'); ESG_MCW.to_csv(f'{OUT}/esg_index_MCW.csv'); ESG_N.to_csv(f'{OUT}/esg_index_counts.csv')
T5 = pd.concat({'EW': pd.DataFrame({'Mean': ESG_EW.mean(), 'Median': ESG_EW.median(), 'Std. dev.': ESG_EW.std(ddof=1)}).T,
                'MCW': pd.DataFrame({'Mean': ESG_MCW.mean(), 'Median': ESG_MCW.median(), 'Std. dev.': ESG_MCW.std(ddof=1)}).T})
T5.to_csv(f'{OUT}/table5_esg.csv')
esg_t = {}
for scheme, df in [('EW', ESG_EW), ('MCW', ESG_MCW)]:
    for n in IDX:
        x = pd.concat([df[n], df['TradFi']], axis=1).dropna()
        esg_t[f'{scheme}:{n}'] = float(stats.ttest_rel(x.iloc[:, 0], x.iloc[:, 1]).pvalue)
esg_corr_EW = ESG_EW.corr(); esg_corr_EW.to_csv(f'{OUT}/esg_corr_EW.csv')

# ---------- 9. firm-level quarterly panel: FinTech vs TradFi ----------
# daily returns for every FinTech firm (unique base ticker) and every TradFi firm
firm_ret = {}
for n in IDX:
    for t in uni[n]:
        firm_ret.setdefault(base(t), R[n][t])
for t in uni['TradFi']:
    firm_ret[base(t)] = R['TradFi'][t]
firm_ret = pd.DataFrame(firm_ret)
is_ft = {b: 1 for n in IDX for b in map(base, uni[n])}
for t in uni['TradFi']: is_ft.setdefault(base(t), 0)
qper = pd.PeriodIndex(firm_ret.index, freq='Q')
ex = firm_ret.sub(rf_d, axis=0)
rows = []
for p in sorted(set(qper)):
    sel = (qper == p)
    if sel.sum() < 40: continue
    rq = firm_ret[sel]; eq = ex[sel]
    for b in firm_ret.columns:
        rows.append(dict(firm=b, quarter=str(p), ret=rq[b].sum() * 100, vol=rq[b].std(ddof=1) * np.sqrt(252) * 100,
                         sharpe=eq[b].mean() / rq[b].std(ddof=1) * np.sqrt(252), fintech=is_ft[b]))
panel = pd.DataFrame(rows)
esg_all = pd.concat([esg_ft, esg_tf]).drop_duplicates(['base', 'qdate'])
esg_all['quarter'] = pd.PeriodIndex(esg_all['qdate'], freq='Q').astype(str)
esg_all['ln_mcap'] = np.log(esg_all['CUR_MKT_CAP'])
# lag: ESG and size observed at the end of the previous quarter
esg_all['quarter_next'] = (pd.PeriodIndex(esg_all['qdate'], freq='Q') + 1).astype(str)
lagged = esg_all[['base', 'quarter_next', 'composite', 'ln_mcap', 'ESG_SCORE_PERCENTILE', 'SP_R_ESG_RANK']].rename(
    columns={'base': 'firm', 'quarter_next': 'quarter', 'composite': 'esg_lag', 'ln_mcap': 'lnmcap_lag'})
panel = panel.merge(lagged, on=['firm', 'quarter'], how='left')
contemp = esg_all[['base', 'quarter', 'composite']].rename(columns={'base': 'firm', 'composite': 'esg_now'})
panel = panel.merge(contemp, on=['firm', 'quarter'], how='left')
panel = panel[panel['quarter'] >= '2022Q1'].copy()
panel.to_csv(f'{OUT}/firm_quarter_panel.csv', index=False)

import statsmodels.formula.api as smf
def wins(s, lo=0.01, hi=0.99):
    a, b = s.quantile(lo), s.quantile(hi); return s.clip(a, b)
reg = panel.dropna(subset=['esg_lag', 'lnmcap_lag']).copy()
for v in ['ret', 'vol', 'sharpe']: reg[v + '_w'] = wins(reg[v])
reg['esg_x_ft'] = reg['esg_lag'] * reg['fintech']
results = {}
def fit(formula, data, label):
    m = smf.ols(formula, data=data).fit(cov_type='cluster', cov_kwds={'groups': data['firm']})
    keep = ['esg_lag', 'fintech', 'esg_x_ft', 'lnmcap_lag']
    results[label] = {k: (float(m.params[k]), float(m.bse[k]), float(m.pvalues[k])) for k in keep if k in m.params}
    results[label]['nobs'] = int(m.nobs); results[label]['firms'] = int(data['firm'].nunique()); results[label]['r2'] = float(m.rsquared)
    return m
for dv in ['ret_w', 'vol_w', 'sharpe_w']:
    fit(f'{dv} ~ esg_lag + fintech + esg_x_ft + lnmcap_lag + C(quarter)', reg, f'{dv}:pooled_qFE')
    fit(f'{dv} ~ esg_lag + esg_x_ft + lnmcap_lag + C(quarter) + C(firm)', reg, f'{dv}:firmFE_qFE')
# sub-periods
for lab, cond in [('2022-2023', reg['quarter'] <= '2023Q4'), ('2024-2025', reg['quarter'] >= '2024Q1')]:
    fit('ret_w ~ esg_lag + fintech + esg_x_ft + lnmcap_lag + C(quarter)', reg[cond], f'ret_w:pooled_qFE:{lab}')
# contemporaneous ESG for comparison
reg2 = panel.dropna(subset=['esg_now', 'lnmcap_lag']).copy(); reg2['ret_w'] = wins(reg2['ret']); reg2['esg_x_ft'] = reg2['esg_now'] * reg2['fintech']
m = smf.ols('ret_w ~ esg_now + fintech + esg_x_ft + lnmcap_lag + C(quarter)', data=reg2).fit(cov_type='cluster', cov_kwds={'groups': reg2['firm']})
results['ret_w:pooled_qFE:contemporaneous'] = {k: (float(m.params[k]), float(m.bse[k]), float(m.pvalues[k])) for k in ['esg_now', 'fintech', 'esg_x_ft', 'lnmcap_lag']}
results['ret_w:pooled_qFE:contemporaneous'].update(nobs=int(m.nobs), firms=int(reg2['firm'].nunique()), r2=float(m.rsquared))
# long-format export of the regression results (Tables 8 and 9)
rows_out = []
for lab, res in results.items():
    for k, v in res.items():
        if isinstance(v, tuple) or isinstance(v, list):
            rows_out.append(dict(specification=lab, variable=k, coef=v[0], se=v[1], p=v[2]))
        else:
            rows_out.append(dict(specification=lab, variable=k, coef=v, se=np.nan, p=np.nan))
pd.DataFrame(rows_out).to_csv(f'{OUT}/regression_results_market_panel.csv', index=False)
# descriptives of the firm panel
pdesc = reg.groupby('fintech')[['ret', 'vol', 'sharpe', 'esg_lag', 'lnmcap_lag']].agg(['mean', 'std', 'count'])
pdesc.to_csv(f'{OUT}/firm_panel_descriptives.csv')

summary = dict(counts=counts, n_days=int(len(dates)), first_day=str(dates[0].date()), last_day=str(dates[-1].date()),
               quarters=[str(p) for p in quarters], jb=jb, esg_ttest_vs_TradFi=esg_t, maxdd_EW=maxdd,
               regressions=results, panel_firms=int(reg['firm'].nunique()), panel_obs=int(len(reg)),
               panel_fintech_firms=int(reg[reg.fintech == 1]['firm'].nunique()), panel_tradfi_firms=int(reg[reg.fintech == 0]['firm'].nunique()),
               esg_quarters=[str(d.date()) for d in ESG_EW.index])
json.dump(summary, open(f'{OUT}/summary.json', 'w'), indent=1, default=str)
print('done')
