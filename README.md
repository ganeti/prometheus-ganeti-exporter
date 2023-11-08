# prometheus-ganeti-exporter

Welcome to the home of `prometheus-ganeti-exporter. You can use this software to publish [Ganeti](https://www.ganeti.org/) cluster statistics to [Prometheus](https://prometheus.io/). It has been initially developed by Wikimedia Foundation and is now part of the Ganeti project.

## Usage

You can use the provided [systemd service file](./prometheus-ganeti-exporter.service) to run the service in the background. Please create or use a non-privileged system user for the service to avoid running it as `root`! The RAPI user requires read-only permissions for the exporter to work.

## Configuration

The service expects its configuration file in `/etc/ganeti/prometheus.ini` (an alternative path can provided through the ``--config`` parameter). Please see [prometheus.ini.example](./prometheus.ini.example) for an example configuration. Please make sure the file is only readable to the service user as it contains RAPI credentials.

## Integration of htools

You can configure the exporter to include data from Ganeti htools (currently `hbal` and `hspace`). The default setting is to not query these tools, as they need to be available on the machine the exporter is running, and they also might take a long time (especially `hspace` tends block for a while when running on unbalanced clusters). The exporter will kill these processes when they reach the configured refresh interval and log this as an error.

Please beware that htools will connect to the cluster using RAPI. Unfortunately this will **reveal your RAPI credentials in the process list** as they need to passed on the command line. If you plan to run the exporter from a node which is not itself a Ganeti node, you can either build htools from the [Ganeti source](https://github.com/ganeti/ganeti) or install the package `ganeti-htools` if you are on Debian. The latter will *only* install htools without Ganeti itself.

### hbal

Metrics obtained from `hbal` include the current cluster score as well as the achievable cluster score. This allows you to monitor for clusters which are in need of rebalancing. You may specify additional parameters to `hbal` as e.g. `--exclusion-tags` using the exporter configuration file.

### hspace

`hspace` simulates the creation of instances with a given disk template and a given size (specified as `$storage,$memory,$vcpus`). Currently, the only metric exported is the number of instances that could be allocated with the given parameters.

## Logging

You may set the logging level using the argument `--loglevel [error|warning|info|debug]`. Please note that debug logging **might** leak sensitive data like your RAPI credentials. Use this setting with caution! The default loglevel is set to `warning`.

## Grafana

If you use [Prometheus](https://prometheus.io/) with [Grafana](https://grafana.com/) you may want to take a look at the [example overview dashboard](./example-grafana-dashboard-overview.json) or the [example details dashboard](./example-grafana-dashboard-details.json). All dashboards in this repository are released under the [BSD 2-Clause License](./LICENSE).