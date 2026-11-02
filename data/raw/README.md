# `data/raw/` — Bloomberg exports (not committed)

Everything in this folder except this file is ignored by git. Bloomberg and S&P Global terms of use do not allow
redistribution of the raw data, so the files below have to be exported by the user from a Bloomberg Terminal.

## Files used by `code/01_index_level_and_market_panel.py`

The script finds each file by the end of its name, so a date prefix such as `2025.11.25_` is fine.

| File | Content | Layout |
|---|---|---|
| `*Original_Price_Data.xlsx` | Daily closing prices (`PX_LAST`), one sheet per index: `SPX`, `UBXXFINT`, `MLFINTEC`, `BIGLFPVP`, `JP2PMT`, `BEFAP`, `BFPAT`, `FGFBIP`, `SOLFINT`, `BFNQ`, `BEFFP` | Row 1: `Dates` then one Bloomberg ticker per column (e.g. `PYPL UW Equity`); one row per trading day from 29 Nov 2021 |
| `*Original_Marketcap_Data.xlsx` | Daily market capitalization (`CUR_MKT_CAP`), same sheets and tickers | Same layout; a non-date flag row under the header is ignored |
| `*Original_Time_and_Country_Restrictions.xlsx` | Sheet `Time+Country restriction`: for every index a block of four columns (ticker, listing flag, country of domicile, blank) | Country code `US` keeps the firm |
| `*BD_v4.xlsx` | Sheet `EW`: column `Date` with the 964 trading days of the sample (30 Nov 2021 to 2 Oct 2025); sheet `Risk-free`: columns `Date`, `US2Y` (two-year Treasury yield, decimal) | |
| `*ESG.xlsx` | Sheets `Fintech` and `Nonficntech`: quarterly `ESG_SCORE`, `ESG_SCORE_PERCENTILE`, `SP_R_ESG_RANK`, `CUR_MKT_CAP` per ticker, CQ4 2020 to CQ4 2025 | Row 4: ticker above its first field; row 6: field codes; rows 7+: quarter-end dates and values. The `Nonficntech` sheet lists the S&P 500 Financials candidates for the TradFi group |

## File used by `code/03_accounting_panel.py`

`panel_dataset.csv`, one row per firm-quarter, with the columns `firm_id, quarter, fintech, roa, roe, pb,
esg_percentile, esg_rank, market_cap, total_debt, total_assets` (Bloomberg fields `RETURN_ON_ASSET`,
`RETURN_COM_EQY`, `PX_TO_BOOK_RATIO`, `ESG_SCORE_PERCENTILE`, `SP_R_ESG_RANK`, `CUR_MKT_CAP`, `BS_TOT_LIAB2`
or `SHORT_AND_LONG_TERM_DEBT`, `BS_TOT_ASSET`) for the firms of the accounting panel (608 firms with ROA data, 21 quarters).
