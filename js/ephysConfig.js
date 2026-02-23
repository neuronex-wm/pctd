/**
 * EPHYS_CONFIG — Single source of truth for electrophysiology feature names,
 * display labels, units, population means, and plot settings.
 *
 * To add/remove/rename a feature:
 *   1. Edit the relevant entry in `features` or `metadata` below.
 *   2. Reload the page — the parallel-coords plot, scatter plot, detail view,
 *      and bar-chart comparison will all pick up the change.
 *   3. If you also want the new name reflected in the HTML table headers or
 *      scatter dropdowns, update those in ephysCT.html manually (the HTML is
 *      static so you stay in control of the layout).
 *
 * KEY CONCEPTS
 * -----------
 *   key            – The property name used in the JSON data file.
 *                    Must match exactly (case-sensitive).
 *   label          – Human-friendly name shown on plot axes & dropdowns.
 *                    Includes the unit in parentheses where appropriate.
 *   tableHeader    – Short label used in the HTML table column header.
 *   unit           – Measurement unit string (for reference / future use).
 *   mean           – (Optional) Override for the population mean used in the
 *                    bar-chart comparison.  If omitted the mean is computed
 *                    automatically from the loaded data at runtime.
 *   parallelPlot   – Config for the parallel-coordinates dimension.
 *       range      – [min, max] of the axis.
 *       scale      – "linear" or "log" (log uses Math.log10 for values and
 *                    generates integer-rounded tick labels).
 *       tickStep   – Step size for tick generation (only used with "log").
 *   scatterPlot    – true if this feature should be available in the
 *                    scatter-plot axis dropdowns.
 */
var EPHYS_CONFIG = {

    // ── Numeric electrophysiology features ──────────────────────────────
    features: [
        {
            key: 'AP halfwidth',
            label: 'AP Halfwidth (ms)',
            tableHeader: 'Half Width',
            unit: 'ms',
            scatterPlot: true,
            parallelPlot: {
                range: [0, 3],
                scale: 'linear'
            }
        },
        {
            key: 'Amplitude',
            label: 'AP Amplitude (mV)',
            tableHeader: 'Amplitude',
            unit: 'mV',
            scatterPlot: true,
            parallelPlot: {
                range: [0, 120],
                scale: 'linear'
            }
        },
        {
            key: 'Rheobase',
            label: 'Rheobase (pA)',
            tableHeader: 'Rheobase',
            unit: 'pA',
            scatterPlot: true,
            parallelPlot: {
                range: [0, 500],
                scale: 'linear'
            }
        },
        {
            key: 'Resistance',
            label: 'Resistance (MΩ)',
            tableHeader: 'Resistance',
            unit: 'MΩ',
            scatterPlot: true,
            parallelPlot: {
                range: [0.75, 4],
                scale: 'log',
                tickStep: 0.5
            }
        },
        {
            key: 'Time Constant',
            label: 'Time Constant (ms)',
            tableHeader: 'Time Constant',
            unit: 'ms',
            scatterPlot: true,
            parallelPlot: {
                range: [0, 2.5],
                scale: 'log',
                tickStep: 0.25
            }
        },
        {
            key: 'Resting potential',
            label: 'Resting Potential (mV)',
            tableHeader: 'RMP',
            unit: 'mV',
            scatterPlot: true,
            parallelPlot: false          // not shown in parallel-coords plot
        },
        {
            key: 'Max Firing Rate',
            label: 'Maximum Firing Rate (Hz)',
            tableHeader: 'Max firing rate',
            unit: 'Hz',
            scatterPlot: true,
            parallelPlot: {
                range: [0, 250],
                scale: 'linear'
            }
        },
        {
            key: 'Median instantanous frequency',   // note: spelling matches JSON data
            label: 'Median Instantaneous Freq (Hz)',
            tableHeader: 'Median Inst. Freq',
            unit: 'Hz',
            scatterPlot: false,         // not in scatter dropdowns
            parallelPlot: false         // not in parallel-coords plot
        }
    ],

    // ── Metadata / categorical columns ──────────────────────────────────
    // These keys are treated as "subject info" in the detail-view panel
    // and are excluded from the numeric ephys details section.
    metadata: [
        { key: 'Species',        label: 'Species',        type: 'categorical' },
        { key: 'Sex',            label: 'Sex',            type: 'categorical' },
        { key: 'Cortical area',  label: 'Cortical Area',  type: 'categorical',
            parallelPlot: {
                // Categorical axis — tick values are auto-generated from data
                tickCount: 6       // hint: max number of unique categories expected
            }
        },
        { key: 'Dendrite type',  label: 'Dendrite Type',  type: 'categorical',
                parallelPlot: {
                // Categorical axis — tick values are auto-generated from data
                tickCount: 6       // hint: max number of unique categories expected
            }
        },
        { key: 'Cortical layer', label: 'Cortical Layer', type: 'categorical'},
        { key: 'cellID',         label: 'Cell ID',        type: 'identifier'  }
    ],

    // ── Detail View ─────────────────────────────────────────────────────
    // Features shown in the expanded-row "Ephys Details" card.
    // Each entry is { key, label }.  key must match a JSON data property;
    // label is what the user sees.  Order here = display order.
    // Add / remove / reorder entries to control the detail panel.
    detailViewFeatures: [
        { key: 'AP halfwidth',                    label: 'AP Halfwidth (ms)' },
        { key: 'Amplitude',                       label: 'AP Amplitude (mV)' },
        { key: 'Rheobase',                        label: 'Rheobase (pA)' },
        { key: 'Resistance',                      label: 'Resistance (MΩ)' },
        { key: 'Time Constant',                   label: 'Time Constant (ms)' },
        { key: 'Resting potential',               label: 'Resting Potential (mV)' },
        { key: 'Max Firing Rate',                 label: 'Maximum Firing Rate (Hz)' },
        { key: 'Median instantanous frequency',   label: 'Median Instantaneous Freq (Hz)' }
    ],

    // ── Defaults ────────────────────────────────────────────────────────
    defaults: {
        scatterX: 'AP halfwidth',         // initial X-axis feature for scatter plot
        scatterY: 'Amplitude',         // initial Y-axis feature for scatter plot
        tableSort: 'Resting potential',   // default table sort column (data key)
        tableSortOrder: 'asc',
        parallelColorBy: 'AP halfwidth'   // feature used for parallel-coords colour
    }
};

// ── Derived helpers (computed once, used by ephys.js) ───────────────────
// These are simple look-ups so the rest of the code doesn't need to
// iterate the config every time.

/** Array of metadata keys — used to separate "subject info" from numeric data */
EPHYS_CONFIG._metadataKeys = EPHYS_CONFIG.metadata.map(function (m) { return m.key; });

/** Direct reference — the detail-view list is already in the right format */
EPHYS_CONFIG._detailViewFeatures = EPHYS_CONFIG.detailViewFeatures;

/** { dataKey: mean } object — populated at runtime by computeMeans() */
EPHYS_CONFIG._means = {};

/**
 * Compute population means from the loaded data array.
 * Called once in ephys.js after the AJAX load completes.
 * If a feature has a hardcoded `mean` in the config it is used as-is;
 * otherwise the mean is calculated from the data.
 */
EPHYS_CONFIG.computeMeans = function (data) {
    EPHYS_CONFIG.features.forEach(function (f) {
        // Allow manual override
        if (f.mean !== undefined) {
            EPHYS_CONFIG._means[f.key] = f.mean;
            return;
        }
        // Auto-compute from data
        var sum = 0;
        var count = 0;
        data.forEach(function (row) {
            var v = parseFloat(row[f.key]);
            if (!isNaN(v)) {
                sum += v;
                count++;
            }
        });
        EPHYS_CONFIG._means[f.key] = count > 0 ? sum / count : 0;
    });
};

/** { dataKey: label } object — axis / dropdown labels keyed by data key */
EPHYS_CONFIG._featureLabels = {};
EPHYS_CONFIG.features.forEach(function (f) {
    EPHYS_CONFIG._featureLabels[f.key] = f.label;
});
