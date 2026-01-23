"""Shared pytest fixtures and utilities for prometheus-ganeti-exporter tests"""

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

import tempfile
from unittest.mock import Mock, MagicMock
import pytest


@pytest.fixture
def mock_response():
    """Create a mock requests.Response object"""
    def _mock_response(status_code=200, json_data=None):
        mock_resp = Mock()
        mock_resp.status_code = status_code
        mock_resp.json.return_value = json_data if json_data else {}
        return mock_resp
    return _mock_response


@pytest.fixture
def mock_cluster_info():
    """Mock Ganeti cluster info response"""
    return {
        'name': 'test-cluster',
        'version': '3.0.0',
        'architecture': 'x86_64'
    }


@pytest.fixture
def sample_config():
    """Sample valid configuration dictionary"""
    return {
        'ganeti_api_endpoint': 'https://ganeti.example.com:5080',
        'ganeti_user': 'testuser',
        'ganeti_password': 'testpass',
        'verify_tls': True,
        'port': 8000,
        'namespace': '',
        'refresh_interval': 30,
        'hspace_enabled': False,
        'hspace_path': '/usr/bin/hspace',
        'hspace_disk_template': 'plain',
        'hspace_alloc_data': '20480,2048,2',
        'hbal_enabled': False,
        'hbal_path': '/usr/bin/hbal',
        'hbal_extra_parameters': ''
    }


@pytest.fixture
def sample_nodes():
    """Sample node data from Ganeti API"""
    return [
        {
            'name': 'node1.example.com',
            'ctotal': 32,
            'dfree': 500000,
            'dtotal': 1000000,
            'mfree': 32768,
            'mtotal': 65536,
            'pinst_cnt': 5,
            'sinst_cnt': 3,
            'offline': False
        },
        {
            'name': 'node2.example.com',
            'ctotal': 32,
            'dfree': 400000,
            'dtotal': 1000000,
            'mfree': 16384,
            'mtotal': 65536,
            'pinst_cnt': 7,
            'sinst_cnt': 2,
            'offline': False
        },
        {
            'name': 'node3.example.com',
            'ctotal': 16,
            'dfree': 0,
            'dtotal': 500000,
            'mfree': 0,
            'mtotal': 32768,
            'pinst_cnt': 0,
            'sinst_cnt': 0,
            'offline': True
        }
    ]


@pytest.fixture
def sample_instances():
    """Sample instance data from Ganeti API"""
    return [
        {
            'name': 'instance1.example.com',
            'oper_vcpus': 4,
            'oper_ram': 8192,
            'oper_state': True,
            'pnode': 'node1.example.com',
            'snodes': ['node2.example.com']
        },
        {
            'name': 'instance2.example.com',
            'oper_vcpus': 2,
            'oper_ram': 4096,
            'oper_state': True,
            'pnode': 'node1.example.com',
            'snodes': ['node2.example.com']
        },
        {
            'name': 'instance3.example.com',
            'oper_vcpus': 8,
            'oper_ram': 16384,
            'oper_state': False,  # Stopped instance
            'pnode': 'node2.example.com',
            'snodes': ['node1.example.com']
        },
        {
            'name': 'instance4.example.com',
            'oper_vcpus': 2,
            'oper_ram': 2048,
            'oper_state': True,
            'pnode': 'node2.example.com',
            'snodes': []
        }
    ]


@pytest.fixture
def sample_jobs():
    """Sample job data from Ganeti API"""
    return [
        {
            'id': 1,
            'status': 'success',
            'ops': [{'OP_ID': 'OP_INSTANCE_CREATE'}],
            'received_ts': [1640000000, 0],
            'start_ts': [1640000010, 0],
            'end_ts': [1640000100, 0]
        },
        {
            'id': 2,
            'status': 'running',
            'ops': [{'OP_ID': 'OP_INSTANCE_MIGRATE'}],
            'received_ts': [1640000200, 0],
            'start_ts': [1640000210, 0],
            'end_ts': None
        },
        {
            'id': 3,
            'status': 'queued',
            'ops': [{'OP_ID': 'OP_INSTANCE_REMOVE'}],
            'received_ts': [1640000300, 0],
            'start_ts': None,
            'end_ts': None
        },
        {
            'id': 4,
            'status': 'error',
            'ops': None,
            'received_ts': [1640000400, 0],
            'start_ts': [1640000405, 0],
            'end_ts': [1640000410, 0]
        }
    ]


@pytest.fixture
def temp_config_file():
    """Create a temporary configuration file for testing"""
    def _create_config(content):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini',
                                         delete=False) as f:
            f.write(content)
            return f.name
    return _create_config
