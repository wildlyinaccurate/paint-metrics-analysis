import json
import plotly.offline as py
import plotly.graph_objs as go
import sys
from math import floor
from statistics import mean, harmonic_mean

if len(sys.argv) < 2:
    print('Usage: paint-metric-analysis.py <filename>')
    exit()

filename = sys.argv[1]

f = open(filename, 'r')
data = json.load(f)
f.close()


def percentile(xs, n):
    return xs[int(floor(len(xs) * n))]

# Metric values across all URLs, excluding values over a given percentile


def values_without_outliers(metric, outlier_percentile=0.95):
    all_values = [item for url in data['urls'] for item in url[metric]]
    outlier_threshold = percentile(all_values, outlier_percentile)
    return [value for value in all_values if value < outlier_threshold]


def histogram_trace(data, label, bin_size):
    return go.Histogram(name=label, x=data, xbins=dict(size=bin_size, start=min(data), end=max(data)), opacity=0.75)


def generate_histogram(outfile, bin_size, data, labels):
    data = [histogram_trace(series, label, bin_size)
            for series, label in zip(data, labels)]
    layout = go.Layout(barmode='overlay')
    fig = go.Figure(data=data, layout=layout)
    py.plot(fig, filename=outfile, auto_open=False)
    print('Generated %s' % outfile)


renders = values_without_outliers('render')
fps = values_without_outliers('fp')
fcps = values_without_outliers('fcp')
fmps = values_without_outliers('fmp')

generate_histogram(filename.replace('.json', '-distribution.html'), 50, [renders, fps, fcps], [
    'Start Render', 'First Paint', 'First Contentful Paint'])

fp_deltas = [fp - render for fp, render in zip(fps, renders)]
fcp_deltas = [fcp - render for fcp, render in zip(fcps, renders)]
fmp_deltas = [fmp - render for fmp, render in zip(fmps, renders)]

generate_histogram(filename.replace('.json', '-deltas.html'), 20, [fp_deltas, fcp_deltas], [
    'First Paint Delta', 'First Contentful Paint Delta'])

mean_render = mean(renders)
mean_fp = mean(fps)
mean_fcp = mean(fcps)
mean_fmp = mean(fmps)

hmean_render = harmonic_mean(renders)
hmean_fp = harmonic_mean(fps)
hmean_fcp = harmonic_mean(fcps)
hmean_fmp = harmonic_mean(fmps)

print('\nAggregate stats:\n')

print('|                                 Mean                                         |')
print('| Start Render | First Paint | First Contentful Paint | First Meaningful Paint |')
print('|--------------|-------------|------------------------|------------------------|')
print('|         %d | %d (%d) |            %d (%d) |             %d (%d) |' % (
    mean_render,
    mean_fp,
    mean_fp - mean_render,
    mean_fcp,
    mean_fcp - mean_render,
    mean_fmp,
    mean_fmp - mean_render,
))

print('')
print('|                            Harmonic Mean                                     |')
print('| Start Render | First Paint | First Contentful Paint | First Meaningful Paint |')
print('|--------------|-------------|------------------------|------------------------|')
print('|         %d | %d (%d) |            %d (%d) |              %d (%d) |' % (
    hmean_render,
    hmean_fp,
    hmean_fp - hmean_render,
    hmean_fcp,
    hmean_fcp - hmean_render,
    hmean_fmp,
    hmean_fmp - hmean_render,
))

fp_deltas_abs = sorted(list(map(abs, fp_deltas)))
fcp_deltas_abs = sorted(list(map(abs, fcp_deltas)))
fmp_deltas_abs = sorted(list(map(abs, fmp_deltas)))

print('')
print('|                                 Deltas                                    |')
print('| Stat      | First Paint | First Contentful Paint | First Meaningful Paint |')
print('|-----------|-------------|------------------------|------------------------|')
print('| avg       |        %s |                   %s |                   %s |' % (
    str(round(mean(fp_deltas_abs))).rjust(4, ' '),
    str(round(mean(fcp_deltas_abs))).rjust(4, ' '),
    str(round(mean(fmp_deltas_abs))).rjust(4, ' '),
))
print('| med (50)  |        %s |                   %s |                   %s |' % (
    str(round(percentile(fp_deltas_abs, 0.5))).rjust(4, ' '),
    str(round(percentile(fcp_deltas_abs, 0.5))).rjust(4, ' '),
    str(round(percentile(fmp_deltas_abs, 0.5))).rjust(4, ' '),
))
print('| 70        |        %s |                   %s |                   %s |' % (
    str(round(percentile(fp_deltas_abs, 0.70))).rjust(4, ' '),
    str(round(percentile(fcp_deltas_abs, 0.70))).rjust(4, ' '),
    str(round(percentile(fmp_deltas_abs, 0.70))).rjust(4, ' '),
))
print('| 80        |        %s |                   %s |                   %s |' % (
    str(round(percentile(fp_deltas_abs, 0.80))).rjust(4, ' '),
    str(round(percentile(fcp_deltas_abs, 0.80))).rjust(4, ' '),
    str(round(percentile(fmp_deltas_abs, 0.80))).rjust(4, ' '),
))
print('| 90        |        %s |                   %s |                   %s |' % (
    str(round(percentile(fp_deltas_abs, 0.9))).rjust(4, ' '),
    str(round(percentile(fcp_deltas_abs, 0.9))).rjust(4, ' '),
    str(round(percentile(fmp_deltas_abs, 0.9))).rjust(4, ' '),
))
print('| 95        |        %s |                   %s |                   %s |' % (
    str(round(percentile(fp_deltas_abs, 0.95))).rjust(4, ' '),
    str(round(percentile(fcp_deltas_abs, 0.95))).rjust(4, ' '),
    str(round(percentile(fmp_deltas_abs, 0.95))).rjust(4, ' '),
))
