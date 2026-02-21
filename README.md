# Primate Cell Types Dataset (PCTD) Website

This repository contains the source for a static website that presents the Primate Cell Types Dataset (PCTD), an open, public neuroscience resource. The site is designed to let users explore multimodal data (transcriptomic, electrophysiological, and morphological) from primate cortical neurons through interactive tables, plots, and downloadable files.

## Repository Structure

- Top-level HTML pages (e.g. `index.html`, `ephysCT.html`, `search.html`) define the main sections of the site.
- `data/` contains CSV/JSON files used to populate tables, plots, and interactive visualizations.
- `js/` holds custom JavaScript for interactivity (filters, plots, viewers) as well as third‑party libraries.
- `css/` includes stylesheets such as Bootstrap and custom layout/theme CSS.
- `images/` includes figures, thumbnails, and other media assets.
- `tests/` contains Playwright end-to-end tests.

## Key Pages

- `index.html` – Landing page with overview and navigation.
- `ephysCT.html` – Electrophysiology cell type views.
- `numberOfCells.html` – Cell count summaries.
- `search.html` – Search and lookup tools for cells and metadata.
- `analytics.html` – Analytics and data summaries.
- `ourTeam.html` – Team member profiles.
- `citation.html` – Citation information for the dataset.

## Data and Usage

The `data/` directory provides pre-generated tables and feature summaries used by the site. In general:

- JSON files are loaded by the JavaScript in `js/` for interactive visualizations.
- CSV files contain the same or related information in a tabular format for offline use.

If you build new visualizations, prefer reading from the existing JSON/CSV files in `data/` to keep everything in sync.

## Development Notes

- Front-end layout and components are primarily based on Bootstrap 4.
- The entire website is designed to be hosted statically. Saves on hosting costs & ensures legacy.
- Custom interaction logic (filters, tables, plots) lives in `js/index.js`, `js/ephys.js`, and other scripts in `js/`.
- Supporting scripts in `data/support_scripts/` (e.g. `csv_to_json_web.py`) were used to convert raw data into the web-ready CSV/JSON files.
- End-to-end tests use [Playwright](https://playwright.dev/) and are located in `tests/`.

## Contributing

This repository is primarily used to host the public dataset website. If you would like to suggest improvements, open an issue or submit a pull request describing:

- The page(s) affected
- The proposed change (content, layout, or code)
- Any new data files and how they are generated

## Citation

If you use this dataset or site in your work, please cite the associated publication (see `citation.html` on the website for full citation details).