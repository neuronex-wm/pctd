// Declare global variables outside $(document).ready()
var $table;
var $parallelCoordsPlot;
var ephysData = null;
var timeseries;
// Derived from EPHYS_CONFIG (see js/ephysConfig.js)
var spec_keys = EPHYS_CONFIG._metadataKeys;
var means = EPHYS_CONFIG._means;
// DANDI download maps (populated on page load)
var dandiMapping = null;   // cellID (string) → DANDI path
var dandiAssetMap = null;  // DANDI path → asset_id

$(document).ready(function() {
    // Initialize global variables that depend on DOM
    $table = $('#table');
    $parallelCoordsPlot = $('#parallelCoordsPlot');
    
    // Load data and initialize table
    $.ajax({
        url: 'data/box2_ephys.json',
        dataType: 'json'
    }).done(function (data) {
        // Store data globally for reuse
        ephysData = data;

        // Compute population means from the loaded data
        EPHYS_CONFIG.computeMeans(data);
        means = EPHYS_CONFIG._means;
        
        // Load data into the table
        $table.bootstrapTable('load', data);
        
        // Apply filters after data is loaded
        var cellvars = getUrlParam('cell', '');
        if (cellvars !== '') {
            $table.bootstrapTable('filterBy', { 'ID': cellvars });
        }
        // Generate graphs
        generate_all_graphs();
    });

    // Load DANDI cellID → path mapping from CSV
    $.ajax({
        url: 'data/dandi_mapping.csv',
        dataType: 'text'
    }).done(function (csvText) {
        dandiMapping = {};
        var lines = csvText.split('\n');
        for (var i = 1; i < lines.length; i++) {
            var cols = lines[i].split(',');
            if (cols.length >= 3 && cols[0].trim()) {
                var cellID = cols[0].trim();
                var dandiPath = cols[2].trim()
                    .replace(/^001776[\\\/]/, '')
                    .replace(/\\/g, '/');
                if (dandiPath) {
                    dandiMapping[cellID] = dandiPath;
                }
            }
        }
    });

    // Load DANDI asset list → build path → asset_id map
    $.ajax({
        url: 'https://api.dandiarchive.org/api/dandisets/001776/versions/draft/assets/?page_size=1000',
        dataType: 'json'
    }).done(function (resp) {
        dandiAssetMap = {};
        if (resp && resp.results) {
            resp.results.forEach(function (asset) {
                dandiAssetMap[asset.path] = asset.asset_id;
            });
        }
    });
});


function nameFormatter(value, row, field, index) {

    if (typeof value == 'string' && value == '') {
        return '';
    } else {

        //return '<span class="badge badge-light">'+ index + '</span>' + '<p>' + value + '</p>'
        return value
    };
}


//functions to format columns
function imageFormatter(value, row) {
    return '<img src="images/previews/' + row.internalID + '.png" style="width:50px;height:50px;" onerror=this.src="images/backup.png" />';
}
function doesFileExist(urlToFile) {
    var xhr = new XMLHttpRequest();
    xhr.open('HEAD', urlToFile, false);
    xhr.send();

    return xhr.status !== 404;
}
function reportFormatter(value, row) {
    return '<a class="fa fa-exclamation-circle" onclick="on(\'' + row.ID + '\')"></a>';
}
function linkFormatter(value, row) {
    // Downloads temporarily disabled
    return '<button class="btn btn-primary btn-sm" disabled title="Downloads temporarily unavailable">Download (NWB)</button>';
}
function morphFormatter(value, row) {
    if (value) {
        // Downloads temporarily disabled
        return '<button class="btn btn-secondary btn-sm" style="margin: 5px" disabled title="Downloads temporarily unavailable">Download Morph</button>';
    }
    else { return; }
}

function detailFormatter(index, row) {
    var html = []
    var url = "./data/traces/" + row.internalID + ".csv"
    var plot_bool = doesFileExist(url)
    var morph_url = "./data/morph/" + row.internalID + "_morph.png"
    var morph_bool = doesFileExist(morph_url)

    html.push('<div class="detail-container">');
    html.push('<div class="row">');

    // Left side - Waveform plot
    html.push('<div class="col-lg-8 col-md-7 col-12">');
    html.push('<div class="waveform-card">');
    html.push('<h6 class="section-title"><i class="bi bi-activity"></i> Electrophysiology Trace</h6>');
    if (plot_bool) {
        html.push('<div id="' + row.cellID + '" class="waveform-plot"><div class="d-flex justify-content-center align-items-center" style="min-height:350px;"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div></div>');
    } else {
        html.push('<div id="' + row.cellID + '" class="waveform-plot"><img src="images/plot_unavailable.png" class="img-fluid"></div>');
    }
    html.push('</div>');
    html.push('</div>');

    // Right side - Details
    html.push('<div class="col-lg-4 col-md-5 col-12">');
    
    // Subject Details Card
    html.push('<div class="info-card">');
    html.push('<h6 class="section-title"><i class="bi bi-person-badge"></i> Subject Details</h6>');
    html.push('<div class="info-grid">');
    $.each(row, function (key, value) {
        if (spec_keys.includes(key)){
            html.push('<div class="info-item"><span class="info-label">' + key + '</span><span class="info-value">' + (value || 'N/A') + '</span></div>');
        }
    });
    html.push('</div>');
    html.push('</div>');

    // Morphology card (only if image exists)
    if (morph_bool) {
        html.push('<div class="info-card">');
        html.push('<h6 class="section-title"><i class="bi bi-diagram-3"></i> Morphology</h6>');
        html.push('<div style="text-align:center;"><img src="' + morph_url + '" class="img-fluid" alt="Morphology reconstruction" style="max-height:250px;"></div>');
        html.push('</div>');
    }
    
    // Ephys Details Card — uses EPHYS_CONFIG._detailViewFeatures for order & labels
    html.push('<div class="info-card">');
    html.push('<h6 class="section-title"><i class="bi bi-lightning"></i> Ephys Details</h6>');
    html.push('<div class="info-grid two-col">');
    EPHYS_CONFIG._detailViewFeatures.forEach(function (feat) {
        var value = row[feat.key];
        if (typeof value === 'number') {
            html.push('<div class="info-item"><span class="info-label">' + feat.label + '</span><span class="info-value">' + (Math.round(value * 100) / 100) + '</span></div>');
        }
    });
    html.push('</div>');
    html.push('</div>');
    
    html.push('</div>'); // end right col
    html.push('</div>'); // end row
    html.push('</div>'); // end detail-container

    setTimeout(() => { maketrace(row) }, 1000);

    return html.join('');
}
function getUrlVars() {
    var vars = {};
    var parts = window.location.href.replace(/[?&]+([^=&]+)=([^&]*)/gi, function (m, key, value) {
        vars[key] = value;
    });
    return vars;
};

function getUrlParam(parameter, defaultvalue) {
    var urlparameter = defaultvalue;
    if (window.location.href.indexOf(parameter) > -1) {
        urlparameter = getUrlVars()[parameter];
    }
    return urlparameter;
};


//functions to open and close the report overlay
function on(ID) {
    document.getElementById("reportBox").outerHTML = '<iframe id="reportBox" src="https://docs.google.com/forms/d/e/1FAIpQLSeBwt-6nn1_Z72E7oc-3ynNVbJGFr5v3RI-q7zuneiKix53Jw/viewform?embedded=true&usp=pp_url&entry.773611234=' + ID + '" width="640" height="741" frameborder="0" marginheight="0" marginwidth="0">Loading…</iframe></div>'
    document.getElementById("overlay").style.display = "block";
}

function off() {
    document.getElementById("overlay").style.display = "none";
}


// cross filter function for parallel plot
function unpack(rows, key) {
                        return rows.map(function (row) {
                            return row[key];
                        });
                    }
function logunpack(rows, key) {
    return rows.map(function (row) {
        return Math.log10(row[key]);
    });
}
function catunpack(rows, key) {
    let arr_lab = rows.map(function (row) {
        return row[key];
    });
    let unique = arr_lab.filter((item, i, ar) => ar.indexOf(item) === i);
    return rows.map(function (row) {
        return unique.indexOf(row[key])
    });
}
function catlabel(rows, key) {
    let arr_lab = rows.map(function (row) {
        return row[key];
    });
    let unique = arr_lab.filter((item, i, ar) => ar.indexOf(item) === i);
    return unique;
}	
function filterByPlot(keys, ranges) {
    if (!ephysData) return;
    
    // Work with a copy to avoid mutating global data
    var data = ephysData.map(function(obj) { return Object.assign({}, obj); });

    // Build the dimension config list in the same order used by generateParallelPlot()
    var dimConfigs = _buildParallelDimConfigs();

    // Encode categorical columns onto each row
    dimConfigs.forEach(function (dc) {
        if (dc.type === 'categorical') {
            var encoded = catunpack(data, dc.key);
            data.forEach(function (obj, i) {
                obj[dc.key + '_enc'] = encoded[i];
            });
        }
    });

    // Dynamic filtering — iterate dimension configs in the same order as
    // the parallel-coords axes so the positional `ranges` array lines up.
    var newArray = data.filter(function (el) {
        for (var i = 0; i < dimConfigs.length; i++) {
            var dc = dimConfigs[i];
            var lo = ranges[i][0];
            var hi = ranges[i][1];

            if (dc.type === 'categorical') {
                var val = el[dc.key + '_enc'];
                if (val < lo || val > hi) return false;
            } else if (dc.scale === 'log') {
                // Parallel-coords axis is in log-space; convert bounds back
                if (el[dc.key] < Math.pow(10, lo) || el[dc.key] > Math.pow(10, hi)) return false;
            } else {
                if (el[dc.key] < lo || el[dc.key] > hi) return false;
            }
        }
        return true;
    });

    let result = newArray.map(function (a) { return a['cellID']; });
    $table.bootstrapTable('filterBy', { 'cellID': result });
}

function filterByID(ids) {
    if (typeof ids !== 'undefined') {
        $table.bootstrapTable('filterBy', { 'cellID': ids });
    }
    else if (ephysData) {
        ids = ephysData.map(function (a) { return a.cellID; });
        $table.bootstrapTable('filterBy', { 'cellID': ids });
    }
}
// Download a single NWB file from DANDI Archive
function downloadFromDandi(cellID) {
    alert('Downloads are temporarily unavailable. Please check back later.');
    return;
}


//function to generate plots
function maketrace(row) {
    var url = "./data/traces/" + row.internalID + ".csv"
    Plotly.d3.csv(url, function (rows) {
        data = []
        var i = 1
        var temp_t = rows.shift()
        delete temp_t[Object.keys(temp_t)[0,1]]
        timeseries = Object.keys(temp_t).map(function (e) {
                return temp_t[e]
            })
        rows.forEach(function (row) {

            var sweepname = row[Object.keys(row)[0]].toString() + ': ' + Math.round(row[Object.keys(row)[1]].toString()) + ' pA'
            delete row[Object.keys(row)[0,1]]
            var rowdata = Object.keys(row).map(function (e) {
                return row[e]
            })


            var trace = {
                type: 'scatter',                    // set the chart type
                mode: 'lines',                      // connect points with lines
                name: sweepname,
                y: rowdata,
                x: timeseries,
                hovertemplate: '%{x} S, %{y} mV',
                line: {                             // set the width of the line.
                    width: 1,
                    shape: 'spline',
                    smoothing: 0.5
                }

            };
            data.push(trace);
            i += 1;
        });



        var layout = {
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(250,250,250,1)',
            font: {
                family: 'system-ui, -apple-system, sans-serif',
                size: 11,
                color: '#495057'
            },
            yaxis: {
                title: {
                    text: "mV",
                    font: { size: 11 }
                },
                gridcolor: '#e9ecef',
                zerolinecolor: '#adb5bd'
            },
            xaxis: {
                dtick: 0.25,
                zeroline: false,
                title: {
                    text: "Time (s)",
                    font: { size: 11 }
                },
                gridcolor: '#e9ecef'
            },
            margin: { b: 45, r: 150, t: 20, l: 55 },
            hovermode: "closest",
            legend: {
                orientation: 'v',
                x: 1.02,
                y: 1,
                font: { size: 8 },
                bgcolor: 'rgba(255,255,255,0.95)',
                bordercolor: '#dee2e6',
                borderwidth: 1,
                tracegroupgap: 2
            },
            showlegend: true,
            autosize: true
        };
        document.getElementById(row.cellID).replaceChildren();
        Plotly.newPlot(document.getElementById(row.cellID), data, layout, { displaylogo: false, responsive: true });
    })

        ;
}
function makebar(row){
    var id = row.cellID
    
    var data_diff = {}
    for (var key in row) {
        if (key.includes('ID')){
            
        }
        else if (spec_keys.includes(key))  {
            
        }
        else{
            data_diff[key] = row[key]
        }
        
    };
    
    var trace1 = {
                x: Object.keys(data_diff),
                y: Object.values(data_diff),
                name: 'Cell Values',
                type: 'bar'
            };
    var trace2 = {
                x: Object.keys(means),
                y: Object.values(means),
                name: 'Data Means',
                type: 'bar'
            };
    var layout = {
        barmode: 'group',
        yaxis: {
        autorange: true
        },
        autosize: true,
        height: 200,
        margin: { r: 30, l:30, t:10, b:150 },
    }
    
    
    Plotly.newPlot(document.getElementById(id+'_bar'), [trace1, trace2],layout, { displaylogo: false, responsive: true });
}


//function to generate dynamic scatter plot
function generateScatterPlot(xFeature, yFeature) {
    if (!ephysData) return;
    
    // Feature display names derived from config
    var featureLabels = EPHYS_CONFIG._featureLabels;
    
    var rows = ephysData;
    
    var data = [];
    var colors = ['#ffb3ba', '#baffc9', '#ffdfba', '#bae1ff', '#7dd8e1'];
    
    rows.forEach(function (row) {
        var sweepname = row.cellID;
        
        // Only plot if both values exist and are not zero
        if (row[xFeature] != 0 && row[yFeature] != 0 && 
            row[xFeature] != undefined && row[yFeature] != undefined) {
            
            var trace = {
                type: 'scatter',
                mode: 'markers',
                name: sweepname,
                x: [parseFloat(row[xFeature])],
                y: [parseFloat(row[yFeature])],
                marker: {
                    colorscale: 'Bluered',
                    cmin: 0,
                    cmax: Math.max(...unpack(rows, xFeature)),
                    color: [parseFloat(row[xFeature])],
                    size: 8
                }
            };
            data.push(trace);
        }
    });
    
    var layout = {
        dragmode: 'lasso',
        colorway: 'Bluered',
        autosize: true,
        xaxis: { title: featureLabels[xFeature] || xFeature },
        yaxis: { title: featureLabels[yFeature] || yFeature },
        margin: { t: 10, b: 40, l: 50, r: 30 },
        showlegend: false
    };
    
    Plotly.newPlot('scatterPlot', data, layout, { displaylogo: false, responsive: true });
    
    var scatterPlotEl = document.getElementById("scatterPlot");
    scatterPlotEl.on('plotly_selected', function (eventData) {
        var ids = [];
        
        if (eventData && eventData.points) {
            eventData.points.forEach(function (pt) {
                ids.push(parseInt(pt.data.name));
            });
        } else {
            ids = undefined; //case of no selection
        }
        
        filterByID(ids);
    });
}


/**
 * Build the ordered list of dimension configs used by both
 * generateParallelPlot() and filterByPlot().  Keeping this in
 * one place ensures the positional indices always match.
 */
function _buildParallelDimConfigs() {
    var configs = [];

    // Numeric features with parallelPlot enabled
    EPHYS_CONFIG.features.forEach(function (f) {
        if (f.parallelPlot) {
            configs.push({
                key:       f.key,
                label:     f.key,        // parallel-coords uses data key as label
                range:     f.parallelPlot.range,
                scale:     f.parallelPlot.scale || 'linear',
                tickStep:  f.parallelPlot.tickStep,
                type:      'numeric'
            });
        }
    });

    // Categorical metadata with parallelPlot enabled
    EPHYS_CONFIG.metadata.forEach(function (m) {
        if (m.parallelPlot) {
            configs.push({
                key:       m.key,
                label:     m.key,
                tickCount: m.parallelPlot.tickCount || 6,
                type:      'categorical'
            });
        }
    });

    return configs;
}

function generateParallelPlot(colorFeature){
    if (!ephysData) return;
    
    var rows = ephysData;
    colorFeature = colorFeature || EPHYS_CONFIG.defaults.parallelColorBy;
    
    const range = (start, stop, step = 1) =>
            Array(Math.ceil((stop - start) / step)).fill(start).map((x, y) => x + y * step);
    const logrange = (start, stop, step = 1) =>
            Array(Math.ceil((stop - start) / step)).fill(start).map((x, y) => Math.round(10**(x + y * step)));

    // Build dimensions array from config
    var dimConfigs = _buildParallelDimConfigs();
    var dimensions = dimConfigs.map(function (dc) {
        if (dc.type === 'categorical') {
            var tickvals = [];
            for (var i = 0; i < dc.tickCount; i++) tickvals.push(i);
            return {
                label:    dc.label,
                tickvals: tickvals,
                ticktext: catlabel(rows, dc.key),
                values:   catunpack(rows, dc.key)
            };
        }
        // Numeric dimension
        var dim = {
            range:  dc.range,
            label:  dc.label,
            values: dc.scale === 'log' ? logunpack(rows, dc.key) : unpack(rows, dc.key)
        };
        if (dc.scale === 'log' && dc.tickStep) {
            dim.tickvals = range(dc.range[0], dc.range[1] + dc.tickStep, dc.tickStep);
            dim.ticktext = logrange(dc.range[0], dc.range[1] + dc.tickStep, dc.tickStep);
        }
        return dim;
    });

    // Colour by the selected feature (numeric or categorical)
    var colorByKey = colorFeature;
    var colorByLabel = EPHYS_CONFIG._featureLabels[colorByKey] || colorByKey;

    // Determine whether the colour-by key is categorical
    var isCategorical = EPHYS_CONFIG.metadata.some(function (m) {
        return m.key === colorByKey && m.type === 'categorical';
    });

    var lineConfig;
    if (isCategorical) {
        var catColors = catunpack(rows, colorByKey);
        var catLabels = catlabel(rows, colorByKey);
        var nCats = catLabels.length;
        // Qualitative palette (D3 Category10)
        var palette = [
            '#1f77b4','#ff7f0e','#2ca02c','#d62728','#9467bd',
            '#8c564b','#e377c2','#7f7f7f','#bcbd22','#17becf'
        ];
        // Build a discrete colorscale mapping [0..nCats-1] to palette entries
        var discreteScale = [];
        for (var ci = 0; ci < nCats; ci++) {
            var lo = ci / nCats;
            var hi = (ci + 1) / nCats;
            var c  = palette[ci % palette.length];
            discreteScale.push([lo, c]);
            discreteScale.push([hi, c]);
        }
        // Build tick positions at the centre of each band
        var tickvals = [];
        for (var ti = 0; ti < nCats; ti++) {
            tickvals.push(ti);
        }
        lineConfig = {
            colorscale: discreteScale,
            autocolorscale: false,
            color: catColors,
            cmin: 0,
            cmax: nCats - 1,
            showscale: true,
            colorbar: {
                title: { text: colorByLabel, font: { size: 10 }, side: 'right' },
                thickness: 15,
                len: 0.5,
                tickvals: tickvals,
                ticktext: catLabels
            }
        };
    } else {
        lineConfig = {
            colorscale: 'viridis',
            autocolorscale: false,
            color: unpack(rows, colorByKey),
            showscale: true,
            colorbar: {
                title: { text: colorByLabel, font: { size: 10 }, side: 'right' },
                thickness: 15,
                len: 0.5
            }
        };
    }

    var data = [{
        type: 'parcoords',
        pad: [80, 80, 80, 80],
        line: lineConfig,
        dimensions: dimensions
    }];

    var layout = {
        autosize: true,
        margin: { r: 80, l: 80, t: 60, b: 30 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        font: {
            family: 'system-ui, -apple-system, sans-serif',
            size: 11,
            color: '#495057'
        }
    };

    Plotly.newPlot('parallelCoordsPlot', data, layout, { displaylogo: false, responsive: true });
    var parallelCoordsEl = document.getElementById("parallelCoordsPlot");
    parallelCoordsEl.on('plotly_restyle', function (data) {
        var keys = [];
        var ranges = [];

        parallelCoordsEl.data[0].dimensions.forEach(function (d) {
            if (d.constraintrange === undefined) {
                keys.push(d.label);
                ranges.push([-9999, 9999]); //no filter applied, if values are ut
            }
            else {
                keys.push(d.label);
                var allLengths = d.constraintrange.flat();
                if (allLengths.length > 2) {
                    ranges.push([d.constraintrange[0][0], d.constraintrange[0][1]]); //return only the first filter applied per feature

                } else {
                    ranges.push(d.constraintrange);
                }


            } // => use this to find values are selected
        });

        filterByPlot(keys, ranges);
    });
}

function generateUMAPPlot(colorFeature) {
    if (!ephysData) return;

    colorFeature = colorFeature || EPHYS_CONFIG.defaults.umapColorBy;

    var featureLabels = EPHYS_CONFIG._featureLabels;

    // Only plot rows that have valid UMAP coordinates
    var rows = ephysData.filter(function (r) {
        return r.UMAP1 != null && r.UMAP2 != null;
    });

    var xVals     = rows.map(function (r) { return r.UMAP1; });
    var yVals     = rows.map(function (r) { return r.UMAP2; });
    var colorVals = rows.map(function (r) { return parseFloat(r[colorFeature]); });
    var cellIDs   = rows.map(function (r) { return r.cellID; });

    var trace = {
        type: 'scatter',
        mode: 'markers',
        x: xVals,
        y: yVals,
        text: cellIDs,
        customdata: cellIDs,
        marker: {
            color: colorVals,
            colorscale: 'Viridis',
            showscale: true,
            colorbar: {
                title: { text: featureLabels[colorFeature] || colorFeature, font: { size: 10 }, side: 'right' },
                thickness: 8,
                len: 0.4,
                tickfont: { size: 9 }
            },
            size: 7,
            opacity: 0.85
        },
        hovertemplate: '<b>%{text}</b><br>UMAP1: %{x:.2f}<br>UMAP2: %{y:.2f}<extra></extra>'
    };

    var layout = {
        dragmode: 'lasso',
        autosize: true,
        xaxis: { title: 'UMAP 1', zeroline: false },
        yaxis: { title: 'UMAP 2', zeroline: false },
        margin: { b: 40, r: 80, t: 20, l: 50 }
    };

    Plotly.newPlot('umapPlot', [trace], layout, { displaylogo: false, responsive: true });

    var $umapPlotEl = document.getElementById('umapPlot');
    $umapPlotEl.on('plotly_selected', function (eventData) {
        var ids;
        if (eventData && eventData.points && eventData.points.length > 0) {
            ids = eventData.points.map(function (pt) { return pt.customdata; });
        } else {
            ids = undefined;
        }
        filterByID(ids);
    });
}

function redraw_scatter(){
    Plotly.restyle(document.getElementById("scatterPlot"));
}

//function to generate plots
function generate_all_graphs(){
    



    // feature driven scatter plot - generate initial plot
    generateScatterPlot(EPHYS_CONFIG.defaults.scatterX, EPHYS_CONFIG.defaults.scatterY);
    
    // Add event listeners for dropdown changes
    $('#scatterXAxis').on('change', function() {
        var xFeature = $('#scatterXAxis').val();
        var yFeature = $('#scatterYAxis').val();
        generateScatterPlot(xFeature, yFeature);
    });
    
    $('#scatterYAxis').on('change', function() {
        var xFeature = $('#scatterXAxis').val();
        var yFeature = $('#scatterYAxis').val();
        generateScatterPlot(xFeature, yFeature);
    });

    // Generate parallel plot
    generateParallelPlot();

    $('#parallelColorBy').on('change', function () {
        generateParallelPlot($('#parallelColorBy').val());
    });

    // Generate UMAP plot
    generateUMAPPlot();

    $('#umapColorBy').on('change', function () {
        generateUMAPPlot($('#umapColorBy').val());
    });

    //wait a few seconds then trigger resize on the scatterplots to make them responsive
    setTimeout(function () { resizeAllPlots(); }, 2000);

    //listen for clicks on filter buttons to resize plots after collapse transition
    $('#filterParallelBtn').on('click', function() {
        setTimeout(function () { resizeAllPlots(); }, 500);
    });
    $('#filterScatterBtn').on('click', function() {
        setTimeout(function () { resizeAllPlots(); }, 500);
    });

    // Debounced window resize handler so plots redraw at breakpoint transitions
    var resizeTimer;
    window.addEventListener('resize', function () {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function () { resizeAllPlots(); }, 250);
    });
}

function resizeAllPlots() {
    var ids = ['parallelCoordsPlot', 'scatterPlot', 'umapPlot'];
    ids.forEach(function (id) {
        var el = document.getElementById(id);
        if (el && el.data) { Plotly.Plots.resize(el); }
    });
}
