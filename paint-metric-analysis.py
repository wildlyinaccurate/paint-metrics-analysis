import json
import plotly.offline as py
import plotly.graph_objs as go
from statistics import mean, harmonic_mean

f = open('paint-metrics.json', 'r')
data = json.load(f)
f.close()


def values_without_outliers(key, outlier_threshold=6500):
    return [item for url in data['urls'] for item in url[key] if item < outlier_threshold]


def avg_by_url_without_outliers(key, outlier_threshold=6500):
    return list(map(mean, [[val for val in url[key] if val < outlier_threshold] for url in data['urls']]))


def histogram_trace(data, label, bin_size):
    return go.Histogram(name=label, x=data, xbins=dict(size=bin_size, start=min(data), end=max(data)), opacity=0.75)


def generate_histogram(outfile, bin_size, data, labels):
    data = [histogram_trace(series, label, bin_size)
            for series, label in zip(data, labels)]
    layout = go.Layout(barmode='overlay')
    fig = go.Figure(data=data, layout=layout)
    py.plot(fig, filename=outfile, auto_open=False)


print('Generating HTML charts... ', end='', flush=True)
renders = values_without_outliers('render')
fps = values_without_outliers('fp')
fcps = values_without_outliers('fcp')
fmps = values_without_outliers('fmp')

generate_histogram('metric-distribution.html', 100, [renders, fps, fcps], [
    'Start Render', 'First Paint', 'First Contentful Paint'])

render_avgs = avg_by_url_without_outliers('render')
fp_avgs = avg_by_url_without_outliers('fp')
fcp_avgs = avg_by_url_without_outliers('fcp')

generate_histogram('metric-distribution-by-url.html', 50,
                   [render_avgs, fp_avgs, fcp_avgs], ['Start Render', 'First Paint', 'First Contentful Paint'])

fp_deltas = [fp - render for fp, render in zip(fps, renders)]
fcp_deltas = [fcp - render for fcp, render in zip(fcps, renders)]

generate_histogram('metric-deltas.html', 50, [fp_deltas, fcp_deltas], [
    'First Paint Delta', 'First Contentful Paint Delta'])
print('Done.')

mean_render = mean(renders)
mean_fp = mean(fps)
mean_fcp = mean(fcps)
mean_fmp = mean(fmps)

hmean_render = harmonic_mean(renders)
hmean_fp = harmonic_mean(fps)
hmean_fcp = harmonic_mean(fcps)
hmean_fmp = harmonic_mean(fmps)

print('Generating aggregate stats...\n')

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
