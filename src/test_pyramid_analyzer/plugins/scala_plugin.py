"""Scala language plugin."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .base import LanguagePlugin


class ScalaPlugin(LanguagePlugin):
    name = "scala"
    extensions = [".scala"]
    test_file_patterns = [
        "*Spec.scala",
        "*Suite.scala",
        "*Test.scala",
        "*Tests.scala",
        "*IT.scala",
        "*Specification.scala",
    ]

    # ScalaTest base classes — unit vs integration
    _SCALATEST_UNIT = re.compile(
        r"extends AnyFlatSpec|extends AnyWordSpec|extends AnyFunSpec"
        r"|extends AnyFunSuite|extends PropSpec|extends AnyFreeSpec"
        r"|extends UnitSpec"
    )
    _SCALATEST_INTEGRATION = re.compile(
        r"extends IntegrationSpec|extends IntegrationPatience"
        r"|with ScalatestRouteTest|extends PlaySpec|extends WithApplication"
    )

    # specs2
    _SPECS2_INTEGRATION = re.compile(r"extends org\.specs2\.integration|IntegrationSpec")
    _SPECS2_UNIT = re.compile(r"import org\.specs2\.|extends Specification")

    # Akka TestKit (integration)
    _AKKA_TESTKIT = re.compile(r"AkkaSpec|TestKit|AkkaTestkit|akka\.testkit")

    # Gatling (load/performance testing → E2E-ish)
    _GATLING = re.compile(r"import io\.gatling\.|extends Simulation|setUp\s*\(|scenario\s*\(")

    # ScalaCheck (property-based → unit)
    _SCALACHECK = re.compile(r"import org\.scalacheck\.|extends Checkers|forAll\s*\(|Gen\.")

    # Testcontainers
    _TESTCONTAINERS = re.compile(
        r"com\.dimafeng\.testcontainers\.|TestcontainersSuite|ForAllTestContainer"
    )

    def extra_signals(
        self, file_path: Path, content: str, rules: dict[str, Any]
    ) -> list[dict[str, Any]]:
        signals: list[dict[str, Any]] = []

        if self._GATLING.search(content):
            signals.append({
                "test_type": "e2e",
                "source": "framework",
                "name": "Gatling load/simulation test",
                "weight": 4.0,
                "matched_text": "Gatling Simulation / setUp()",
            })

        if (self._SCALATEST_INTEGRATION.search(content)
                or self._AKKA_TESTKIT.search(content)
                or self._TESTCONTAINERS.search(content)
                or self._SPECS2_INTEGRATION.search(content)):
            signals.append({
                "test_type": "integration",
                "source": "framework",
                "name": "ScalaTest integration / AkkaTestKit / Testcontainers",
                "weight": 3.5,
                "matched_text": "IntegrationPatience / AkkaSpec / TestcontainersSuite",
            })

        if self._SCALATEST_UNIT.search(content) or self._SPECS2_UNIT.search(content):
            signals.append({
                "test_type": "unit",
                "source": "framework",
                "name": "ScalaTest / specs2 unit spec",
                "weight": 2.5,
                "matched_text": "AnyFlatSpec / AnyWordSpec / Specification",
            })

        if self._SCALACHECK.search(content):
            signals.append({
                "test_type": "unit",
                "source": "framework",
                "name": "ScalaCheck property-based test",
                "weight": 2.0,
                "matched_text": "scalacheck / forAll / Gen.",
            })

        return signals
