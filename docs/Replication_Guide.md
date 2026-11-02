# Replication guide

## Requirements

- Python 3.10 or later and the packages in `requirements.txt` (`pip install -r requirements.txt`).
  `linearmodels` is only needed for the Hausman test in step 3.
- Access to a Bloomberg Terminal (with the ESG fields) to export the raw data; the exports stay in `data/raw/`
  and are never committed.

## Step 1: index level and market panel (Tables 1-5, 8, 9, A2, A3)

Place the five Bloomberg workbooks described in `data/raw/README.md` in `data/raw/`, then run

```bash
python code/01_index_level_and_market_panel.py data/raw data/processed
```

The script

1. reads prices, market capitalizations, the country restriction list, the trading-day calendar and the two-year Treasury yield;
2. applies the two filters (U.S. domicile, complete price history) and builds the universes; prints the universe sizes and the
   firms removed from TradFi because they belong to a FinTech index;
3. computes daily log returns and the EW and MCW indices (equation 1), Table 1, the correlation matrices (Table 2), the
   cumulative levels and maximum drawdowns;
4. computes quarterly annualized Sharpe and Treynor ratios (equations 3 and 4) and their averages (Table 3, Tables A2 and A3);
5. runs Jarque-Bera, paired t and Wilcoxon tests (Table 4);
6. builds the composite ESG score (equation 2) and the EW and MCW ESG indices with paired t-tests against TradFi (Table 5);
7. builds the firm-quarter market panel and estimates equation (10) with quarter effects and with quarter and firm effects,
   the two sub-periods and the contemporaneous-rating version (Tables 8 and 9).

Runtime is about ten seconds. Outputs go to `data/processed/` (see the README there). The run that produced the
numbers in the paper is the one committed in `data/processed/`.

## Step 2: tables in markdown

```bash
python code/02_make_tables.py data/processed output/tables_md.txt
```

writes the blocks `<<T1>>` to `<<T9>>`, `<<A2>>` and `<<A3>>` exactly as they appear in the manuscript.

## Step 3: accounting panel (Tables 6 and 7)

Export the quarterly fundamentals and ESG fields for the accounting panel into `data/raw/panel_dataset.csv`
(column list in `data/raw/README.md`), then run

```bash
python code/03_accounting_panel.py data/raw/panel_dataset.csv data/processed
```

It builds the composite ESG, the interaction, log market capitalization and leverage, winsorizes the dependent
variables, and writes Table 6 (pooled OLS, firm-clustered standard errors), the four Table 7 specifications for ROA,
the firm fixed-effects estimate of the interaction, the VIFs and the Hausman test.

## Checking the numbers

- `data/processed/summary.json` holds every regression coefficient, standard error and p-value, the universe sizes,
  the Jarque-Bera statistics, the maximum drawdowns and the ESG t-tests.
- `output/tables_md.txt` is what was pasted into the manuscript; differences at the last decimal between operating
  systems are possible for the regressions.

## Notes on the method

- MCW weights use the market capitalization of the previous trading day, so a day's own return does not enter its weight.
- The sample begins on 30 November 2021, so 2021-Q4 is incomplete; the ratio averages use the 15 complete quarters
  2022-Q1 to 2025-Q3.
- The TradFi group excludes every FinTech-index member (including incumbents such as JPM, ICE, NDAQ, MSCI, COIN or HOOD
  that the broad FinTech indices hold), so that no firm is in both groups.
