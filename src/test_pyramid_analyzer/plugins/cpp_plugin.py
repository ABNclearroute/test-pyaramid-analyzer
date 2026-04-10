"""C and C++ language plugin."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .base import LanguagePlugin


class CppPlugin(LanguagePlugin):
    name = "cpp"
    extensions = [".cpp", ".cc", ".cxx", ".c", ".h", ".hpp"]
    test_file_patterns = [
        "*_test.cpp",
        "*_test.cc",
        "*_test.cxx",
        "test_*.cpp",
        "test_*.c",
        "*Test.cpp",
        "*Spec.cpp",
        "*_spec.cpp",
    ]

    # Google Test
    _GTEST = re.compile(r'#include\s+[<"]gtest/gtest\.h[">]')
    _GTEST_FIXTURE = re.compile(r"class \w+ : public ::testing::Test|TEST_F\s*\(")
    _GTEST_MOCK = re.compile(r'#include\s+[<"]gmock/gmock\.h[">]|EXPECT_CALL\s*\(|ON_CALL\s*\(')

    # Catch2
    _CATCH2 = re.compile(r'#include\s+[<"]catch2/catch|#include\s+[<"]catch\.hpp[">]|SCENARIO\s*\(')

    # doctest
    _DOCTEST = re.compile(r'#include\s+[<"]doctest/doctest\.h[">]')

    # Boost.Test
    _BOOST_TEST = re.compile(r"boost/test/|BOOST_AUTO_TEST_SUITE|BOOST_CHECK|BOOST_REQUIRE")

    # Integration hints: network or DB in test
    _HTTP_LIB = re.compile(r"#include.*curl/curl\.h|httplib\.h|libcurl|beast/http")
    _DB_LIB = re.compile(r"#include.*libpq-fe\.h|mysql\.h|sqlite3\.h|pqxx/pqxx")

    def extra_signals(
        self, file_path: Path, content: str, rules: dict[str, Any]
    ) -> list[dict[str, Any]]:
        signals: list[dict[str, Any]] = []

        if self._GTEST_MOCK.search(content):
            signals.append({
                "test_type": "unit",
                "source": "framework",
                "name": "GoogleMock (gmock)",
                "weight": 3.0,
                "matched_text": "gmock.h / EXPECT_CALL",
            })
        elif self._GTEST.search(content):
            if self._GTEST_FIXTURE.search(content):
                # Fixtures with real deps → integration; simple TEST() → unit
                if self._HTTP_LIB.search(content) or self._DB_LIB.search(content):
                    signals.append({
                        "test_type": "integration",
                        "source": "framework",
                        "name": "Google Test (integration fixture)",
                        "weight": 2.5,
                        "matched_text": "TEST_F with HTTP/DB",
                    })
                else:
                    signals.append({
                        "test_type": "unit",
                        "source": "framework",
                        "name": "Google Test fixture",
                        "weight": 2.0,
                        "matched_text": "TEST_F()",
                    })
            else:
                signals.append({
                    "test_type": "unit",
                    "source": "framework",
                    "name": "Google Test",
                    "weight": 2.5,
                    "matched_text": "gtest/gtest.h",
                })

        if self._CATCH2.search(content):
            signals.append({
                "test_type": "unit",
                "source": "framework",
                "name": "Catch2",
                "weight": 2.5,
                "matched_text": "catch2/catch.hpp / SCENARIO()",
            })

        if self._DOCTEST.search(content):
            signals.append({
                "test_type": "unit",
                "source": "framework",
                "name": "doctest",
                "weight": 2.5,
                "matched_text": "doctest/doctest.h",
            })

        if self._BOOST_TEST.search(content):
            signals.append({
                "test_type": "unit",
                "source": "framework",
                "name": "Boost.Test",
                "weight": 2.5,
                "matched_text": "BOOST_AUTO_TEST_SUITE / BOOST_CHECK",
            })

        if self._HTTP_LIB.search(content):
            signals.append({
                "test_type": "integration",
                "source": "framework",
                "name": "libcurl / httplib (C++ HTTP)",
                "weight": 2.5,
                "matched_text": "curl/curl.h / httplib.h",
            })

        if self._DB_LIB.search(content):
            signals.append({
                "test_type": "integration",
                "source": "framework",
                "name": "libpq / mysql / sqlite3 (C++ DB)",
                "weight": 3.0,
                "matched_text": "libpq-fe.h / mysql.h / sqlite3.h",
            })

        return signals
