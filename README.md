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

## Development Notes

- Front-end layout and components are primarily based on Bootstrap 4.
- The entire website is designed to be hosted statically. Saves on hosting costs & ensures legacy.
- Custom interaction logic (filters, tables, plots) lives in `js/index.js`, `js/ephys.js`, and other scripts in `js/`.
- Feature names, display labels, units, population means, and plot settings are centralized in `js/ephysConfig.js` (see below).
- Supporting scripts in `data/support_scripts/` handle data conversion, trace management, and DANDI preparation (see [Updating the Data](#updating-the-data) above).
- End-to-end tests use [Playwright](https://playwright.dev/) and are located in `tests/`.

## Contributing

This repository is primarily used to host the public dataset website. If you would like to suggest improvements, open an issue or submit a pull request describing:

- The page(s) affected
- The proposed change (content, layout, or code)
- Any new data files and how they are generated

## Data and Usage

The `data/` directory provides pre-generated tables and feature summaries used by the site. In general:

- JSON files are loaded by the JavaScript in `js/` for interactive visualizations.
- CSV files contain the same or related information in a tabular format for offline use.

If you build new visualizations, prefer reading from the existing JSON/CSV files in `data/` to keep everything in sync.


## Updating the Data

All data-processing scripts live in `data/support_scripts/`. The pipeline flows roughly as:

```
source CSV ─► _2026_conv.py ─► box2_ephys.csv / .json
                                    │
               ┌────────────────────┼───────────────────┐
               ▼                    ▼                    ▼
       id_Lookup.py /        gen_swc_loading.py    prep_for_dandi.py
       _pull_goe.py          (SWC → PNG)           (NWB validation)
       (trace renaming)            │                    │
               │                   ▼                    ▼
               ▼              data/morph/         match_dandi_names.py
         data/traces/                              ─► dandi_mapping.csv
```

> **Important:** Most scripts contain hardcoded local paths near the top of the file. Update these to match your environment before running.

### Script Quick-Reference

| Script | Purpose | Key Input | Key Output |
|--------|---------|-----------|------------|
| `_2026_conv.py` | Convert a new dataset to the website format | Source dataset CSV | `data/box2_ephys.csv`, `data/box2_ephys.json` |
| `bucket_pull.py` | Download trace CSVs from the S3 bucket | S3 bucket URL (hardcoded) | `downloaded_files/` |
| `id_Lookup.py` | Rename trace files from internal IDs to cell IDs | `box2_ephys.csv` + trace CSVs | Renamed files in `data/traces/` |
| `_pull_goe.py` | Copy & rename GOE dataset traces | `box2_ephys.csv` + GOE traces folder | Renamed files in `data/traces/` |
| `gen_swc_loading.py` | Render SWC morphology files as PNGs | Local SWC directory | Full-size + 48×48 thumbnails in `data/morph/` |
| `dandi_prep/prep_for_dandi.py` | Validate, repair, and organise NWBs | Source NWB folder + `box2_ephys.csv` | `data/updated_nwbs/{subject}/` |
| `dandi_prep/match_dandi_names.py` | Link local NWBs to DANDI archive paths | `data/updated_nwbs/` + `001776/` | `data/dandi_mapping.csv` |
| `dandi_prep/pack_in_Swc.py` | Embed SWC data into NWB files (experimental) | NWBs + SWC files | `data/nwbs_with_morph/` |

### Python Dependencies

```
pip install pandas numpy h5py pynwb hdmf ngauge matplotlib httpx
```

Not every script needs all packages — `_2026_conv.py` only requires `pandas`, `numpy`, and `json`, for example — but the list above covers the full pipeline.

### 1. Adding or Updating Cells (`_2026_conv.py`)

This is the main ingestion script. It reads a source dataset CSV, renames columns to match the website schema, computes availability flags, and writes the two files the website consumes.

**Steps:**

1. Open `_2026_conv.py` and update the input CSV path at the top of the file (currently points to a local `marmData_wUMAP.csv`).
2. Review the `OTHER_MAPPINGS` dictionary — it maps source column names to the website's expected names (e.g. `RinHD` → `Resistance`, `widTP_LP` → `AP halfwidth`). Add or modify entries if the new dataset uses different column names.
3. The script auto-detects whether trace/morphology files exist by scanning `data/traces/` and `data/morph/`. The boolean columns `hasPlot` and `hasMorph` are set accordingly, so make sure trace and morphology files are in place *before* running this script (or re-run it afterward).
4. Dendritic types are mapped as: `A` → Aspiny, `S` → Spiny, anything else → Unknown.
5. Rows are sorted by Amplitude (descending), then `hasPlot`, then `hasMorph` so the most complete cells appear first in the table.
6. Run the script. It writes `data/box2_ephys.csv` and `data/box2_ephys.json`.

If you need to flag specific cells for removal, add their IDs to the `flag_cells` list near the top of the script.

After updating the data, check whether any new features were added. If so, add corresponding entries in `js/ephysConfig.js` (see the [Electrophysiology Feature Configuration](#electrophysiology-feature-configuration-jsephysconfigjs) section below).

### 2. Updating Traces

Trace files are CSV files stored in `data/traces/`, named by cell ID (e.g. `CJ001.csv`).

**Downloading from S3:**
`bucket_pull.py` downloads all trace CSVs from the project's S3 bucket (`ptcd-traces.s3.us-east-2.amazonaws.com`). Files are saved to a local `downloaded_files/` directory.

**Renaming files to cell IDs:**
Source trace files are typically named by internal recording ID. Two scripts handle renaming:

- `id_Lookup.py` — general-purpose: reads the `internalID` → `cellID` mapping from `box2_ephys.csv`, copies each trace CSV in `data/traces/` to a new file named `{cellID}.csv`.
- `_pull_goe.py` — same logic, but pulls from a separate GOE traces folder and copies into `data/traces/`.

Both scripts require `box2_ephys.csv` to exist first (produced by `_2026_conv.py`).

### 3. Updating Morphology Previews (`gen_swc_loading.py`)

This script converts SWC reconstruction files into PNG images used by the website.

1. Update `swc_dir` at the top of the file to point to your local folder of `.swc` files.
2. Run the script. For each SWC file it produces:
   - A full-size image at 300 dpi: `data/morph/{name}_morph.png`
   - A 48×48 thumbnail: `data/morph/{name}_morph_thumb.png`
3. After generating images, re-run `_2026_conv.py` so the `hasMorph` flags are updated.

Requires the `ngauge` and `matplotlib` packages.

### 4. Preparing NWBs for DANDI Upload

These scripts live in `data/support_scripts/dandi_prep/`.

**Step 1 — Validate and organise (`prep_for_dandi.py`):**

```bash
python prep_for_dandi.py --data-folders /path/to/raw/nwbs --id-lookup-csv ../../box2_ephys.csv --new-nwb-dir ../../updated_nwbs
```

- Copies NWB files into `data/updated_nwbs/{subject}/`, renaming by cell ID.
- Attempts to read each file with `pynwb`. If reading fails (common with MatLab-exported NWBs), it applies a repair pass using `h5py`: adds a dummy intracellular electrode, links it to acquisition/stimulus datasets, and ensures subject weight metadata exists.
- Use `--retain-original-id` to keep the internal ID in the filename alongside the cell ID.

**Step 2 — Match to DANDI archive (`match_dandi_names.py`):**

This script links local NWBs in `data/updated_nwbs/` to the corresponding files in the DANDI archive directory (`001776/`). It uses a two-tier matching strategy:

1. **Tier 1 (file size):** If a source NWB has a unique file size among the candidate DANDI files, it matches immediately.
2. **Tier 2 (timestamp):** For ambiguous sizes, it reads `session_start_time` from the source NWB (via `h5py`) and matches against the timestamp encoded in the DANDI filename (`ses-YYYYMMDDTHHMMSS`).

Output: `data/dandi_mapping.csv` with columns `cellID`, `updated_nwbs_path`, `dandi_path`, `dandi_filename`, and `match_method`.

The `001776/` directory (DANDI dataset structure) must be present locally for this script to work.

**Step 3 (experimental) — Embed morphology (`pack_in_Swc.py`):**

Reads SWC files and writes them as `DynamicTable` entries inside a `morphology` processing module in each NWB. Output goes to `data/nwbs_with_morph/`. This step is optional and still under development.


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