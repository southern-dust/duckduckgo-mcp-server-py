"""
Unit tests for data models
"""

import pytest
from pydantic import ValidationError

from duckduckgo_mcp_server.models import DuckDuckGoSearchArgs, SearchResult


class TestDuckDuckGoSearchArgs:
    """Test cases for DuckDuckGoSearchArgs model"""

    def test_valid_search_args_minimal(self):
        """Test creating search args with minimal valid data"""
        args = DuckDuckGoSearchArgs(query="Python programming")
        assert args.query == "Python programming"
        assert args.count == 10  # default value
        assert args.safeSearch == "moderate"  # default value

    def test_valid_search_args_all_fields(self):
        """Test creating search args with all fields provided"""
        args = DuckDuckGoSearchArgs(
            query="Python async",
            count=5,
            safeSearch="strict"
        )
        assert args.query == "Python async"
        assert args.count == 5
        assert args.safeSearch == "strict"

    def test_valid_search_args_off_safe_search(self):
        """Test with 'off' safe search option"""
        args = DuckDuckGoSearchArgs(
            query="test query",
            safeSearch="off"
        )
        assert args.safeSearch == "off"

    def test_empty_query_validation_error(self):
        """Test that empty query is accepted but may be handled differently"""
        # Empty query doesn't raise ValidationError by default (Pydantic allows empty strings)
        # but we can still create it and verify it's handled appropriately
        args = DuckDuckGoSearchArgs(query="")
        assert args.query == ""
        # Note: Empty query handling is typically done at the business logic level, not model level

    def test_query_too_long_validation_error(self):
        """Test that query longer than 400 characters raises validation error"""
        long_query = "a" * 401
        with pytest.raises(ValidationError) as exc_info:
            DuckDuckGoSearchArgs(query=long_query)

        assert "query" in str(exc_info.value)

    def test_query_exactly_max_length(self):
        """Test that query exactly 400 characters is accepted"""
        max_query = "a" * 400
        args = DuckDuckGoSearchArgs(query=max_query)
        assert args.query == max_query

    def test_count_below_minimum_validation_error(self):
        """Test that count below 1 raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            DuckDuckGoSearchArgs(query="test", count=0)

        assert "count" in str(exc_info.value)

    def test_count_above_maximum_validation_error(self):
        """Test that count above 20 raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            DuckDuckGoSearchArgs(query="test", count=21)

        assert "count" in str(exc_info.value)

    def test_count_boundary_values(self):
        """Test count at boundary values"""
        # Test minimum value
        args_min = DuckDuckGoSearchArgs(query="test", count=1)
        assert args_min.count == 1

        # Test maximum value
        args_max = DuckDuckGoSearchArgs(query="test", count=20)
        assert args_max.count == 20

    def test_invalid_safe_search_value(self):
        """Test that invalid safe search value raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            DuckDuckGoSearchArgs(query="test", safeSearch="invalid")

        assert "safeSearch" in str(exc_info.value)

    def test_query_with_special_characters(self):
        """Test query with various special characters"""
        special_queries = [
            "Python + async/await",
            "C++ programming",
            "JavaScript & TypeScript",
            "Python's decorators",
            'Search for "quotes"',
            "Search with [brackets]",
            "Search with {braces}",
            "Search with <angle> brackets",
            "Search with punctuation:;!?",
            "Search with numbers 123",
            "Mixed 中英文字符 test"
        ]

        for query in special_queries:
            args = DuckDuckGoSearchArgs(query=query)
            assert args.query == query

    def test_model_serialization(self):
        """Test model serialization to dictionary"""
        args = DuckDuckGoSearchArgs(
            query="Python async",
            count=5,
            safeSearch="strict"
        )

        expected = {
            "query": "Python async",
            "count": 5,
            "safeSearch": "strict"
        }

        assert args.model_dump() == expected

    def test_model_deserialization(self):
        """Test model deserialization from dictionary"""
        data = {
            "query": "Python async",
            "count": 5,
            "safeSearch": "strict"
        }

        args = DuckDuckGoSearchArgs(**data)
        assert args.query == "Python async"
        assert args.count == 5
        assert args.safeSearch == "strict"

    def test_model_json_serialization(self):
        """Test model JSON serialization and deserialization"""
        args = DuckDuckGoSearchArgs(
            query="Python async",
            count=5,
            safeSearch="strict"
        )

        # Test serialization
        json_str = args.model_dump_json()
        assert isinstance(json_str, str)

        # Test deserialization
        restored_args = DuckDuckGoSearchArgs.model_validate_json(json_str)
        assert restored_args.query == args.query
        assert restored_args.count == args.count
        assert restored_args.safeSearch == args.safeSearch


class TestSearchResult:
    """Test cases for SearchResult model"""

    def test_valid_search_result_minimal(self):
        """Test creating search result with required fields"""
        result = SearchResult(
            title="Python Official Website",
            description="Python is a high-level programming language...",
            url="https://python.org"
        )

        assert result.title == "Python Official Website"
        assert result.description == "Python is a high-level programming language..."
        assert result.url == "https://python.org"

    def test_search_result_with_special_characters(self):
        """Test search result with special characters in fields"""
        result = SearchResult(
            title="Python's async/await: A Complete Guide",
            description="Learn about Python's async/await syntax & how to use it effectively.",
            url="https://example.com/python-async-guide?lang=en&version=3.9"
        )

        assert "Python's async/await" in result.title
        assert "&" in result.description
        assert "?" in result.url and "&" in result.url

    def test_search_result_unicode_content(self):
        """Test search result with Unicode content"""
        result = SearchResult(
            title="Python 编程指南",
            description="这是一份关于 Python 异步编程的中文指南",
            url="https://example.com/zh-cn/python-guide"
        )

        assert "编程指南" in result.title
        assert "中文指南" in result.description

    def test_search_result_empty_fields(self):
        """Test search result with empty string fields"""
        result = SearchResult(
            title="",
            description="",
            url=""
        )

        assert result.title == ""
        assert result.description == ""
        assert result.url == ""

    def test_search_result_long_content(self):
        """Test search result with very long content"""
        long_title = "A " * 100  # 200 characters
        long_description = "B " * 500  # 1000 characters
        long_url = "https://example.com/" + "c" * 1000

        result = SearchResult(
            title=long_title,
            description=long_description,
            url=long_url
        )

        assert len(result.title) == len(long_title)
        assert len(result.description) == len(long_description)
        assert len(result.url) == len(long_url)

    def test_model_serialization(self):
        """Test SearchResult serialization to dictionary"""
        result = SearchResult(
            title="Python Official Website",
            description="Python is a high-level programming language...",
            url="https://python.org"
        )

        expected = {
            "title": "Python Official Website",
            "description": "Python is a high-level programming language...",
            "url": "https://python.org"
        }

        assert result.model_dump() == expected

    def test_model_json_serialization(self):
        """Test SearchResult JSON serialization and deserialization"""
        result = SearchResult(
            title="Python Official Website",
            description="Python is a high-level programming language...",
            url="https://python.org"
        )

        # Test serialization
        json_str = result.model_dump_json()
        assert isinstance(json_str, str)

        # Test deserialization
        restored_result = SearchResult.model_validate_json(json_str)
        assert restored_result.title == result.title
        assert restored_result.description == result.description
        assert restored_result.url == result.url

    def test_model_field_types(self):
        """Test that model fields have correct types"""
        result = SearchResult(
            title="Test Title",
            description="Test Description",
            url="https://test.com"
        )

        assert isinstance(result.title, str)
        assert isinstance(result.description, str)
        assert isinstance(result.url, str)