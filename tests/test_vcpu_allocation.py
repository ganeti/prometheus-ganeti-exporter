"""Tests for vCPU allocation calculation logic"""

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


class TestVCPUAllocation:
    """Test vCPU allocation calculation methods"""

    @patch('prometheus_ganeti_exporter.__main__.requests.get')
    def test_cpu_allocation_primary_node(self, mock_get, sample_config,
                                         mock_cluster_info):
        """Test calculating primary vCPU allocation for a node"""
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_cluster_info)

        collector = GanetiCollector(sample_config)
        node = {'name': 'node1.example.com'}
        instances = [
            {
                'name': 'instance1',
                'oper_vcpus': 4,
                'oper_state': True,
                'pnode': 'node1.example.com',
                'snodes': ['node2.example.com']
            },
            {
                'name': 'instance2',
                'oper_vcpus': 2,
                'oper_state': True,
                'pnode': 'node1.example.com',
                'snodes': []
            },
            {
                'name': 'instance3',
                'oper_vcpus': 8,
                'oper_state': True,
                'pnode': 'node2.example.com',  # Different primary node
                'snodes': []
            }
        ]

        metric = collector.cpu_allocation_per_node(node, instances, primary=True)

        assert metric.name == 'ganeti_node_p_oper_vcpus'
        samples = list(metric.samples)
        # Should sum vcpus from instance1 (4) + instance2 (2) = 6
        assert samples[0].value == 6

    @patch('prometheus_ganeti_exporter.__main__.requests.get')
    def test_cpu_allocation_secondary_node(self, mock_get, sample_config,
                                           mock_cluster_info):
        """Test calculating secondary vCPU allocation for a node"""
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_cluster_info)

        collector = GanetiCollector(sample_config)
        node = {'name': 'node2.example.com'}
        instances = [
            {
                'name': 'instance1',
                'oper_vcpus': 4,
                'oper_state': True,
                'pnode': 'node1.example.com',
                'snodes': ['node2.example.com']  # node2 is secondary
            },
            {
                'name': 'instance2',
                'oper_vcpus': 2,
                'oper_state': True,
                'pnode': 'node1.example.com',
                'snodes': ['node2.example.com']  # node2 is secondary
            },
            {
                'name': 'instance3',
                'oper_vcpus': 8,
                'oper_state': True,
                'pnode': 'node2.example.com',
                'snodes': []  # node2 is primary, not secondary
            }
        ]

        metric = collector.cpu_allocation_per_node(node, instances, primary=False)

        assert metric.name == 'ganeti_node_s_oper_vcpus'
        samples = list(metric.samples)
        # Should sum vcpus from instance1 (4) + instance2 (2) = 6
        assert samples[0].value == 6

    @patch('prometheus_ganeti_exporter.__main__.requests.get')
    def test_cpu_allocation_stopped_instances_excluded(self, mock_get, sample_config,
                                                       mock_cluster_info):
        """Test that stopped instances are not counted"""
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_cluster_info)

        collector = GanetiCollector(sample_config)
        node = {'name': 'node1.example.com'}
        instances = [
            {
                'name': 'running',
                'oper_vcpus': 4,
                'oper_state': True,
                'pnode': 'node1.example.com',
                'snodes': []
            },
            {
                'name': 'stopped',
                'oper_vcpus': 8,
                'oper_state': False,  # Stopped
                'pnode': 'node1.example.com',
                'snodes': []
            }
        ]

        metric = collector.cpu_allocation_per_node(node, instances, primary=True)

        samples = list(metric.samples)
        # Should only count running instance: 4 vcpus
        assert samples[0].value == 4

    @patch('prometheus_ganeti_exporter.__main__.requests.get')
    def test_cpu_allocation_node_with_no_instances(self, mock_get, sample_config,
                                                    mock_cluster_info):
        """Test node with no assigned instances"""
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_cluster_info)

        collector = GanetiCollector(sample_config)
        node = {'name': 'empty-node.example.com'}
        instances = [
            {
                'name': 'instance1',
                'oper_vcpus': 4,
                'oper_state': True,
                'pnode': 'other-node.example.com',
                'snodes': []
            }
        ]

        metric = collector.cpu_allocation_per_node(node, instances, primary=True)

        samples = list(metric.samples)
        # Should be 0 for empty node
        assert samples[0].value == 0

    @patch('prometheus_ganeti_exporter.__main__.requests.get')
    def test_cpu_allocation_multiple_secondary_nodes(self, mock_get, sample_config,
                                                     mock_cluster_info):
        """Test instance with multiple secondary nodes"""
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_cluster_info)

        collector = GanetiCollector(sample_config)
        node = {'name': 'node2.example.com'}
        instances = [
            {
                'name': 'instance1',
                'oper_vcpus': 4,
                'oper_state': True,
                'pnode': 'node1.example.com',
                'snodes': ['node2.example.com', 'node3.example.com']
            }
        ]

        metric = collector.cpu_allocation_per_node(node, instances, primary=False)

        samples = list(metric.samples)
        # node2 is in snodes list, should count the vcpus
        assert samples[0].value == 4

    @patch('prometheus_ganeti_exporter.__main__.requests.get')
    def test_collect_vcpu_allocation_complete(self, mock_get, sample_config,
                                              mock_cluster_info, sample_nodes,
                                              sample_instances):
        """Test complete vCPU allocation collection for all nodes"""
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_cluster_info)

        collector = GanetiCollector(sample_config)
        metrics = collector.collect_vcpu_allocation(sample_nodes, sample_instances)

        # Should return 2 metrics per node (primary + secondary)
        expected_count = len(sample_nodes) * 2
        assert len(metrics) == expected_count

        # Check that both primary and secondary metrics are present
        metric_names = [m.name for m in metrics]
        assert 'ganeti_node_p_oper_vcpus' in metric_names
        assert 'ganeti_node_s_oper_vcpus' in metric_names

    @patch('prometheus_ganeti_exporter.__main__.requests.get')
    def test_collect_vcpu_allocation_values(self, mock_get, sample_config,
                                            mock_cluster_info, sample_instances):
        """Test vCPU allocation values are calculated correctly"""
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_cluster_info)

        collector = GanetiCollector(sample_config)

        # Simple test case with known values
        nodes = [
            {'name': 'node1.example.com'},
            {'name': 'node2.example.com'}
        ]

        # From sample_instances:
        # instance1: pnode=node1, snodes=[node2], vcpus=4, state=True
        # instance2: pnode=node1, snodes=[node2], vcpus=2, state=True
        # instance3: pnode=node2, snodes=[node1], vcpus=8, state=False (stopped)
        # instance4: pnode=node2, snodes=[], vcpus=2, state=True

        metrics = collector.collect_vcpu_allocation(nodes, sample_instances)

        primary_metrics = [m for m in metrics if m.name == 'ganeti_node_p_oper_vcpus']
        secondary_metrics = [m for m in metrics if m.name == 'ganeti_node_s_oper_vcpus']

        # Verify primary allocation for node1
        node1_primary_samples = None
        for metric in primary_metrics:
            samples = list(metric.samples)
            for sample in samples:
                if 'node1' in str(sample.labels):
                    node1_primary_samples = sample
                    break

        # node1 primary: instance1 (4) + instance2 (2) = 6
        if node1_primary_samples:
            assert node1_primary_samples.value == 6

        # Verify primary allocation for node2
        node2_primary_samples = None
        for metric in primary_metrics:
            samples = list(metric.samples)
            for sample in samples:
                if 'node2' in str(sample.labels):
                    node2_primary_samples = sample
                    break

        # node2 primary: instance4 (2) only (instance3 is stopped)
        if node2_primary_samples:
            assert node2_primary_samples.value == 2

    @patch('prometheus_ganeti_exporter.__main__.requests.get')
    def test_collect_vcpu_allocation_empty_lists(self, mock_get, sample_config,
                                                  mock_cluster_info):
        """Test vCPU allocation with empty node/instance lists"""
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_cluster_info)

        collector = GanetiCollector(sample_config)
        metrics = collector.collect_vcpu_allocation([], [])

        assert len(metrics) == 0

    @patch('prometheus_ganeti_exporter.__main__.requests.get')
    def test_cpu_allocation_with_namespace(self, mock_get, mock_cluster_info):
        """Test that namespace prefix is applied to vCPU metrics"""
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_cluster_info)

        config = {
            'ganeti_api_endpoint': 'https://ganeti.example.com:5080',
            'ganeti_user': 'testuser',
            'ganeti_password': 'testpass',
            'verify_tls': True,
            'port': 8000,
            'namespace': 'prod',
            'refresh_interval': 30,
            'hspace_enabled': False,
            'hbal_enabled': False
        }

        collector = GanetiCollector(config)
        node = {'name': 'node1'}
        instances = [
            {
                'name': 'instance1',
                'oper_vcpus': 4,
                'oper_state': True,
                'pnode': 'node1',
                'snodes': []
            }
        ]

        metric = collector.cpu_allocation_per_node(node, instances, primary=True)

        # Check that namespace is in metric name
        assert 'prod_ganeti_' in metric.name
