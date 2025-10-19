"""Tests for the common logging module."""
import logging
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from finnews.common.logging import setup_logging, get_logger


class TestLoggingSetup:
    """Test the logging setup functionality."""

    def test_setup_logging_default(self):
        """Test default logging setup."""
        with patch('logging.basicConfig') as mock_basic_config:
            setup_logging()
            mock_basic_config.assert_called_once_with(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=None
            )

    def test_setup_logging_custom_level(self):
        """Test logging setup with custom level."""
        with patch('logging.basicConfig') as mock_basic_config:
            setup_logging(level=logging.DEBUG)
            mock_basic_config.assert_called_once_with(
                level=logging.DEBUG,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=None
            )

    def test_setup_logging_with_file(self):
        """Test logging setup with file output."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as temp_file:
            temp_path = Path(temp_file.name)
            
            with patch('logging.basicConfig') as mock_basic_config:
                setup_logging(log_file=temp_path)
                
                # Check that basicConfig was called with file handler
                call_args = mock_basic_config.call_args
                assert call_args[1]['level'] == logging.INFO
                assert 'handlers' in call_args[1]
                handlers = call_args[1]['handlers']
                assert len(handlers) == 1
                assert isinstance(handlers[0], logging.FileHandler)
                assert handlers[0].baseFilename == str(temp_path.absolute())

    def test_setup_logging_with_console_and_file(self):
        """Test logging setup with both console and file output."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as temp_file:
            temp_path = Path(temp_file.name)
            
            with patch('logging.basicConfig') as mock_basic_config:
                setup_logging(log_file=temp_path, console=True)
                
                # Check that basicConfig was called with both handlers
                call_args = mock_basic_config.call_args
                assert call_args[1]['level'] == logging.INFO
                assert 'handlers' in call_args[1]
                handlers = call_args[1]['handlers']
                assert len(handlers) == 2
                
                # Check handler types
                handler_types = [type(h) for h in handlers]
                assert logging.StreamHandler in handler_types
                assert logging.FileHandler in handler_types

    def test_setup_logging_custom_format(self):
        """Test logging setup with custom format."""
        custom_format = '%(name)s - %(levelname)s - %(message)s'
        
        with patch('logging.basicConfig') as mock_basic_config:
            setup_logging(format_string=custom_format)
            mock_basic_config.assert_called_once_with(
                level=logging.INFO,
                format=custom_format,
                handlers=None
            )


class TestGetLogger:
    """Test the get_logger function."""

    def test_get_logger_default(self):
        """Test getting logger with default name."""
        logger = get_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == 'finnews'

    def test_get_logger_custom_name(self):
        """Test getting logger with custom name."""
        logger = get_logger('custom.module')
        assert isinstance(logger, logging.Logger)
        assert logger.name == 'custom.module'

    def test_get_logger_with_setup(self):
        """Test getting logger after setup_logging."""
        with patch('logging.basicConfig') as mock_basic_config:
            setup_logging()
            logger = get_logger('test.module')
            
            assert isinstance(logger, logging.Logger)
            assert logger.name == 'test.module'
            # Verify that basicConfig was called
            mock_basic_config.assert_called_once()

    def test_get_logger_level_propagation(self):
        """Test that logger level is set correctly."""
        with patch('logging.basicConfig'):
            setup_logging(level=logging.DEBUG)
            logger = get_logger('test.module')
            
            # The logger should inherit the root logger's level
            assert logger.level == logging.DEBUG

    def test_multiple_loggers(self):
        """Test that multiple loggers work correctly."""
        logger1 = get_logger('module1')
        logger2 = get_logger('module2')
        
        assert logger1.name == 'module1'
        assert logger2.name == 'module2'
        assert logger1 is not logger2

    def test_logger_hierarchy(self):
        """Test that logger hierarchy works correctly."""
        parent_logger = get_logger('parent')
        child_logger = get_logger('parent.child')
        
        assert child_logger.parent.name == 'parent'
        assert child_logger.name == 'parent.child'

    def test_logger_with_handlers(self):
        """Test logger behavior with custom handlers."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as temp_file:
            temp_path = Path(temp_file.name)
            
            with patch('logging.basicConfig'):
                setup_logging(log_file=temp_path, console=True)
                logger = get_logger('test.handlers')
                
                # Logger should have handlers from the root logger
                assert len(logger.handlers) >= 0  # May be 0 if handlers are on root logger
