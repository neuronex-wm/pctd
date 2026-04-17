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

All data-processing scripts live in `data/support_scripts/`. The pipeline is managed by a single orchestrator script with centralized configuration — no hardcoded paths to edit.

```
source CSV ─► convert_dataset.py ─► box2_ephys.csv / .json
                                         │
               ┌─────────────────────────┼───────────────────┐
               ▼                         ▼                    ▼
        pull_traces.py          render_morphology.py    dandi_prep/
        (copy/rename)            (SWC → PNG)           prep_for_dandi.py
               │                        │                    │
               ▼                        ▼                    ▼
         data/traces/             data/morph/         match_dandi_names.py
                                                      ─► dandi_mapping.csv
```

### Quick Start: Adding New Cells (Append Mode)

The most common task — adding new cells without regenerating the whole database:

```bash
cd data/support_scripts

# Append from a CSV (format is auto-detected)
python run_pipeline.py append path/to/new_cells.csv
```

That's it. The script will:
1. Auto-detect whether your CSV is in raw format (source column names like `RinHD`, `widTP_LP`) or pre-formatted (display names like `Resistance`, `AP halfwidth`)
2. Transform columns if needed
3. Merge into the existing `box2_ephys.csv` / `.json`, overwriting any duplicate `cellID` entries
4. Create a backup (`box2_ephys.csv.bak`) before writing
5. Print a summary of cells added/updated

**Accepted input formats:**
- **Raw format** — same as the source dataset (e.g. `marmData_wUMAP.csv`): must have columns like `Row`, `Identifier`, `RinHD`, `widTP_LP`, etc.
- **Pre-formatted** — already in website schema: must have columns like `internalID`, `cellID`, `Resistance`, `AP halfwidth`, etc.

### Full Rebuild

For a complete regeneration from a master dataset:

```bash
cd data/support_scripts

# Option A: set environment variable
set PCTD_SOURCE_CSV=C:\path\to\full_dataset.csv     # Windows
export PCTD_SOURCE_CSV=/path/to/full_dataset.csv     # Linux/Mac

python run_pipeline.py convert

# Option B: pass directly
python convert_dataset.py --source C:\path\to\full_dataset.csv
```

### Script Quick-Reference

| Script | Purpose | Key Input | Key Output |
|--------|---------|-----------|------------|
| `run_pipeline.py` | Orchestrator — run any step by name | Step name + args | Delegates to other scripts |
| `convert_dataset.py` | Convert source CSV or append new cells | Source/append CSV | `data/box2_ephys.csv`, `.json` |
| `pull_traces.py` | Copy and rename local trace files | `--source-dir` | `data/traces/` |
| `render_morphology.py` | Render SWC files as PNGs | `--swc-dir` or `PCTD_SWC_DIR` | `data/morph/` |
| `pipeline_config.py` | Centralized paths & column mappings | (configuration module) | — |
| `id_utils.py` | Shared ID mapping & file helpers | (utility module) | — |
| `dandi_prep/prep_for_dandi.py` | Validate, repair, and organise NWBs | `--data-folders` + CSV | `data/updated_nwbs/` |
| `dandi_prep/match_dandi_names.py` | Link NWBs to DANDI archive paths | `updated_nwbs/` + `001776/` | `data/dandi_mapping.csv` |
| `dandi_prep/pack_in_Swc.py` | Embed SWC into NWBs (experimental) | NWBs + SWCs | `data/nwbs_with_morph/` |

### Environment Variables (Optional)

All paths auto-resolve relative to the repo. Override with environment variables only if your layout differs:

| Variable | Purpose | Default |
|----------|---------|---------|
| `PCTD_SOURCE_CSV` | Full source dataset for regeneration | *(none — required for full convert)* |
| `PCTD_SWC_DIR` | Directory of `.swc` files | *(none — required for morph step)* |
| `PCTD_RAW_NWB_DIR` | Raw NWB source folder | *(none — required for DANDI prep)* |
| `PCTD_BOX2_CSV` | Override `data/box2_ephys.csv` location | `<repo>/data/box2_ephys.csv` |
| `PCTD_TRACES_DIR` | Override traces directory | `<repo>/data/traces` |
| `PCTD_MORPH_DIR` | Override morphology directory | `<repo>/data/morph` |

### Python Dependencies

```
pip install pandas numpy h5py pynwb hdmf ngauge matplotlib
```

Not every script needs all packages — `convert_dataset.py` only requires `pandas` and `numpy` — but the list above covers the full pipeline.

### Pipeline Steps in Detail

#### 1. Adding or Updating Cells (`convert_dataset.py`)

**Append mode** (most common — adds to existing DB):
```bash
python convert_dataset.py --append path/to/new_cells.csv
```
- Input format is auto-detected (raw or pre-formatted)
- Duplicates by `cellID` are overwritten with the new data
- `hasPlot` / `hasMorph` flags are recomputed for new rows
- A `.bak` backup is created before modifying the database

**Full mode** (regenerate everything from scratch):
```bash
python convert_dataset.py --source path/to/full_dataset.csv
```
- Reads the complete source dataset
- Applies column renaming (`RinHD` → `Resistance`, etc.)
- Maps dendrite types: `A` → Aspiny, `S` → Spiny
- Sorts by Amplitude, hasPlot, hasMorph (descending)
- Overwrites `data/box2_ephys.csv` and `data/box2_ephys.json`

Column mappings are defined in `pipeline_config.py` → `COLUMN_MAPPINGS` dict. This is the single source of truth that must stay in sync with `js/ephysConfig.js`.

#### 2. Updating Traces (`pull_traces.py`)

```bash
# Copy traces from a local directory, renaming by internalID
python pull_traces.py --source-dir /path/to/traces/
```

Source files may be named by `cellID` (numeric) or `internalID` (string). Files named by `cellID` are automatically renamed to the corresponding `internalID`. Trace files are stored in `data/traces/` (e.g. `A19_MM_A1_C08.csv`).

#### 3. Updating Morphology Previews (`render_morphology.py`)

```bash
python render_morphology.py --swc-dir /path/to/swc/files/
# or: set PCTD_SWC_DIR=... then just run:
python render_morphology.py
```

For each SWC file it produces:
- Full-size image at 300 dpi: `data/morph/{name}_morph.png`
- 48×48 thumbnail: `data/morph/{name}_morph_thumb.png`

After generating images, re-run `convert_dataset.py --append` or `convert` so the `hasMorph` flags update.

#### 4. Preparing NWBs for DANDI Upload

```bash
# Step 1: Validate and organise NWBs
python dandi_prep/prep_for_dandi.py --data-folders /path/to/raw/nwbs

# Step 2: Match to DANDI archive
python dandi_prep/match_dandi_names.py

# Step 3 (optional): Embed morphology
python dandi_prep/pack_in_Swc.py
```

See docstrings in each script for details. All paths now import from `pipeline_config.py`.

### Legacy Scripts

Old scripts are preserved in `data/support_scripts/_archive/` for reference. They are superseded by the new pipeline but kept for historical context.


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
