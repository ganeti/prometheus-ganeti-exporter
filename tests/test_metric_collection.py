"""Tests for Prometheus metric collection from Ganeti data"""

#
# Copyright (c) 2026, Ganeti Project
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
# IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from unittest.mock import patch, Mock
import pytest
from prometheus_ganeti_exporter.__main__ import GanetiCollector


class TestNodeMetricCollection:
    """Test collect_node_metrics method"""

    @patch('prometheus_ganeti_exporter.__main__.requests.get')
    def test_collect_node_metrics_single_node(self, mock_get, sample_config,
                                               mock_cluster_info):
        """Test collecting metrics from a single node"""
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_cluster_info)

        collector = GanetiCollector(sample_config)
        nodes = [
            {
                'name': 'node1.example.com',
                'ctotal': 32,
                'dfree': 500000,
                'dtotal': 1000000,
                'mfree': 32768,
                'mtotal': 65536
            }
        ]

        metrics = collector.collect_node_metrics(nodes)

        assert len(metrics) == 5  # ctotal, dfree, dtotal, mfree, mtotal
        metric_names = {m.name for m in metrics}
        assert 'ganeti_node_ctotal' in metric_names
        assert 'ganeti_node_dfree' in metric_names
        assert 'ganeti_node_dtotal' in metric_names
        assert 'ganeti_node_mfree' in metric_names
        assert 'ganeti_node_mtotal' in metric_names

    @patch('prometheus_ganeti_exporter.__main__.requests.get')
    def test_collect_node_metrics_multiple_nodes(self, mock_get, sample_config,
                                                  mock_cluster_info, sample_nodes):
        """Test collecting metrics from multiple nodes"""
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_cluster_info)

        collector = GanetiCollector(sample_config)
        metrics = collector.collect_node_metrics(sample_nodes)

        # Should create one metric family per metric type
        assert len(metrics) > 0

        # Check that metrics contain data from all nodes
        for metric in metrics:
            if metric.name == 'ganeti_node_ctotal':
                # Should have 3 samples (one per node)
                samples = list(metric.samples)
                assert len(samples) == 3

    @patch('prometheus_ganeti_exporter.__main__.requests.get')
    def test_collect_node_metrics_empty_list(self, mock_get, sample_config,
                                              mock_cluster_info):
        """Test collecting metrics from empty node list"""
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_cluster_info)

        collector = GanetiCollector(sample_config)
        metrics = collector.collect_node_metrics([])

        assert len(metrics) == 0

    @patch('prometheus_ganeti_exporter.__main__.requests.get')
    def test_collect_node_metrics_with_namespace(self, mock_get, mock_cluster_info):
        """Test that namespace prefix is applied to metrics"""
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_cluster_info)

        config = {
            'ganeti_api_endpoint': 'https://ganeti.example.com:5080',
            'ganeti_user': 'testuser',
            'ganeti_password': 'testpass',
            'verify_tls': True,
            'port': 8000,
            'namespace': 'myorg',
            'refresh_interval': 30,
            'hspace_enabled': False,
            'hbal_enabled': False
        }

        collector = GanetiCollector(config)
        nodes = [{'name': 'node1', 'ctotal': 16}]
        metrics = collector.collect_node_metrics(nodes)

        # Check that namespace is applied
        metric_names = {m.name for m in metrics}
        assert any('myorg_ganeti_' in name for name in metric_names)


class TestInstanceMetricCollection:
    """Test collect_instance_metrics method"""

    @patch('prometheus_ganeti_exporter.__main__.requests.get')
    def test_collect_instance_metrics_running(self, mock_get, sample_config,
                                               mock_cluster_info):
        """Test collecting metrics from running instances"""
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_cluster_info)

        collector = GanetiCollector(sample_config)
        instances = [
            {
                'name': 'instance1.example.com',
                'oper_vcpus': 4,
                'oper_ram': 8192,
                'oper_state': True
            }
        ]

        metrics = collector.collect_instance_metrics(instances)

        assert len(metrics) == 2  # oper_vcpus, oper_ram
        metric_names = {m.name for m in metrics}
        assert 'ganeti_instance_oper_vcpus' in metric_names
        assert 'ganeti_instance_oper_ram' in metric_names

    @patch('prometheus_ganeti_exporter.__main__.requests.get')
    def test_collect_instance_metrics_stopped(self, mock_get, sample_config,
                                               mock_cluster_info):
        """Test that stopped instances report 0 for metrics"""
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_cluster_info)

        collector = GanetiCollector(sample_config)
        instances = [
            {
                'name': 'stopped-instance',
                'oper_vcpus': 8,
                'oper_ram': 16384,
                'oper_state': False  # Stopped
            }
        ]

        metrics = collector.collect_instance_metrics(instances)

        # Stopped instances should report 0 for resource metrics
        for metric in metrics:
            for sample in metric.samples:
                assert sample.value == 0

    @patch('prometheus_ganeti_exporter.__main__.requests.get')
    def test_collect_instance_metrics_mixed_states(self, mock_get, sample_config,
                                                    mock_cluster_info, sample_instances):
        """Test collecting metrics from instances with mixed states"""
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_cluster_info)

        collector = GanetiCollector(sample_config)
        metrics = collector.collect_instance_metrics(sample_instances)

        assert len(metrics) == 2

        # Verify that stopped instances have 0 values
        for metric in metrics:
            if metric.name == 'ganeti_instance_oper_vcpus':
                samples = list(metric.samples)
                # instance3 is stopped, should have 0 vcpus reported
                stopped_sample = [s for s in samples if 'instance3' in str(s.labels)]
                if stopped_sample:
                    assert stopped_sample[0].value == 0

    @patch('prometheus_ganeti_exporter.__main__.requests.get')
    def test_collect_instance_metrics_empty_list(self, mock_get, sample_config,
                                                  mock_cluster_info):
        """Test collecting metrics from empty instance list"""
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_cluster_info)

        collector = GanetiCollector(sample_config)
        metrics = collector.collect_instance_metrics([])

        assert len(metrics) == 0


class TestSummaryMetricCollection:
    """Test collect_summaries method"""

    @patch('prometheus_ganeti_exporter.__main__.requests.get')
    def test_collect_summaries_basic(self, mock_get, sample_config, mock_cluster_info,
                                      sample_nodes, sample_instances, sample_jobs):
        """Test collecting summary metrics"""
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_cluster_info)

        collector = GanetiCollector(sample_config)
        metrics = collector.collect_summaries(sample_nodes, sample_instances, sample_jobs)

        assert len(metrics) == 4  # instance_count, node_count, offline_nodes, jobs
        metric_names = {m.name for m in metrics}
        assert 'ganeti_cluster_instance_count' in metric_names
        assert 'ganeti_cluster_node_count' in metric_names
        assert 'ganeti_cluster_offline_nodes' in metric_names
        assert 'ganeti_cluster_jobs' in metric_names

    @patch('prometheus_ganeti_exporter.__main__.requests.get')
    def test_collect_summaries_counts(self, mock_get, sample_config, mock_cluster_info,
                                       sample_nodes, sample_instances, sample_jobs):
        """Test that summary counts are correct"""
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_cluster_info)

        collector = GanetiCollector(sample_config)
        metrics = collector.collect_summaries(sample_nodes, sample_instances, sample_jobs)

        for metric in metrics:
            if metric.name == 'ganeti_cluster_instance_count':
                samples = list(metric.samples)
                assert samples[0].value == len(sample_instances)

            if metric.name == 'ganeti_cluster_node_count':
                samples = list(metric.samples)
                assert samples[0].value == len(sample_nodes)

            if metric.name == 'ganeti_cluster_offline_nodes':
                samples = list(metric.samples)
                # sample_nodes has 1 offline node (node3)
                assert samples[0].value == 1

    @patch('prometheus_ganeti_exporter.__main__.requests.get')
    def test_collect_summaries_job_states(self, mock_get, sample_config,
                                          mock_cluster_info, sample_jobs):
        """Test that job states are counted correctly"""
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_cluster_info)

        collector = GanetiCollector(sample_config)
        metrics = collector.collect_summaries([], [], sample_jobs)

        job_metric = None
        for metric in metrics:
            if metric.name == 'ganeti_cluster_jobs':
                job_metric = metric
                break

        assert job_metric is not None

        # Check that all job states are present
        samples = list(job_metric.samples)
        job_states = {s.labels['job_status']: s.value for s in samples}

        # From sample_jobs: 1 success, 1 running, 1 queued, 1 error
        assert job_states.get('success', 0) == 1
        assert job_states.get('running', 0) == 1
        assert job_states.get('queued', 0) == 1
        assert job_states.get('error', 0) == 1
        # These should be 0
        assert job_states.get('waiting', 0) == 0
        assert job_states.get('canceled', 0) == 0
        assert job_states.get('canceling', 0) == 0

    @patch('prometheus_ganeti_exporter.__main__.requests.get')
    def test_collect_summaries_empty_inputs(self, mock_get, sample_config,
                                            mock_cluster_info):
        """Test summary collection with empty inputs"""
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_cluster_info)

        collector = GanetiCollector(sample_config)
        metrics = collector.collect_summaries([], [], [])

        for metric in metrics:
            if metric.name in ['ganeti_cluster_instance_count',
                              'ganeti_cluster_node_count',
                              'ganeti_cluster_offline_nodes']:
                samples = list(metric.samples)
                assert samples[0].value == 0


class TestJobMetricCollection:
    """Test collect_job_metrics method"""

    @patch('prometheus_ganeti_exporter.__main__.requests.get')
    def test_collect_job_metrics_with_timestamps(self, mock_get, sample_config,
                                                  mock_cluster_info):
        """Test collecting job metrics with complete timestamps"""
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_cluster_info)

        collector = GanetiCollector(sample_config)
        jobs = [
            {
                'id': 1,
                'status': 'success',
                'ops': [{'OP_ID': 'OP_INSTANCE_CREATE'}],
                'received_ts': [1640000000, 0],
                'start_ts': [1640000010, 0],
                'end_ts': [1640000100, 0]
            }
        ]

        metrics = collector.collect_job_metrics(jobs)

        assert len(metrics) == 2  # wait_time, run_time
        metric_names = {m.name for m in metrics}
        assert 'ganeti_job_wait_time' in metric_names
        assert 'ganeti_job_run_time' in metric_names

        # Check calculated times
        for metric in metrics:
            samples = list(metric.samples)
            if metric.name == 'ganeti_job_wait_time':
                # Wait time: start - received = 1640000010 - 1640000000 = 10
                assert samples[0].value == 10
            if metric.name == 'ganeti_job_run_time':
                # Run time: end - start = 1640000100 - 1640000010 = 90
                assert samples[0].value == 90

    @patch('prometheus_ganeti_exporter.__main__.requests.get')
    def test_collect_job_metrics_missing_timestamps(self, mock_get, sample_config,
                                                     mock_cluster_info):
        """Test that jobs with missing timestamps are skipped"""
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_cluster_info)

        collector = GanetiCollector(sample_config)
        jobs = [
            {
                'id': 2,
                'status': 'queued',
                'ops': [{'OP_ID': 'OP_INSTANCE_MIGRATE'}],
                'received_ts': [1640000200, 0],
                'start_ts': None,  # Not started yet
                'end_ts': None
            }
        ]

        metrics = collector.collect_job_metrics(jobs)

        # Metrics are created but should have no samples for this job
        for metric in metrics:
            samples = list(metric.samples)
            assert len(samples) == 0

    @patch('prometheus_ganeti_exporter.__main__.requests.get')
    def test_collect_job_metrics_missing_ops(self, mock_get, sample_config,
                                              mock_cluster_info):
        """Test that jobs without ops are handled gracefully"""
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_cluster_info)

        collector = GanetiCollector(sample_config)
        jobs = [
            {
                'id': 3,
                'status': 'error',
                'ops': None,  # No ops
                'received_ts': [1640000300, 0],
                'start_ts': [1640000305, 0],
                'end_ts': [1640000310, 0]
            }
        ]

        metrics = collector.collect_job_metrics(jobs)

        # Should still calculate times, but op_id should be "unknown"
        for metric in metrics:
            samples = list(metric.samples)
            if len(samples) > 0:
                assert samples[0].labels['job_operation'] == 'unknown'

    @patch('prometheus_ganeti_exporter.__main__.requests.get')
    def test_collect_job_metrics_empty_list(self, mock_get, sample_config,
                                            mock_cluster_info):
        """Test collecting job metrics from empty list"""
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_cluster_info)

        collector = GanetiCollector(sample_config)
        metrics = collector.collect_job_metrics([])

        # Metrics are created but have no samples
        assert len(metrics) == 2
        for metric in metrics:
            samples = list(metric.samples)
            assert len(samples) == 0
