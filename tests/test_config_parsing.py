"""Tests for configuration file parsing"""

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

import os
import tempfile
import pytest
from prometheus_ganeti_exporter.__main__ import parse_config


class TestParseConfig:
    """Test configuration parsing functionality"""

    def test_valid_minimal_config(self, temp_config_file):
        """Test parsing a minimal valid configuration"""
        config_content = """
[ganeti]
api = https://ganeti.example.com:5080
user = testuser
password = testpass
"""
        config_path = temp_config_file(config_content)
        try:
            config = parse_config(config_path)
            assert config['ganeti_api_endpoint'] == 'https://ganeti.example.com:5080'
            assert config['ganeti_user'] == 'testuser'
            assert config['ganeti_password'] == 'testpass'
            # Check defaults
            assert config['verify_tls'] is True
            assert config['port'] == 8000
            assert config['namespace'] == ''
            assert config['refresh_interval'] == 30
        finally:
            os.unlink(config_path)

    def test_valid_complete_config(self, temp_config_file):
        """Test parsing a complete configuration with all options"""
        config_content = """
[default]
port = 9000
verify_tls = False
refresh_interval = 60
namespace = myorg

[ganeti]
api = https://ganeti.example.com:5080
user = readonly
password = secret123

[htools]
hspace_enabled = True
hspace_path = /opt/bin/hspace
hspace_disk_template = drbd
hspace_alloc_data = 40960,4096,4
hbal_enabled = True
hbal_path = /opt/bin/hbal
hbal_extra_parameters = --no-instance-moves
"""
        config_path = temp_config_file(config_content)
        try:
            config = parse_config(config_path)
            # Default section
            assert config['port'] == 9000
            assert config['verify_tls'] is False
            assert config['refresh_interval'] == 60
            assert config['namespace'] == 'myorg'
            # Ganeti section
            assert config['ganeti_api_endpoint'] == 'https://ganeti.example.com:5080'
            assert config['ganeti_user'] == 'readonly'
            assert config['ganeti_password'] == 'secret123'
            # Htools section
            assert config['hspace_enabled'] is True
            assert config['hspace_path'] == '/opt/bin/hspace'
            assert config['hspace_disk_template'] == 'drbd'
            assert config['hspace_alloc_data'] == '40960,4096,4'
            assert config['hbal_enabled'] is True
            assert config['hbal_path'] == '/opt/bin/hbal'
            assert config['hbal_extra_parameters'] == '--no-instance-moves'
        finally:
            os.unlink(config_path)

    def test_missing_config_file(self):
        """Test handling of non-existent configuration file"""
        with pytest.raises(SystemExit) as exc_info:
            parse_config('/nonexistent/path/to/config.ini')
        assert exc_info.value.code == 1

    def test_missing_ganeti_section(self, temp_config_file):
        """Test handling of missing [ganeti] section"""
        config_content = """
[default]
port = 8000
"""
        config_path = temp_config_file(config_content)
        try:
            with pytest.raises(SystemExit) as exc_info:
                parse_config(config_path)
            assert exc_info.value.code == 1
        finally:
            os.unlink(config_path)

    def test_missing_required_api_field(self, temp_config_file):
        """Test handling of missing required 'api' field"""
        config_content = """
[ganeti]
user = testuser
password = testpass
"""
        config_path = temp_config_file(config_content)
        try:
            with pytest.raises(SystemExit) as exc_info:
                parse_config(config_path)
            assert exc_info.value.code == 1
        finally:
            os.unlink(config_path)

    def test_missing_required_user_field(self, temp_config_file):
        """Test handling of missing required 'user' field"""
        config_content = """
[ganeti]
api = https://ganeti.example.com:5080
password = testpass
"""
        config_path = temp_config_file(config_content)
        try:
            with pytest.raises(SystemExit) as exc_info:
                parse_config(config_path)
            assert exc_info.value.code == 1
        finally:
            os.unlink(config_path)

    def test_missing_required_password_field(self, temp_config_file):
        """Test handling of missing required 'password' field"""
        config_content = """
[ganeti]
api = https://ganeti.example.com:5080
user = testuser
"""
        config_path = temp_config_file(config_content)
        try:
            with pytest.raises(SystemExit) as exc_info:
                parse_config(config_path)
            assert exc_info.value.code == 1
        finally:
            os.unlink(config_path)

    def test_boolean_parsing_true_lowercase(self, temp_config_file):
        """Test parsing boolean value 'true'"""
        config_content = """
[default]
verify_tls = true

[ganeti]
api = https://ganeti.example.com:5080
user = testuser
password = testpass
"""
        config_path = temp_config_file(config_content)
        try:
            config = parse_config(config_path)
            assert config['verify_tls'] is True
        finally:
            os.unlink(config_path)

    def test_boolean_parsing_false_lowercase(self, temp_config_file):
        """Test parsing boolean value 'false'"""
        config_content = """
[default]
verify_tls = false

[ganeti]
api = https://ganeti.example.com:5080
user = testuser
password = testpass
"""
        config_path = temp_config_file(config_content)
        try:
            config = parse_config(config_path)
            assert config['verify_tls'] is False
        finally:
            os.unlink(config_path)

    def test_integer_parsing(self, temp_config_file):
        """Test parsing integer values"""
        config_content = """
[default]
port = 9100
refresh_interval = 120

[ganeti]
api = https://ganeti.example.com:5080
user = testuser
password = testpass
"""
        config_path = temp_config_file(config_content)
        try:
            config = parse_config(config_path)
            assert config['port'] == 9100
            assert isinstance(config['port'], int)
            assert config['refresh_interval'] == 120
            assert isinstance(config['refresh_interval'], int)
        finally:
            os.unlink(config_path)

    def test_empty_namespace(self, temp_config_file):
        """Test that empty namespace defaults to empty string"""
        config_content = """
[default]
namespace =

[ganeti]
api = https://ganeti.example.com:5080
user = testuser
password = testpass
"""
        config_path = temp_config_file(config_content)
        try:
            config = parse_config(config_path)
            assert config['namespace'] == ''
        finally:
            os.unlink(config_path)

    def test_htools_defaults(self, temp_config_file):
        """Test that htools options have correct defaults"""
        config_content = """
[ganeti]
api = https://ganeti.example.com:5080
user = testuser
password = testpass
"""
        config_path = temp_config_file(config_content)
        try:
            config = parse_config(config_path)
            assert config['hspace_enabled'] is False
            assert config['hspace_path'] == '/usr/bin/hspace'
            assert config['hspace_disk_template'] == 'plain'
            assert config['hspace_alloc_data'] == '20480,2048,2'
            assert config['hbal_enabled'] is False
            assert config['hbal_path'] == '/usr/bin/hbal'
            assert config['hbal_extra_parameters'] == ''
        finally:
            os.unlink(config_path)

    def test_special_characters_in_password(self, temp_config_file):
        """Test that special characters in password are preserved"""
        config_content = """
[ganeti]
api = https://ganeti.example.com:5080
user = testuser
password = p@$$w0rd!#&*()
"""
        config_path = temp_config_file(config_content)
        try:
            config = parse_config(config_path)
            assert config['ganeti_password'] == 'p@$$w0rd!#&*()'
        finally:
            os.unlink(config_path)

    def test_url_with_path(self, temp_config_file):
        """Test API URL with path component"""
        config_content = """
[ganeti]
api = https://ganeti.example.com:5080/api/v2
user = testuser
password = testpass
"""
        config_path = temp_config_file(config_content)
        try:
            config = parse_config(config_path)
            assert config['ganeti_api_endpoint'] == 'https://ganeti.example.com:5080/api/v2'
        finally:
            os.unlink(config_path)
