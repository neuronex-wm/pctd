// Declare global variables outside $(document).ready()
var zip;
var $table;
var $graphDiv;
var selections = [];
var ephysData = null;
var timeseries;
// Derived from EPHYS_CONFIG (see js/ephysConfig.js)
var spec_keys = EPHYS_CONFIG._metadataKeys;
var means = EPHYS_CONFIG._means;

$(document).ready(function() {
    // Initialize global variables that depend on DOM
    zip = new JSZip();
    $table = $('#table');
    $graphDiv = $('#graphDiv');
    
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

    
});


var Promise = window.Promise;
if (!Promise) {
    Promise = JSZip.external.Promise;
}
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
    /*return '<div class="dropright"><button class="btn btn-secondary dropdown-toggle" type="button" id="dropdownMenuButton" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false"  onclick="showtoast()"">Download</button><div class="dropdown-menu"> <button id="dlzip" class="dropdown-item" href="#" class="btn btn-primary">Download (zip/abf)</button> <button id="dlnwb" class="dropdown-item" href="#">Download (NWB)</button></div></div>'; */
    return '<div class="dropright"><button class="btn btn-secondary dropdown-toggle" type="button" id="dropdownMenuButton" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">Download</button><div class="dropdown-menu"> <a class="dropdown-item" href="http://primatedatabase.com/download?cell=' + row.internalID + '.abf" target="_blank" class="btn btn-primary">Download (abf)</a> <a class= "dropdown-item" href="http://primatedatabase.com/download?cell=' + row.internalID + '.nwb" target="_blank">Download (NWB)</a></div></div>';
}
function morphFormatter(value, row) {
    if (value) {

        var morphID = value.split("=")
        return '<a href="http://primatedatabase.com' + value + '" class="btn btn-primary" style="margin: 5px">View Cell</a> <a href="http://primatedatabase.com/swc/' + morphID[1] + '" class="btn btn-secondary" style="margin: 5px">Download Morph</a> ';
    }
    else { return; }
}

function detailFormatter(index, row) {
    var html = []
    var url = "https://ptcd-traces.s3.us-east-2.amazonaws.com/" + row.cellID + ".csv"
    var plot_bool = doesFileExist(url)

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
// get table seletctions
function getIdSelections() {

    var ids = $.map($table.bootstrapTable('getSelections'), function (row) {

        return row.ID
    })

    return ids;
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
function urlToPromise(url) {
    return new Promise(function (resolve, reject) {
        JSZipUtils.getBinaryContent(url, function (err, data) {
            if (err) {
                reject(err);
            } else {
                resolve(data);
            }
        });
    });
}
function resetMessage() {
    $("#dlsel")
        .text("");
}
function showtoast() {
    $('.toast').toast('show');
}
function showMessage(text) {
    resetMessage();
    $("#dlsel")
        .html(text);
}
$(function () {
    $table.on('check.bs.table uncheck.bs.table ' +
        'check-all.bs.table uncheck-all.bs.table',
        function () {

            selections = getIdSelections()

        })
    $("#dlsel").on("click", function () {

        var ids
        $("#dlsel").html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generating ZIP...')
        myWindow = window.open("http://primatedatabase.com/download", "download", "width=200, height=100");
        myWindow.close();
        ids = getIdSelections();

        $.each(ids, function (idu, a) {
            var dlurl = "https://d3baje3o5bqx2r.cloudfront.net/" + a + ".nwb"
            var filename = a + ".nwb";
            zip.file(filename, urlToPromise(dlurl), { binary: true });

        });
        zip.generateAsync({ type: "blob" }, function updateCallback(metadata) {
            var msg = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generating ZIP... Progression : ' + metadata.percent.toFixed(2) + " %";
            if (metadata.currentFile) {
                msg += ", current file = " + metadata.currentFile;
            }
            showMessage(msg);

        })
            .then(function callback(blob) {

                // see FileSaver.js
                saveAs(blob, "dataset.zip");

                showMessage("Download Selected (Zip)");
            }, function (e) {

            });

        return false;

    })
    $('#dropdownMenuButton').hover(function () {

        $('.toast').toast('show');
    });
    $("#dlsel").click(function(){
            
            $('.toast').toast('show');
            });
    $("#dlall").click(function(){
    
            $('.toast').toast('show');
            });

    $('[data-toggle="tooltip"]').tooltip()

})

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
    
    Plotly.newPlot('graphDiv_scatter2', data, layout, { displaylogo: false, responsive: true });
    
    var graphDiv = document.getElementById("graphDiv_scatter2");
    graphDiv.on('plotly_selected', function (eventData) {
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

function generateParallelPlot(){
    if (!ephysData) return;
    
    var rows = ephysData;
    
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

    // Colour by the configured default feature
    var colorByKey = EPHYS_CONFIG.defaults.parallelColorBy;
    var colorByLabel = EPHYS_CONFIG._featureLabels[colorByKey] || colorByKey;

    var data = [{
        type: 'parcoords',
        pad: [80, 80, 80, 80],
        line: {
            colorscale: "viridis",
            autocolorscale: false,
            color: unpack(rows, colorByKey),
            showscale: true,
            colorbar: {
                title: colorByLabel,
                thickness: 15,
                len: 0.5
            }
        },
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

    Plotly.newPlot('graphDiv', data, layout, { displaylogo: false, responsive: true });
    var graphDiv = document.getElementById("graphDiv");
    graphDiv.on('plotly_restyle', function (data) {
        var keys = [];
        var ranges = [];

        graphDiv.data[0].dimensions.forEach(function (d) {
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

function generateUMAPPlot(){
    //umap plot
    Plotly.d3.csv('data/UMAP4website.csv', function (err, rows) {

        function unpack(rows, key) {
            return rows.map(function (row) {
                return row[key];
            });
        }
        data = []
        m_trace_x = []
        m_trace_y = []
        h_trace_x = []
        h_trace_y = []
        var colors = ['#f59582', '#f0320c', '#274f1b', '#d6b376', '#18c912', '#58d4d6', '#071aeb', '#000000']
        rows.forEach(function (row) {
            var rowdata = Object.keys(row).map(function (e) {
                return row[e]
            })
            var timeseries = Object.keys(row);

            if ((row.labels.includes("Macaca") != true) && (row.labels.includes("Callithrix") != true)) {
                m_trace_y = m_trace_y.concat([row.X2])
                m_trace_x = m_trace_x.concat([row.X1])


            } else if (row.labels.includes("Macaca") || row.labels.includes("Callithrix")) {
                var sweepname = row.IDs
                var trace = {
                    type: 'scatter',                    // set the chart type
                    mode: 'markers',                      // connect points with lines
                    name: sweepname,
                    y: [row.X2],
                    x: [row.X1],

                };
                data.push(trace);
            }



        });
        var m_trace = {
            type: 'scatter',                    // set the chart type
            mode: 'markers',                      // connect points with lines
            name: 'mouse data',
            y: m_trace_y,
            x: m_trace_x,
            marker: {
                color: '#D3D3D3',
                opacity: 0.55,
            },

        };
        var h_trace = {
            type: 'scatter',                    // set the chart type
            mode: 'markers',                      // connect points with lines
            name: 'human data',
            y: h_trace_y,
            x: h_trace_x,
            marker: {
                color: '#707070',
                opacity: 0.55,
            }

        };
        data = data.concat(m_trace, h_trace);

        var layout = {
            dragmode: 'lasso',
            autosize: true,
            margin: {                           // update the left, bottom, right, top margin
                b: 20, r: 10, t: 20, l: 40
            },

        };

        Plotly.react('graphDiv_scatter4', data, layout, { displaylogo: false, responsive: true });
        var graphDiv5 = document.getElementById("graphDiv_scatter4")
        graphDiv5.on('plotly_selected', function (eventData) {
            var ids = []
            var ranges = []
            if (typeof eventData !== 'undefined') {

                eventData.points.forEach(function (pt) {


                    ids.push(parseInt(pt.data.name));
                });
            }
            else {
                console.log(ids)
                ids = undefined
            }
            filterByID(ids);
        });
    });
}

function redraw_scatter(){
    Plotly.restyle(document.getElementById("graphDiv_scatter2"));
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

    // Generate UMAP plot
    //generateUMAPPlot();

    //wait a few seconds then trigger resize on the scatterplots to make them responsive
    setTimeout(() => { Plotly.Plots.resize(document.getElementById("graphDiv_scatter2")); }, 2000);


    //listen for clicks on filter_btn2 to resize scatter plot
    $('#filter_btn2').on('click', function() {
        setTimeout(() => { Plotly.Plots.resize(document.getElementById("graphDiv_scatter2")); }, 500);
    });
}
