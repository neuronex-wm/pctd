# Primate Cell Types Dataset (PCTD) Website

This repository contains the source for a static website that presents the Primate Cell Types Dataset (PCTD), an open, public neuroscience resource. The site is designed to let users explore multimodal data (transcriptomic, electrophysiological, and morphological) from priamte cortical neurons through interactive tables, plots, and downloadable files.

## Repository Structure

- Top-level HTML pages (e.g. `index.html`, `transcriptome.html`, `EephysCT.html`, `morphology.html`) define the main sections of the site.
- `data/` contains CSV/JSON files used to populate tables, plots, and interactive visualizations.
- `js/` holds custom JavaScript for interactivity (filters, plots, viewers) as well as third‑party libraries.
- `css/` includes stylesheets such as Bootstrap and custom layout/theme CSS.
- `swc/` stores neuron morphology files in SWC format for 3D visualization.
- `images/` and `video/` include figures, thumbnails, and media assets.
- `externals/` and `old or duplicates/` keep experimental or legacy assets that are not part of the main site.

## Key Pages

- `index.html` – Landing page with overview and navigation.
- `transcriptome.html` – Transcriptomic cell type views and related visualizations.
- `EephysCT.html` / `ephysCT.html` – Electrophysiology cell type views.
- `morphology.html` – Morphological reconstructions and SWC-based 3D viewer.
- `search.html` – Search and lookup tools for cells and metadata.
- `download.html` – Links to download underlying data files.

## Data and Usage

The `data/` directory provides pre-generated tables and feature summaries used by the site. In general:

- JSON files are loaded by the JavaScript in `js/` for interactive visualizations.
- CSV files contain the same or related information in a tabular format for offline use.
- SWC files in `swc/` can be loaded by standard morphology viewers in addition to the embedded viewer on the site.

If you build new visualizations, prefer reading from the existing JSON/CSV files in `data/` to keep everything in sync.

## Development Notes

- Front-end layout and components are primarily based on Bootstrap 5. 
- The entire website is designed to be hosted statically. Saves on hosting costs & ensures legacy.
- Custom interaction logic (filters, tables, plots) lives in `js/index.js`, `js/morphology.js`, and other scripts in `js/`.
- Supporting scripts in `data/support_scripts/` (e.g. `csv_to_json_web.py`) were used to convert raw data into the web-ready CSV/JSON files.

## Adding / updating data

- The pipeline / method for updating data is quite old. Written when I was a novice coder. The general idea is so:


## Contributing

This repository is primarily used to host the public dataset website. If you would like to suggest improvements, open an issue or submit a pull request describing:

- The page(s) affected
- The proposed change (content, layout, or code)
- Any new data files and how they are generated

## Citation

If you use this dataset or site in your work, please cite the associated publication (see `citation.html` on the website for full citation details).