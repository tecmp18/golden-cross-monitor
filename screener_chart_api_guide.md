# Screener.in Historical PE / EPS / Price / DMA Data API

## Purpose

This document records how we found and used the Screener.in internal
chart endpoint to retrieve the historical data behind the charts on a
company page.

The workflow is:

``` text
Screener company page
        ↓
Find companyId
        ↓
Find chart JavaScript
        ↓
Find getChartMetric
        ↓
Find Utils.getUrl()
        ↓
Construct /api/company/{companyId}/chart/
        ↓
Pass q, days and consolidated
        ↓
Receive JSON datasets
```

> **Important:** Screener.in does not present this chart endpoint as a
> general public developer API. This workflow uses the HTTP endpoint
> used by the site's own web application. Treat it as an implementation
> detail that can change.

------------------------------------------------------------------------

# 1. Start with the company page

Example:

``` text
https://www.screener.in/company/AVANTEL/consolidated/
```

For consolidated financial data, use:

``` text
/consolidated/
```

when the company supports it.

Screener's normal company URL pattern is:

``` text
https://www.screener.in/company/{SYMBOL}/consolidated/
```

------------------------------------------------------------------------

# 2. Find the Company ID

Open the page source:

``` text
Ctrl + U
```

Then search for:

``` text
data-company-id
```

You should find the company's internal Screener ID in the HTML.

For AVANTEL:

``` text
companyId = 340
```

The same HTML also contained:

``` text
data-warehouse-id = 6594832
```

For the chart API, **companyId is the important value**.

### Example

``` text
AVANTEL
companyId = 340
```

Do not confuse:

``` text
companyId
```

with:

``` text
warehouseId
```

They are different identifiers.

------------------------------------------------------------------------

# 3. Find the chart JavaScript

The company page loads Screener's chart JavaScript.

Example:

``` text
https://cdn-static.screener.in/js/chart.2a4531d22d97.js
```

The exact filename/hash may change when Screener deploys a new version.

In the JavaScript, search for:

``` text
getChartMetric
```

The important function is the chart data loader.

Conceptually it does:

``` javascript
var params = {
    companyId: info.companyId,
    q: metrics.join("-"),
    days: days,
};

if (info.isConsolidated) {
    params.consolidated = "true";
}

var url = Utils.getUrl("getChartMetric", params);
```

Then it performs an AJAX request and parses the JSON response.

------------------------------------------------------------------------

# 4. Find `Utils.getUrl()`

The chart JavaScript does not directly contain the final HTTP URL.

It calls:

``` javascript
Utils.getUrl("getChartMetric", params)
```

The `Utils` object is defined in Screener's utility JavaScript.

Example:

``` text
https://cdn-static.screener.in/js/utils.0147599e8f13.js
```

Search that file for:

``` text
getChartMetric
```

The endpoint mapping is:

``` text
getChartMetric
        ↓
/api/company/{companyId}/chart/
```

The URL formatter then puts the remaining parameters into the query
string.

------------------------------------------------------------------------

# 5. The actual chart API

The final HTTP endpoint is:

``` text
https://www.screener.in/api/company/{COMPANY_ID}/chart/
```

For AVANTEL:

``` text
https://www.screener.in/api/company/340/chart/
```

The endpoint is then supplied with query parameters.

------------------------------------------------------------------------

# 6. Requesting the PE/EPS chart

The PE chart uses these Screener metrics:

``` text
Price to Earning
Median PE
EPS
```

They are supplied in the `q` parameter separated by hyphens:

``` text
q=Price+to+Earning-Median+PE-EPS
```

For a consolidated company, add:

``` text
consolidated=true
```

For five years of data:

``` text
days=1825
```

Therefore the AVANTEL request is:

``` text
https://www.screener.in/api/company/340/chart/?q=Price+to+Earning-Median+PE-EPS&days=1825&consolidated=true
```

------------------------------------------------------------------------

# 7. Requesting Price + DMA data

Screener's Price chart uses:

``` text
Price
DMA50
DMA200
Volume
```

The chart configuration uses:

``` text
Price-DMA50-DMA200-Volume
```

If Volume is not required, the useful metrics are:

``` text
Price-DMA50-DMA200
```

Example:

``` text
https://www.screener.in/api/company/340/chart/?q=Price-DMA50-DMA200&days=1825&consolidated=true
```

------------------------------------------------------------------------

# 8. Requesting everything together

For our Python data pipeline, we can request:

``` text
Price
DMA50
DMA200
Price to Earning
Median PE
EPS
```

The metric query becomes:

``` text
Price-DMA50-DMA200-Price to Earning-Median PE-EPS
```

A URL-encoded request can therefore look like:

``` text
https://www.screener.in/api/company/340/chart/?q=Price-DMA50-DMA200-Price+to+Earning-Median+PE-EPS&days=1825&consolidated=true
```

Using Python's `urllib.parse.urlencode()` is preferable to manually
constructing this URL because spaces and special characters are encoded
correctly.

------------------------------------------------------------------------

# 9. `days` parameter

The useful values for our workflow are:

``` text
365     = approximately 1 year
1095    = approximately 3 years
1825    = approximately 5 years
3652    = approximately 10 years
```

For our investment analysis, we generally use:

``` text
days=3652
```

when we want long historical context.

For the PE chart, Screener's own chart code switches to a five-year
period when PE is selected and the requested period is shorter than the
required threshold.

------------------------------------------------------------------------

# 10. Understanding the JSON response

The API returns an object containing:

``` json
{
  "datasets": [
    ...
  ]
}
```

Each dataset has a structure similar to:

``` json
{
  "metric": "EPS",
  "label": "TTM EPS",
  "values": [
    ["2026-04-26", 0.57],
    ["2026-07-11", 0.65]
  ],
  "meta": {}
}
```

PE looks like:

``` json
{
  "metric": "Price to Earning",
  "label": "PE",
  "values": [
    ["2026-07-31", 248.9],
    ["2026-08-07", 251.5],
    ["2026-08-14", 243.9],
    ["2026-08-20", 250.6]
  ],
  "meta": {}
}
```

Median PE looks like:

``` json
{
  "metric": "Median PE",
  "label": "Median PE = 56.9",
  "values": [
    ["2021-08-27", "56.9"],
    ["2026-08-20", "56.9"]
  ],
  "meta": {}
}
```

Price/DMA datasets use the same general concept:

``` text
[date, value]
```

------------------------------------------------------------------------

# 11. The three important PE/EPS datasets

For our analysis:

### EPS

``` text
metric = "EPS"
```

This is Screener's TTM EPS series.

### PE

``` text
metric = "Price to Earning"
```

This is the historical PE series used by the Screener PE chart.

### Historical median PE

``` text
metric = "Median PE"
```

This gives the median PE reference value for the requested chart period.

------------------------------------------------------------------------

# 12. Calculating PE relative to historical median

Once we have:

``` text
Current PE
Median PE
```

calculate:

``` text
PE / Median PE = Current PE / Median PE
```

Example:

``` text
Current PE = 22
Median PE  = 30

PE / Median PE
= 22 / 30
= 0.733
```

Interpretation:

``` text
0.73x historical median
```

This is useful because:

``` text
PE < Historical PE
```

is only a yes/no condition.

The ratio tells us the magnitude of the valuation difference.

------------------------------------------------------------------------

# 13. Company ID example: AVANTEL

``` text
Company:
AVANTEL

Screener page:
https://www.screener.in/company/AVANTEL/consolidated/

Company ID:
340

Warehouse ID:
6594832
```

Chart API:

``` text
https://www.screener.in/api/company/340/chart/
```

PE/EPS request:

``` text
https://www.screener.in/api/company/340/chart/?q=Price+to+Earning-Median+PE-EPS&days=1825&consolidated=true
```

------------------------------------------------------------------------

# 14. Python request example

A simple request can be made with:

``` python
import requests

company_id = 340

url = f"https://www.screener.in/api/company/{company_id}/chart/"

params = {
    "q": "Price-DMA50-DMA200-Price to Earning-Median PE-EPS",
    "days": 3652,
    "consolidated": "true",
}

response = requests.get(url, params=params, timeout=30)

response.raise_for_status()

data = response.json()

for dataset in data["datasets"]:
    print(dataset["metric"])
    print(dataset["values"][:5])
```

Using `params` is preferable to manually concatenating the query string.

------------------------------------------------------------------------

# 15. Recommended company JSON structure

For our watchlist pipeline, one JSON file per company can contain:

``` json
{
  "symbol": "AVANTEL",
  "company_id": 340,
  "consolidated": true,

  "data": {
    "price": {},
    "dma50": {},
    "dma200": {},
    "eps": {},
    "pe": {},
    "median_pe": {}
  },

  "latest": {
    "price": null,
    "dma50": null,
    "dma200": null,
    "eps": null,
    "pe": null,
    "median_pe": null,
    "pe_to_median": null
  }
}
```

This is the structure used by the Python extraction workflow we built.

------------------------------------------------------------------------

# 16. Important distinction: raw data vs analysis

Keep these layers separate.

### Layer 1 --- Screener API

Raw:

``` text
Price
DMA50
DMA200
EPS
PE
Median PE
```

### Layer 2 --- Python calculations

Derived:

``` text
EPS growth
PE change
PE / Median PE
```

### Layer 3 --- Quadrant Scanner

Classification:

``` text
BEST
GREAT
MIXED
WORST
```

The quadrant classification should remain in the scanner because its
EPS/PE flat-band thresholds are adjustable.

Do **not** hard-code the quadrant into the raw export.

------------------------------------------------------------------------

# 17. Finding a new company ID

For a new company:

1.  Open its Screener page.

2.  Press `Ctrl + U`.

3.  Search for:

    ``` text
    data-company-id
    ```

4.  Copy the value.

5.  Use that value in:

    ``` text
    /api/company/{companyId}/chart/
    ```

Example:

``` text
Company page:
https://www.screener.in/company/KPIL/consolidated/

Find:
data-company-id="..."

Then:

https://www.screener.in/api/company/{that_id}/chart/
```

There are also programmatic approaches that first query Screener's
company search and then extract the company ID from the returned company
page. An example implementation follows this pattern before calling
`/api/company/{company_id}/chart/`. citeturn0search0

------------------------------------------------------------------------

# 18. Quick reference

## Company page

``` text
https://www.screener.in/company/{SYMBOL}/consolidated/
```

## Find ID

``` text
Ctrl+U
→ search "data-company-id"
```

## Chart API

``` text
https://www.screener.in/api/company/{COMPANY_ID}/chart/
```

## PE + EPS

``` text
?q=Price+to+Earning-Median+PE-EPS
&days=1825
&consolidated=true
```

## Price + DMA

``` text
?q=Price-DMA50-DMA200
&days=3652
&consolidated=true
```

## Combined

``` text
?q=Price-DMA50-DMA200-Price+to+Earning-Median+PE-EPS
&days=3652
&consolidated=true
```

## Important dataset names

``` text
Price
DMA50
DMA200
EPS
Price to Earning
Median PE
```

## AVANTEL example

``` text
companyId = 340

https://www.screener.in/api/company/340/chart/?q=Price+to+Earning-Median+PE-EPS&days=1825&consolidated=true
```

------------------------------------------------------------------------

# 19. Caveat

This is the endpoint and request format we traced from Screener's web
application's JavaScript. It should be considered an
**internal/web-application endpoint**, not a guaranteed stable public
API. Screener's public documentation emphasizes its company pages and
Excel export functionality, while third-party implementations also
describe their access as scraping/using public pages rather than relying
on a guaranteed official API contract. citeturn0search5turn0search3

If Screener changes its JavaScript or endpoint structure, the steps in
this document---especially the `getChartMetric` → `Utils.getUrl()`
tracing process---are the way to rediscover the endpoint.
