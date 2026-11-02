# Variable definitions and codebook

## 1. Sample

- **Return sample:** 30 November 2021 to 2 October 2025, 964 trading days (the base day for the first return is 29 November 2021).
- **ESG sample:** 16 quarter-ends, 31 December 2021 to 30 September 2025.
- **Filters (every group):** the firm is domiciled in the United States (country field of the Bloomberg export) and has a
  closing price on every trading day of the sample. Index composition is therefore fixed over the sample.
- **FinTech cohort:** constituents of the ten Bloomberg FinTech indices after the filters; a firm is FinTech if it is in at
  least one of them (98 distinct firms).

| No. | Index | Code | Retrieved | After filters |
|---|---|---|---|---|
| 1 | UBS FinTech Index | UBXXFINT | 32 | 26 |
| 2 | Bank of America Broad FinTech Index | MLFINTEC | 41 | 38 |
| 3 | BI Global FinTech and Payment Valuation Peer Group | BIGLFPVP | 26 | 16 |
| 4 | Bloomberg Enterprise FinTech Aggregate Index | BEFAP | 61 | 45 |
| 5 | J.P. Morgan iDex U.S. Payment/FinTech Index | JP2PMT | 22 | 19 |
| 6 | Bloomberg Future FinTech Aggregate Total Return Index | BFPAT | 129 | 74 |
| 7 | FTSE Global FinTech and Blockchain Index | FGFBIP | 82 | 40 |
| 8 | Solactive FinTech Index | SOLFINT | 49 | 32 |
| 9 | BlueStar FinTech Index | BFNQ | 48 | 33 |
| 10 | Bloomberg Enterprise FinTech Focus Index | BEFFP | 52 | 37 |

- **S&P 500 (SPX):** 503 constituents retrieved, 467 after the filters.
- **TradFi:** S&P 500 firms in the Bloomberg Financials sector, minus every FinTech-index member (16 firms: JPM, SPGI, COF,
  IBKR, HOOD, ICE, MCO, COIN, NDAQ, FICO, MSCI, SYF, VRSK, EFX, BR, FDS), minus five firms domiciled outside the United States
  (CB, AON, ACGL, WTW, EG) and two firms without a complete price history in the export (ARES, FISV): 48 firms.
- **Accounting panel:** FinTech constituents versus all S&P 500 constituents outside every FinTech index; 608 firms with
  usable ROA over 21 quarters (12,670 firm-quarters), 590 firms for ROE, 592 for the price-to-book ratio.
- **Market panel:** 97 FinTech firms with ESG ratings and the 48 TradFi firms, 2022-Q1 to 2025-Q3 (2,171 firm-quarters).

## 2. Index-level variables

| Variable | Definition | Source / formula |
|---|---|---|
| `r_it` | Daily log return of firm i | ln(P_t / P_{t-1}), Bloomberg `PX_LAST` (equation 1) |
| EW index return | Mean of the constituents' daily log returns | |
| MCW index return | Weighted mean, weights = market capitalization at the end of the previous trading day (`CUR_MKT_CAP`); the last available value is carried over days missing in the export | |
| Cumulative level | 100 × exp(cumulative sum of daily log returns) | |
| Maximum drawdown | Largest peak-to-trough fall of the cumulative level | |
| `r_ft` | Daily risk-free rate | (1 + y_t)^(1/252) − 1, y_t = U.S. two-year Treasury yield |
| Sharpe ratio (quarter q) | mean(r_pt − r_ft) / sd(r_pt) × √252 over the trading days of q | equation (3) |
| Treynor ratio (quarter q) | 252 × mean(r_pt − r_ft) / β_pq, β from a regression of the portfolio excess return on the SPX excess return with the same weighting, over the days of q | equation (4) |
| Average ratios (Table 3) | Mean over the 15 complete quarters 2022-Q1 to 2025-Q3 | |
| Tests (Table 4) | Jarque-Bera on each series; paired t-test and Wilcoxon signed-rank test on the 964 daily returns of each FinTech index against SPX and against TradFi | equations (5)-(6) |
| Composite ESG | Mean of Bloomberg `ESG_SCORE_PERCENTILE` and `SP_R_ESG_RANK` (the available one if only one exists), 0-100 | equation (2) |
| EW / MCW ESG index | Mean / quarter-end-market-cap-weighted mean of the composite over the rated constituents, per quarter | |

## 3. Accounting panel (Tables 6 and 7, equations 8 and 9)

| Variable | Definition | Bloomberg field |
|---|---|---|
| `ROA` | Return on assets, percent, winsorized at the 1st and 99th percentiles | `RETURN_ON_ASSET` |
| `ROE` | Return on common equity, percent, winsorized | `RETURN_COM_EQY` |
| `PB` | Price-to-book ratio, winsorized | `PX_TO_BOOK_RATIO` |
| `Average_ESG` | Composite ESG of the firm-quarter | (`ESG_SCORE_PERCENTILE` + `SP_R_ESG_RANK`) / 2 |
| `FinTech` | 1 if the firm is in at least one FinTech index | authors |
| `ESG_x_FinTech` | `Average_ESG` × `FinTech` | |
| `ln(MarketCap)` | Log of market capitalization | `CUR_MKT_CAP` |
| `Debt/Assets` | Total debt over total assets | `BS_TOT_LIAB2` (or `SHORT_AND_LONG_TERM_DEBT`) / `BS_TOT_ASSET` |

Estimation: pooled OLS with standard errors clustered by firm (Table 6); the four specifications of Table 7; the within
(firm fixed effects) estimate of the interaction; Hausman test FE versus RE; VIF.

## 4. Market panel (Tables 8 and 9, equation 10)

| Variable | Definition |
|---|---|
| `Return` | Quarterly log return of the firm in percent (sum of daily log returns), winsorized 1/99 |
| `Volatility` | Annualized standard deviation of the firm's daily returns in the quarter, percent, winsorized 1/99 |
| `Sharpe` | Annualized quarterly Sharpe ratio of the firm (equation 3 applied firm by firm), winsorized 1/99 |
| `ESG (t-1)` | Composite ESG at the end of the previous quarter |
| `ln(MarketCap) (t-1)` | Log market capitalization at the end of the previous quarter (`CUR_MKT_CAP` from the ESG export) |
| `FinTech` | 1 for FinTech firms, 0 for TradFi firms |

Estimation: OLS with quarter effects (and firm effects in the even columns of Table 8), standard errors clustered by firm;
sub-periods 2022-Q1 to 2023-Q4 and 2024-Q1 to 2025-Q3; a version with the contemporaneous rating (Table 9, column 4).
