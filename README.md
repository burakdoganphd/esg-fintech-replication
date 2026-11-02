# Does ESG Performance Pay Differently for FinTech Firms?

Replication package for the paper

> Sedghiani N, Doğan B (2026). *Does ESG Performance Pay Differently for FinTech Firms? Evidence from U.S. FinTech and Non-FinTech Companies, 2021--2025.* Bahçeşehir University. Under review.

The paper compares the constituents of ten Bloomberg FinTech indices with the S&P 500 and with a TradFi group of
traditional financial institutions over 30 November 2021 to 2 October 2025, at the index level (daily returns,
risk-adjusted ratios, ESG indices) and in two quarterly firm-level panels: an accounting panel (ROA, ROE,
price-to-book; Tables 6 and 7) and a market panel with traditional financial institutions as the control group
(quarterly return, volatility, Sharpe ratio; Tables 8 and 9).

## Repository structure

```
esg-fintech-replication/
├── code/
│   ├── 01_index_level_and_market_panel.py   universes, EW/MCW indices, Tables 1-5, A2, A3, market panel (Tables 8-9)
│   ├── 02_make_tables.py                    markdown versions of the tables, as pasted into the manuscript
│   └── 03_accounting_panel.py               accounting panel: Tables 6 and 7, Hausman test, VIF, FE interaction
├── data/
│   ├── raw/                                 Bloomberg exports (NOT included, see data/raw/README.md)
│   └── processed/                           index-level series, ESG indices and every table of the paper (included)
├── docs/
│   ├── Variable_Definitions_Codebook.md     variables, Bloomberg fields, filters and formulas
│   └── Replication_Guide.md                 step-by-step instructions
├── output/tables_md.txt                     the tables in markdown
├── requirements.txt
├── CITATION.cff
└── LICENSE
```

## Data

Raw prices, market capitalizations, ESG ratings and financial statement items come from the Bloomberg Terminal
(S&P Global ESG Rank via Bloomberg) under an institutional license and cannot be redistributed. The repository
therefore contains the processed, index-level outputs only:

- `data/processed/index_returns_EW.csv`, `index_returns_MCW.csv`: daily log returns of the 12 portfolios (964 days)
- `data/processed/esg_index_EW.csv`, `esg_index_MCW.csv`, `esg_index_counts.csv`: quarterly composite ESG indices, 2021-Q4 to 2025-Q3
- `data/processed/table*.csv`, `cumulative_end_levels.csv`, `regression_results_market_panel.csv`, `summary.json`: every number in Tables 1-5, 8, 9, A2 and A3

The firm-quarter panels are not published because they contain firm-level ESG ratings. They can be rebuilt from
the Bloomberg exports with the scripts, and are available from the authors for verification.

## Quick start

```bash
pip install -r requirements.txt
python code/01_index_level_and_market_panel.py data/raw data/processed   # needs the Bloomberg exports in data/raw
python code/02_make_tables.py data/processed output/tables_md.txt
python code/03_accounting_panel.py data/raw/panel_dataset.csv data/processed
```

See `docs/Replication_Guide.md` for the inputs each script expects and `docs/Variable_Definitions_Codebook.md`
for the definitions.

## Sample and definitions in short

- Universe: U.S.-domiciled firms with a closing price on every trading day of the sample.
- FinTech: constituent of at least one of the ten filtered FinTech indices (98 distinct firms).
- TradFi: S&P 500 Financials minus the FinTech-index members, non-U.S. firms and firms without a complete price history (48 firms).
- Indices: equal-weighted (mean of daily log returns) and market-capitalization-weighted (previous-day market caps).
- Risk-adjusted ratios: quarterly annualized Sharpe and Treynor ratios, risk-free rate from the U.S. two-year Treasury yield,
  beta against the S&P 500 portfolio with the same weighting.
- ESG composite: mean of the Bloomberg ESG Score Percentile and the S&P Global ESG Rank.

## Citation

See `CITATION.cff`.

## License

Code: MIT (see `LICENSE`). Documentation: CC BY 4.0. Data: subject to the Bloomberg and S&P Global license terms; not redistributed.

## Contact

Nawres Sedghiani (corresponding author), Graduate School, Bahçeşehir University, nawres.sedghiani@bahcesehir.edu.tr

Burak Doğan, Department of Economics, Bahçeşehir University, burak.dogan@bau.edu.tr
