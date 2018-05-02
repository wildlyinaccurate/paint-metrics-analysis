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


def metric_values(metric):
    return [item for url in data['urls'] for item in url[metric]]


def remove_outliers(values, outlier_threshold):
    return [value for value in values if outlier_threshold > value > -(outlier_threshold)]


def histogram_trace(data, label, bin_size, xstart=None, xend=None):
    if xstart is None:
        xstart = min(data)
    if xend is None:
        xend = max(data)
    return go.Histogram(name=label, x=data, xbins=dict(size=bin_size, start=xstart, end=xend), opacity=0.75)


def generate_histogram(outfile, data, labels, bin_size, xstart=None, xend=None, tick_interval=200):
    data = [histogram_trace(series, label, bin_size, xstart, xend)
            for series, label in zip(data, labels)]
    layout = go.Layout(barmode='overlay', font=dict(size=28), legend=dict(x=0.77), xaxis=dict(dtick=tick_interval))
    fig = go.Figure(data=data, layout=layout)
    py.plot(fig, filename=outfile, auto_open=False)
    print('Generated %s' % outfile)


renders = metric_values('render')
fps = metric_values('fp')
fcps = metric_values('fcp')
fmps = metric_values('fmp')

renders_filtered = remove_outliers(renders, percentile(renders, 0.95))
fps_filtered = remove_outliers(fps, percentile(fps, 0.95))
fcps_filtered = remove_outliers(fcps, percentile(fcps, 0.95))
fmps_filtered = remove_outliers(fmps, percentile(fmps, 0.95))

# Seeing a distribution of all of the metric values can show how strongly correlated
# the metrics are. We exclude extreme outliers (>95th percentile) from the metric
# values, in an attempt to filter out potentially-bogus test results.
generate_histogram(filename.replace('.json', '-distribution.html'), [renders_filtered, fps_filtered, fcps_filtered], [
                   'Start Render', 'First Paint', 'First Contentful Paint'], bin_size=50)

# Calculating the delta between the paint metrics and start render gives us a better
# insight into how accurate browsers are at determining when pixels are rendered to
# the screen. Note that deltas of >2000ms are removed to reduce noise.
fp_deltas = remove_outliers(
    [fp - render for fp, render in zip(fps, renders)], 2000)
fcp_deltas = remove_outliers(
    [fcp - render for fcp, render in zip(fcps, renders)], 2000)
fmp_deltas = [fmp - render for fmp, render in zip(fmps, renders)]

generate_histogram(filename.replace('.json', '-deltas.html'), [fp_deltas, fcp_deltas], [
                   'First Paint Delta', 'First Contentful Paint Delta'], bin_size=20, xstart=-1000, xend=1000)

# It's also useful to calculate the deltas as a percentage of the start render time,
# since there is significant variation in the metric values. Deltas of >100% are removed
# to reduce noise.
fp_deltas_rel = remove_outliers(
    [(fp - render) / render for fp, render in zip(fps, renders)], 1)
fcp_deltas_rel = remove_outliers(
    [(fcp - render) / render for fcp, render in zip(fcps, renders)], 1)
fmp_deltas_rel = remove_outliers(
    [(fmp - render) / render for fmp, render in zip(fmps, renders)], 1)

generate_histogram(filename.replace('.json', '-deltas-relative.html'), [fp_deltas_rel, fcp_deltas_rel], [
    'First Paint Delta', 'First Contentful Paint Delta'], bin_size=0.01, xstart=-1, xend=1, tick_interval=0.1)

# Seeing an average value for each of the metrics gives a rough but useful view
# of how different the metrics are.
mean_render = mean(renders)
mean_fp = mean(fps)
mean_fcp = mean(fcps)
mean_fmp = mean(fmps)

# Taking the harmonic mean can help to sanity-check the outlier filtering
hmean_render = harmonic_mean(renders)
hmean_fp = harmonic_mean(fps)
hmean_fcp = harmonic_mean(fcps)
hmean_fmp = harmonic_mean(fmps)

# Taking the deltas as absolute values allows us to make some assertions about
# how frequently the paint metrics are within X milliseconds of start render.
fp_deltas_abs = sorted(list(map(abs, fp_deltas)))
fcp_deltas_abs = sorted(list(map(abs, fcp_deltas)))
fmp_deltas_abs = sorted(list(map(abs, fmp_deltas)))


def pad(i, width=4):
    return str(round(i)).rjust(width, ' ')


print('')
print('|                                 Deltas                                    |')
print('| Stat      | First Paint | First Contentful Paint | First Meaningful Paint |')
print('|-----------|-------------|------------------------|------------------------|')
print('| avg       |        %s |                   %s |                   %s |' % (
    str(round(mean(fp_deltas_abs))).rjust(4, ' '),
    str(round(mean(fcp_deltas_abs))).rjust(4, ' '),
    str(round(mean(fmp_deltas_abs))).rjust(4, ' '),
))
for pct in [10, 25, 50, 70, 80, 90, 95]:
    print('| %s        |        %s |                   %s |                   %s |' % (
        str(pct),
        pad(percentile(fp_deltas_abs, pct / 100)),
        pad(percentile(fcp_deltas_abs, pct / 100)),
        pad(percentile(fmp_deltas_abs, pct / 100)),
    ))

fp_deltas_rel_abs = sorted(list(map(abs, fp_deltas_rel)))
fcp_deltas_rel_abs = sorted(list(map(abs, fcp_deltas_rel)))
fmp_deltas_rel_abs = sorted(list(map(abs, fmp_deltas_rel)))

print('')
print('|                            Deltas (Relative)                              |')
print('| Stat      | First Paint | First Contentful Paint | First Meaningful Paint |')
print('|-----------|-------------|------------------------|------------------------|')
print('| avg       |       %s%% |                  %s%% |                  %s%% |' % (
    pad(mean(fp_deltas_rel_abs) * 100),
    pad(mean(fcp_deltas_rel_abs) * 100),
    pad(mean(fmp_deltas_rel_abs) * 100),
))
for pct in [10, 25, 50, 70, 80, 90, 95]:
    print('| %s        |       %s%% |                  %s%% |                  %s%% |' % (
        str(pct),
        pad(percentile(fp_deltas_rel_abs, pct / 100) * 100),
        pad(percentile(fcp_deltas_rel_abs, pct / 100) * 100),
        pad(percentile(fmp_deltas_rel_abs, pct / 100) * 100),
    ))

print('')
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
print('')
