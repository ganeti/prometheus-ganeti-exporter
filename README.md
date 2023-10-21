# prometheus-ganeti-exporter

Welcome to the home of `prometheus-ganeti-exporter. You can use this software to publish [Ganeti](https://www.ganeti.org/) cluster statistics to [Prometheus](https://prometheus.io/). It has been initially developed by Wikimedia Foundation and is now part of the Ganeti project.

## Usage

You can use the provided [systemd service file](./prometheus-ganeti-exporter.service) to run the service in the background. Please create or use a non-privileged system user for the service to avoid running it as `root`! The RAPI user requires read-only permissions for the exporter to work.

## Configuration

The service expects its configuration file in `/etc/ganeti/prometheus.ini` (an alternative path can provided through the ``--config`` parameter). Please see [prometheus.ini.example](./prometheus.ini.example) for an example configuration. Please make sure the file is only readable to the service user as it contains RAPI credentials.

## Grafana

If you use [Prometheus](https://prometheus.io/) with [Grafana](https://grafana.com/) you may want to take a look at the included [sample dashboard](./example-grafana-dashboard.json).