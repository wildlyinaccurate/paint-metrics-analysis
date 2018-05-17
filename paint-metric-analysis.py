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
    return sorted(xs)[int(floor(len(xs) * n))]


def metric_values(metric):
    return [item for url in data['urls'] for item in url[metric]]


def histogram_trace(data, label, bin_size, xstart=None, xend=None):
    if xstart is None:
        xstart = min(data)
    if xend is None:
        xend = max(data)
    return go.Histogram(name=label, x=data, xbins=dict(size=bin_size, start=xstart, end=xend), opacity=0.75)


def generate_histogram(outfile, data, labels, bin_size, xstart=None, xend=None, tick_interval=200):
    data = [histogram_trace(series, label, bin_size, xstart, xend)
            for series, label in zip(data, labels)]
    layout = go.Layout(barmode='overlay', font=dict(
        size=28), legend=dict(x=0.77), xaxis=dict(dtick=tick_interval))
    fig = go.Figure(data=data, layout=layout)
    py.plot(fig, filename=outfile, auto_open=False)
    print('Generated %s' % outfile)

#
# Distribution plots
#


renders = metric_values('render')
fps = metric_values('fp')
fcps = metric_values('fcp')
fmps = metric_values('fmp')

# Seeing a distribution of all of the metric values can show how strongly correlated
# the metrics are.
generate_histogram(filename.replace('.json', '-distribution.html'), [renders, fps, fcps], [
                   'Start Render', 'First Paint', 'First Contentful Paint'], bin_size=50, xend=percentile(fcps, 0.95))

# Calculating the delta between the paint metrics and start render gives us a better
# insight into how accurate browsers are at determining when pixels are rendered to
# the screen.
fp_deltas = [fp - render for fp, render in zip(fps, renders)]
fcp_deltas = [fcp - render for fcp, render in zip(fcps, renders)]
fmp_deltas = [fmp - render for fmp, render in zip(fmps, renders)]

generate_histogram(filename.replace('.json', '-deltas.html'), [fp_deltas, fcp_deltas], [
                   'First Paint Delta', 'First Contentful Paint Delta'], bin_size=20, xstart=-1000, xend=1000)

# Just for fun, we can see how different FCP is to FP
fp_fcp_deltas = [fcp - fp for fp, fcp in zip(fps, fmps)]

generate_histogram(filename.replace('.json', '-fp-fcp-deltas.html'), [fp_fcp_deltas], [
                   'FCP / FP delta'], bin_size=50, xstart=-2000, xend=2000)

# It's also useful to calculate the deltas as a percentage of the start render time,
# since there is significant variation in the metric values.
fp_deltas_rel = [(fp - render) / render for fp, render in zip(fps, renders)]
fcp_deltas_rel = [(fcp - render) / render for fcp,
                  render in zip(fcps, renders)]
fmp_deltas_rel = [(fmp - render) / render for fmp,
                  render in zip(fmps, renders)]

generate_histogram(filename.replace('.json', '-deltas-relative.html'), [fp_deltas_rel, fcp_deltas_rel], [
    'First Paint Delta', 'First Contentful Paint Delta'], bin_size=0.01, xstart=-1, xend=1, tick_interval=0.1)


#
# Aggregate metrics
#

def pad(i, width=4):
    return str(round(i)).rjust(width, ' ')


def absolute_values(xs):
    return list(map(abs, xs))


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
fp_deltas_abs = absolute_values(fp_deltas)
fcp_deltas_abs = absolute_values(fcp_deltas)
fmp_deltas_abs = absolute_values(fmp_deltas)


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

fp_deltas_rel_abs = absolute_values(fp_deltas_rel)
fcp_deltas_rel_abs = absolute_values(fcp_deltas_rel)
fmp_deltas_rel_abs = absolute_values(fmp_deltas_rel)

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
print('|                                       Aggregate Stats                                           |')
print('| Stat            | Start Render | First Paint  | First Contentful Paint | First Meaningful Paint |')
print('|-----------------|--------------|--------------|------------------------|------------------------|')
print('| Mean            |         %d | %s |           %s |           %s |' % (
    mean_render,
    ('%d (%d)' % (mean_fp, mean_fp - mean_render)).rjust(12, ' '),
    ('%d (%d)' % (mean_fcp, mean_fcp - mean_render)).rjust(12, ' '),
    ('%d (%d)' % (mean_fmp, mean_fmp - mean_render)).rjust(12, ' '),
))
print('| Harmonic Mean   |         %d | %s |           %s |           %s |' % (
    hmean_render,
    ('%d (%d)' % (hmean_fp, hmean_fp - hmean_render)).rjust(12, ' '),
    ('%d (%d)' % (hmean_fcp, hmean_fcp - hmean_render)).rjust(12, ' '),
    ('%d (%d)' % (hmean_fmp, hmean_fmp - hmean_render)).rjust(12, ' '),
))

for pct in [10, 25, 50, 70, 80, 90, 95]:
    render_pct = percentile(renders, pct / 100)
    fp_pct = percentile(fps, pct / 100)
    fcp_pct = percentile(fcps, pct / 100)
    fmp_pct = percentile(fmps, pct / 100)

    print('| %sth percentile |         %d | %s |           %s |           %s |' % (
        str(pct),
        render_pct,
        ('%d (%d)' % (fp_pct, fp_pct - render_pct)).rjust(12, ' '),
        ('%d (%d)' % (fcp_pct, fcp_pct - render_pct)).rjust(12, ' '),
        ('%d (%d)' % (fmp_pct, fmp_pct - render_pct)).rjust(12, ' '),
    ))
print('')
