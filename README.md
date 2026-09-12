# Where To Brap

A live snow report for the Tony Grove Lake SNOTEL station, built to run for free on GitHub Pages.

## What's in here
- `index.html` — the site. Reads `data.json` and renders it.
- `data.json` — the latest snow data. Gets overwritten automatically every hour.
- `scripts/fetch_snow.py` — fetches SNOTEL data and rewrites `data.json`.
- `.github/workflows/update-snow.yml` — the GitHub Action that runs the script hourly.
- `CNAME` — tells GitHub Pages this site should answer to www.wheretobrap.com.

See the setup steps in the chat where this was generated for how to get this live.
