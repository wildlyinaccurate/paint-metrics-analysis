# Paint Metrics Analysis

Raw data for the SpeedCurve paint metric analysis, and accompanying analysis script.

## Requirements

 * Python 3.6+
 * Plotly (`pip install plotly`)
 * NumPy (`pip install numpy`)
 * SciPy (`pip install scipy`)

## Running the analysis

There are two sets of data included in this repository:

- The set in `paint-metrics.json` is gathered from newer SpeedCurve test agents that capture video at 10 FPS. Due to this low framerate, the start render times in this data set are only accurate to within 100ms.
- The set in `paint-metrics-hires.json` is gathered from older SpeedCurve test agents that capture video at a higher framerate (60 FPS?). The start render times in this data set are more accurate.

Despite this discrepancy in start render resolution, both data sets show similar distributions of paint timing metric deltas.

To run the analysis, run `paint-metric-analysis.py` with the filename of the dataset you want to use:

```
python paint-metric-analysis.py paint-metrics.json

# Or on some systems:
python3 paint-metric-analysis.py paint-metrics.json
```

This will output some aggregate stats, and also generate three HTML files containing frequency distributions of the metric values themselves as well as the deltas between start render and FP/FCP.
