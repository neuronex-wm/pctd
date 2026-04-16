# Primate Cell Types Dataset (PCTD) Website

This repository contains the source for a static website that presents the Primate Cell Types Dataset (PCTD), an open, public neuroscience resource. The site is designed to let users explore multimodal data (electrophysiological, and morphological) from primate cortical neurons through interactive tables, plots, and downloadable files.

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
- Feature names, display labels, units, population means, and plot settings are centralized in `js/ephysConfig.js` (see below).
- Supporting scripts in `data/support_scripts/` (e.g. `csv_to_json_web.py`) were used to convert raw data into the web-ready CSV/JSON files.
- End-to-end tests use [Playwright](https://playwright.dev/) and are located in `tests/`.

## Contributing

This repository is primarily used to host the public dataset website. If you would like to suggest improvements, open an issue or submit a pull request describing:

- The page(s) affected
- The proposed change (content, layout, or code)
- Any new data files and how they are generated

## Electrophysiology Feature Configuration (`js/ephysConfig.js`)

All electrophysiology feature names, labels, and plot settings are defined in a single file — `js/ephysConfig.js`. This means you can add, remove, or rename features in one place and have the change reflected across the parallel-coordinates plot, scatter plot, detail-view panels, and bar-chart comparisons without touching `ephys.js` or the HTML.

### Structure at a glance

```js
var EPHYS_CONFIG = {
    features: [ ... ],   // numeric electrophysiology features
    metadata: [ ... ],   // categorical / identifier columns (Species, Sex, etc.)
    defaults: { ... }    // initial scatter axes, table sort, parallel-coords colour
};
```

### Feature entry fields

| Field | Purpose | Example |
|---|---|---|
| `key` | Property name in the JSON data (must match exactly). | `"AP halfwidth"` |
| `label` | Display name with unit, used on plot axes and dropdowns. | `"AP Halfwidth (ms)"` |
| `tableHeader` | Short label shown in the HTML table column header. | `"Half Width"` |
| `unit` | Measurement unit string. | `"ms"` |
| `mean` | Population mean, shown in the bar-chart comparison. | `0.852` |
| `scatterPlot` | `true` to include in the scatter-plot axis dropdowns. | `true` |
| `parallelPlot` | Object with `range`, `scale` (`"linear"` / `"log"`), and optional `tickStep`. Set to `false` to exclude. | `{ range: [0, 3], scale: "linear" }` |

### Metadata entry fields

| Field | Purpose | Example |
|---|---|---|
| `key` | Property name in the JSON data. | `"Cortical area"` |
| `label` | Display name. | `"Cortical Area"` |
| `type` | `"categorical"` or `"identifier"`. | `"categorical"` |
| `parallelPlot` | Optional object with `tickCount` to show in parallel-coords. | `{ tickCount: 6 }` |

### Defaults

| Field | Purpose |
|---|---|
| `scatterX` / `scatterY` | Initial X/Y feature for the scatter plot. |
| `tableSort` / `tableSortOrder` | Default table sort column and direction. |
| `parallelColorBy` | Feature used to colour the parallel-coordinates lines. |

### Common tasks

| I want to… | What to edit |
|---|---|
| **Rename a feature label on plot axes** | Change `label` on the relevant feature entry. |
| **Change a table column header** | Change `tableHeader`, then update the matching `<th>` in `ephysCT.html`. |
| **Add a feature to the scatter dropdown** | Set `scatterPlot: true`, then add an `<option>` in `ephysCT.html`. |
| **Add / remove a parallel-coords axis** | Set or clear the `parallelPlot` object. The filter logic updates automatically. |
| **Change axis range or linear/log scale** | Edit `parallelPlot.range` / `parallelPlot.scale`. |
| **Update population means** | Edit `mean` on the feature entry. |

## Citation

If you use this dataset or site in your work, please cite the associated publication (see `citation.html` on the website for full citation details).
