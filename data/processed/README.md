# `data/processed/` — outputs of the scripts (included)

All files are produced by `code/01_index_level_and_market_panel.py` from the Bloomberg exports, except where noted.
They are index-level or aggregated and contain no firm-level licensed data.

| File | Content | Paper |
|---|---|---|
| `index_returns_EW.csv`, `index_returns_MCW.csv` | Daily log returns of the 12 portfolios (SPX, ten FinTech indices, TradFi), 964 trading days | Section 3.2 |
| `table1_descriptives.csv` | Mean, median, standard deviation, minimum, maximum, skewness, excess kurtosis, EW and MCW | Table 1 |
| `table2_corr_EW.csv`, `table2_corr_MCW.csv` | Full Pearson correlation matrices of daily returns | Table 2 |
| `cumulative_end_levels.csv` | Level of 100 invested on 30 Nov 2021 at the end of the sample | Section 4.2 |
| `table3_risk_adjusted_averages.csv` | Average quarterly annualized Sharpe and Treynor ratios, 2022-Q1 to 2025-Q3 | Table 3 |
| `table_A2_sharpe_EW.csv`, `table_A2_sharpe_MCW.csv` | Quarterly Sharpe ratios | Table A2 |
| `table_A3_treynor_EW.csv`, `table_A3_treynor_MCW.csv` | Quarterly Treynor ratios | Table A3 |
| `table_beta_EW.csv`, `table_beta_MCW.csv` | Quarterly betas against the S&P 500 portfolio with the same weighting | equation (4) |
| `table_4_ttest_*.csv`, `table_4_wilcoxon_*.csv` | p-values of paired t-tests and Wilcoxon signed-rank tests against SPX and TradFi | Table 4 |
| `esg_index_EW.csv`, `esg_index_MCW.csv`, `esg_index_counts.csv` | Quarterly composite ESG indices and the number of rated constituents, 2021-Q4 to 2025-Q3 | Table 5 |
| `table5_esg.csv`, `esg_corr_EW.csv` | Descriptive statistics and correlations of the ESG indices | Table 5 |
| `regression_results_market_panel.csv` | Coefficients, clustered standard errors and p-values of the market-panel regressions | Tables 8 and 9 |
| `firm_panel_descriptives.csv` | Means, standard deviations and counts of the market-panel variables by group | Section 4.8 |
| `summary.json` | Universe sizes, sample dates, Jarque-Bera tests, maximum drawdowns, ESG paired t-tests, all regressions | throughout |

Not included: `firm_quarter_panel.csv` (the firm-quarter market panel, written by the script) and
`panel_dataset.csv` (the accounting panel), because they contain firm-level ESG ratings. Both are available from
the authors for verification. `code/03_accounting_panel.py` writes `table6_main.csv`, `table7_robustness_roa.csv`,
`fe_interaction_roa.csv`, `vif.csv` and `hausman.txt` into this folder when the accounting panel is available.
