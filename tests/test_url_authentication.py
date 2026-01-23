"""Tests for URL authentication injection"""

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


class TestURLAuthentication:
    """Test _add_auth_to_url method"""

    @patch('prometheus_ganeti_exporter.__main__.requests.get')
    def test_https_url_basic(self, mock_get, sample_config, mock_cluster_info):
        """Test basic HTTPS URL with authentication"""
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_cluster_info)

        collector = GanetiCollector(sample_config)
        result = collector._add_auth_to_url(
            'https://ganeti.example.com:5080',
            'testuser',
            'testpass'
        )

        assert result == 'https://testuser:testpass@ganeti.example.com:5080'

    @patch('prometheus_ganeti_exporter.__main__.requests.get')
    def test_http_url(self, mock_get, sample_config, mock_cluster_info):
        """Test HTTP URL with authentication"""
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_cluster_info)

        collector = GanetiCollector(sample_config)
        result = collector._add_auth_to_url(
            'http://ganeti.example.com',
            'user',
            'pass'
        )

        assert result == 'http://user:pass@ganeti.example.com'

    @patch('prometheus_ganeti_exporter.__main__.requests.get')
    def test_url_with_custom_port(self, mock_get, sample_config, mock_cluster_info):
        """Test URL with custom port"""
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_cluster_info)

        collector = GanetiCollector(sample_config)
        result = collector._add_auth_to_url(
            'https://ganeti.example.com:8443',
            'admin',
            'secret'
        )

        assert result == 'https://admin:secret@ganeti.example.com:8443'

    @patch('prometheus_ganeti_exporter.__main__.requests.get')
    def test_url_without_port(self, mock_get, sample_config, mock_cluster_info):
        """Test URL without explicit port"""
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_cluster_info)

        collector = GanetiCollector(sample_config)
        result = collector._add_auth_to_url(
            'https://ganeti.example.com',
            'testuser',
            'testpass'
        )

        assert result == 'https://testuser:testpass@ganeti.example.com'

    @patch('prometheus_ganeti_exporter.__main__.requests.get')
    def test_special_characters_in_username(self, mock_get, sample_config, mock_cluster_info):
        """Test username with special characters"""
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_cluster_info)

        collector = GanetiCollector(sample_config)
        result = collector._add_auth_to_url(
            'https://ganeti.example.com:5080',
            'test.user@domain',
            'password'
        )

        assert result == 'https://test.user@domain:password@ganeti.example.com:5080'

    @patch('prometheus_ganeti_exporter.__main__.requests.get')
    def test_special_characters_in_password(self, mock_get, sample_config, mock_cluster_info):
        """Test password with special characters"""
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_cluster_info)

        collector = GanetiCollector(sample_config)
        result = collector._add_auth_to_url(
            'https://ganeti.example.com:5080',
            'testuser',
            'p@$$w0rd!'
        )

        assert result == 'https://testuser:p@$$w0rd!@ganeti.example.com:5080'

    @patch('prometheus_ganeti_exporter.__main__.requests.get')
    def test_empty_password(self, mock_get, sample_config, mock_cluster_info):
        """Test empty password"""
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_cluster_info)

        collector = GanetiCollector(sample_config)
        result = collector._add_auth_to_url(
            'https://ganeti.example.com:5080',
            'testuser',
            ''
        )

        assert result == 'https://testuser:@ganeti.example.com:5080'

    @patch('prometheus_ganeti_exporter.__main__.requests.get')
    def test_url_with_path(self, mock_get, sample_config, mock_cluster_info):
        """Test URL with path component (path should be preserved in netloc)"""
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_cluster_info)

        collector = GanetiCollector(sample_config)
        # Note: urllib3.util.parse_url treats path as part of the URL structure,
        # but for the netloc it only includes scheme://hostname:port
        result = collector._add_auth_to_url(
            'https://ganeti.example.com:5080/api',
            'user',
            'pass'
        )

        # The function uses url_parts.netloc which doesn't include path
        assert result == 'https://user:pass@ganeti.example.com:5080'

    @patch('prometheus_ganeti_exporter.__main__.requests.get')
    def test_ipv4_address(self, mock_get, sample_config, mock_cluster_info):
        """Test with IPv4 address"""
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_cluster_info)

        collector = GanetiCollector(sample_config)
        result = collector._add_auth_to_url(
            'https://192.168.1.100:5080',
            'admin',
            'secret'
        )

        assert result == 'https://admin:secret@192.168.1.100:5080'

    @patch('prometheus_ganeti_exporter.__main__.requests.get')
    def test_localhost(self, mock_get, sample_config, mock_cluster_info):
        """Test with localhost"""
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_cluster_info)

        collector = GanetiCollector(sample_config)
        result = collector._add_auth_to_url(
            'http://localhost:5080',
            'local',
            'pass'
        )

        assert result == 'http://local:pass@localhost:5080'
