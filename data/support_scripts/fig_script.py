# %%
import json
import re
from pathlib import Path
import numpy as np


def load_ephys_config(config_path=None):
    """
    Parse js/ephysConfig.js and return the config as a Python dict.
    
    Extracts the EPHYS_CONFIG object literal from the JS file,
    converts JS syntax to valid JSON, and returns a dict with keys:
      features, metadata, detailViewFeatures, defaults
    
    Parameters
    ----------
    config_path : str or Path, optional
        Path to ephysConfig.js.  Defaults to ../../js/ephysConfig.js
        (relative to this notebook's location).
    """
    if config_path is None:
        config_path = Path(__file__).parent / '../../js/ephysConfig.js' \
            if '__file__' in dir() else Path('../../js/ephysConfig.js')
    
    text = Path(config_path).read_text(encoding='utf-8')
    
    # Extract the object literal assigned to EPHYS_CONFIG
    match = re.search(r'var\s+EPHYS_CONFIG\s*=\s*(\{)', text)
    if not match:
        raise ValueError('Could not find EPHYS_CONFIG in ' + str(config_path))
    
    # Walk forward from the opening brace, counting braces to find the end
    start = match.start(1)
    depth = 0
    end = start
    for i, ch in enumerate(text[start:], start):
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    
    js_obj = text[start:end]
    
    # Convert JS object literal → valid JSON
    # 1. Strip single-line comments  (// ...)
    js_obj = re.sub(r'//[^\n]*', '', js_obj)
    # 2. Strip multi-line comments   (/* ... */)
    js_obj = re.sub(r'/\*.*?\*/', '', js_obj, flags=re.DOTALL)
    # 3. Replace single quotes with double quotes
    js_obj = js_obj.replace("'", '"')
    # 4. Quote unquoted keys:  key: value  →  "key": value
    js_obj = re.sub(r'(?<=[{,\n])\s*([A-Za-z_]\w*)\s*:', r' "\1":', js_obj)
    # 5. Convert JS booleans / null
    js_obj = re.sub(r'\bfalse\b', 'false', js_obj)
    js_obj = re.sub(r'\btrue\b', 'true', js_obj)
    # 6. Remove trailing commas before } or ]
    js_obj = re.sub(r',\s*([}\]])', r'\1', js_obj)
    
    config = json.loads(js_obj)
    return config


def build_parallel_dimensions(config, dataframe):
    """
    Build a list of Plotly parallel-coordinates dimension dicts
    from the parsed EPHYS_CONFIG and a pandas DataFrame.
    
    Handles linear features, log-scaled features, and categorical
    metadata — exactly mirroring what the JS website renders.
    """
    dims = []

    # Numeric features
    for f in config['features']:
        pp = f.get('parallelPlot')
        if not pp:
            continue
        
        d = dict(label=f['key'])
        r = pp['range']
        d['range'] = r
        
        if pp.get('scale') == 'log':
            d['values'] = np.log10(dataframe[f['key']])
            step = pp.get('tickStep', 0.5)
            ticks = np.arange(r[0], r[1] + step, step)
            d['tickvals'] = ticks.tolist()
            d['ticktext'] = [str(int(10**x)) for x in ticks]
        else:
            d['values'] = dataframe[f['key']]
        
        dims.append(d)

    # Categorical metadata
    for m in config.get('metadata', []):
        pp = m.get('parallelPlot')
        if not pp:
            continue
        col = m['key']
        if col not in dataframe.columns:
            continue
        categories = dataframe[col].unique()
        cat_map = {cat: i for i, cat in enumerate(categories)}
        dims.append(dict(
            label=col,
            tickvals=list(range(len(categories))),
            ticktext=list(categories),
            values=[cat_map[x] for x in dataframe[col]]
        ))

    return dims


# ── Quick test ───────────────────────────────────────────────────────────
config = load_ephys_config(config_path=r".\js\ephysConfig.js")
print("Loaded config with", len(config['features']), "features and",
      len(config.get('metadata', [])), "metadata columns.")
print("Parallel-plot features:",
      [f['key'] for f in config['features'] if f.get('parallelPlot')])

# %%
import pandas as pd
import plotly.graph_objects as go


def plot_parallel_coordinates(dataframe, config, output_file='parallel_coordinates.pdf'):
    """
    Generate a parallel-coordinates plot using dimensions
    pulled from ephysConfig.js via build_parallel_dimensions().
    """
    dimensions = build_parallel_dimensions(config, dataframe)

    color_by = config.get('defaults', {}).get('parallelColorBy', 'AP halfwidth')
    color_label = next(
        (f['label'] for f in config['features'] if f['key'] == color_by),
        color_by
    )

    fig = go.Figure(data=
        go.Parcoords(
            line=dict(
                colorscale='Viridis',
                color=dataframe[color_by],
                showscale=True,
                colorbar=dict(
                    title={ 'text': color_by, 'font': { 'size': 7 }, 'side': 'right' },
                    thickness=15,
                    len=0.5
                )
            ),
            dimensions=dimensions
        )
    )

    fig.update_layout(
        autosize=True,
        margin=dict(r=80, l=80, t=60, b=30),
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(
            family='system-ui, -apple-system, sans-serif',
            size=7*4.48,  # scale font size with image scale for better readability
            color='#495057'
        )
    )

    print("Generated parallel coordinates plot.")
    width =  1200 #172mm @ 300dpi
    height = int(width * 1/4) # Aspect ratio of 5:1 seems to work well for ~20 dimensions
    fig.write_image(output_file, format='pdf', width=width, height=height, scale=4, validate=True)

    fig.write_image(output_file.replace('.pdf', '.svg'), format='svg',  width=width, height=height, scale=2.5, validate=True) 
    print(f"Plot saved to {output_file}")

    return fig


# Load data and generate the plot
data = pd.read_csv('C:\\Users\\SMest\\source\\pctd\\data\\box2_ephys.csv')
fig = plot_parallel_coordinates(data, config)
fig.show()

# %%
#also plot the UMAP with the same color scheme

# %%
def plot_umap(dataframe, config, output_file='umap_plot.pdf'):
    umapX = 'UMAP1'
    umapY = 'UMAP2'
    color_by = config.get('defaults', {}).get('parallelColorBy', 'AP halfwidth')
    color_label = next(
        (f['label'] for f in config['features'] if f['key'] == color_by),
        color_by
    )
    fig = go.Figure(data=go.Scatter(
        x=dataframe[umapX],
        y=dataframe[umapY],
        mode='markers',
        marker=dict(
            size=5,
            color=dataframe[color_by],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(
                title={ 'text': color_label, 'font': { 'size': 7 }, 'side': 'right' },
                thickness=15,
                len=0.5
            )
        )
    ))
    fig.update_layout(
        autosize=True,
        margin=dict(r=80, l=80, t=60, b=30),
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(
            family='system-ui, -apple-system, sans-serif',
            size=7,
            color='#495057'
        )
    )
    print("Generated UMAP plot.")
    width = 482
    height = 400
    fig.write_image(output_file, format='pdf', width=width, height=height, scale=4, validate=True)
    fig.write_image(output_file.replace('.pdf', '.svg'), format='svg', width=width, height=height, scale=4, validate=True)
    print(f"UMAP plot saved to {output_file}")
    return fig
fig = plot_umap(data, config)
fig.show()



