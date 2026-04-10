# test-pyramid-analyzer

A deterministic, rule-based CLI tool that scans a repository, classifies test files into **unit / integration / E2E** categories, detects anti-patterns, and generates actionable reports — with zero AI/LLM dependency.

```
╔══════════════════════════════════════════════════════════════╗
║  Test Pyramid Analyzer                                        ║
║  Repo: /path/to/my-service        Scanned: 2024-01-15 UTC   ║
╚══════════════════════════════════════════════════════════════╝

 Test Distribution
 ┌──────────────┬───────┬─────────┬────────────────────────────────┐
 │ Type         │ Count │   Share │ Distribution                   │
 ├──────────────┼───────┼─────────┼────────────────────────────────┤
 │ Unit         │    48 │  64.0 % │ ████████████████████░░░░░░░░░░ │
 │ Integration  │    18 │  24.0 % │ ████████░░░░░░░░░░░░░░░░░░░░░░ │
 │ E2E          │     6 │   8.0 % │ ███░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
 │ Ambiguous    │     3 │   4.0 % │ █░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
 └──────────────┴───────┴─────────┴────────────────────────────────┘
```

---

## Features

| Feature | Detail |
|---|---|
| **12 languages** | Python, Java, JS/TS, Go, Ruby, C#, Rust, Kotlin, PHP, C/C++, Groovy, Scala |
| **100+ frameworks** | Every major unit, integration, and E2E framework per language |
| **7 CI platforms** | GitHub Actions, GitLab CI, CircleCI, Azure Pipelines, Travis CI, Bitbucket, Jenkins |
| **Deterministic** | 100 % rule-based — no LLM, no network calls |
| **Configurable** | Deep-merge your own `rules.yaml` on top of the defaults |
| **Anti-patterns** | Ice Cream Cone, Hourglass, Testing Trophy, missing layers |
| **Output formats** | Console (Rich), JSON, HTML (interactive Chart.js report) |
| **Plugin system** | Add new languages by extending `LanguagePlugin` |
| **Explain Mode** | `--debug` prints a full per-file signal breakdown — exactly why each file was classified |
| **PR Comments** | GitHub Action posts (and idempotently updates) a structured markdown comment on every PR |

---

## Supported Languages

| Language | Extensions | Example test patterns |
|---|---|---|
| **Python** | `.py` | `test_*.py`, `*_test.py` |
| **Java** | `.java` | `*Test.java`, `*IT.java`, `*Spec.java` |
| **JavaScript / TypeScript** | `.js` `.ts` `.jsx` `.tsx` `.mjs` | `*.test.js`, `*.spec.ts` |
| **Go** | `.go` | `*_test.go` |
| **Ruby** | `.rb` | `*_spec.rb`, `*_test.rb` |
| **C# (.NET)** | `.cs` | `*Tests.cs`, `*Spec.cs`, `*Steps.cs` |
| **Rust** | `.rs` | `*_test.rs`, `tests.rs` |
| **Kotlin** | `.kt` `.kts` | `*Test.kt`, `*IT.kt`, `*Spec.kt` |
| **PHP** | `.php` | `*Test.php`, `*Cest.php`, `*FeatureTest.php` |
| **C / C++** | `.cpp` `.cc` `.cxx` `.c` | `*_test.cpp`, `test_*.c`, `*Spec.cpp` |
| **Groovy** | `.groovy` | `*Spec.groovy`, `*Specification.groovy` |
| **Scala** | `.scala` | `*Spec.scala`, `*Suite.scala`, `*IT.scala` |

---

## Supported Frameworks

### Unit

| Language | Frameworks |
|---|---|
| Python | `unittest`, `pytest`, `nose2`, `hypothesis`, `doctest` |
| Java | `JUnit 5`, `JUnit 4`, `TestNG`, `Mockito`, `EasyMock`, `PowerMock` |
| JavaScript | `Jest`, `Vitest`, `Mocha`, `Jasmine`, `QUnit`, `Ava`, `Tape`, `Chai`, `Sinon`, `Karma` |
| Go | `testing` (stdlib), `testify`, `gomock/mockery`, `gocheck` |
| Ruby | `RSpec`, `Minitest`, `Test::Unit` |
| C# | `xUnit`, `NUnit`, `MSTest`, `Moq`, `NSubstitute`, `FakeItEasy`, `FluentAssertions` |
| Rust | `#[test]` / `#[cfg(test)]`, `rstest`, `proptest` |
| Kotlin | `JUnit`, `Kotest`, `MockK` |
| PHP | `PHPUnit`, `PHPSpec`, `Kahlan`, `Mockery` |
| C/C++ | `Google Test`, `Catch2`, `doctest`, `Boost.Test`, `CppUnit`, `GoogleMock` |
| Groovy | `Spock` (`extends Specification`) |
| Scala | `ScalaTest`, `specs2`, `MUnit`, `ScalaCheck` |

### Integration

| Language | Frameworks |
|---|---|
| Python | `pytest-django`, `pytest-flask`, `pytest-fastapi/httpx`, `testcontainers`, `requests-mock`, `responses`, `factory_boy`, `tavern`, `behave`, `robot framework` |
| Java | `Spring Boot Test` (`@SpringBootTest`, `@DataJpaTest`, `@WebMvcTest`), `Testcontainers`, `WireMock`, `RestAssured`, `Arquillian`, `DBUnit`, `Spring MVC Test` |
| JavaScript | `supertest`, `MSW`, `nock`, `axios-mock-adapter`, `pact-js`, `@testing-library` |
| Go | `testcontainers-go`, `dockertest`, `sqlmock`, `net/http/httptest`, `goconvey` |
| Ruby | `rack-test`, `rspec-rails` (request specs), `FactoryBot`, `DatabaseCleaner`, `VCR` |
| C# | `WebApplicationFactory`, `Testcontainers.DotNet`, `EF Core InMemory/SQLite`, `Pact-Net` |
| Rust | `actix-web::test`, `axum-test`, `sqlx::test`, `wiremock-rs` |
| Kotlin | `Spring Boot Test`, `Testcontainers`, `Ktor testApplication`, `Kotest extensions` |
| PHP | `Laravel Feature / HTTP test`, `PHPUnit DbUnit` |
| C/C++ | `libcurl`, `httplib`, `libpq`, `mysql.h`, `sqlite3.h` |
| Groovy | `Spock` + `@SpringBootTest`, `Testcontainers` |
| Scala | `ScalaTest IntegrationPatience`, `AkkaTestKit`, `Testcontainers-Scala`, `Play WS Test` |

### E2E

| Language | Frameworks |
|---|---|
| Python | `Selenium`, `Playwright`, `Pyppeteer`, `Helium`, `Splinter`, `Robot Framework`, `Locust` |
| Java | `Selenium WebDriver`, `Playwright`, `Cucumber-JVM`, `JBehave`, `Appium`, `Geb`, `Gatling` |
| JavaScript | `Cypress`, `Playwright`, `Puppeteer`, `Nightwatch`, `WebDriverIO`, `TestCafe`, `Detox`, `Appium`, `Taiko` |
| Go | `chromedp`, `Rod`, `playwright-go`, `Agouti` |
| Ruby | `Capybara`, `Selenium WebDriver`, `Watir`, `Cucumber` |
| C# | `Selenium WebDriver`, `Playwright (.NET)`, `SpecFlow`, `Reqnroll` |
| Rust | `fantoccini`, `thirtyfour` |
| Kotlin | `Selenium`, `Playwright` |
| PHP | `Behat`, `Laravel Dusk`, `Codeception Acceptance` |
| Groovy | `Geb` (`GebSpec`) |
| Scala | `Gatling` (`Simulation`), `ScalaTest Selenium DSL` |

---

## Supported CI Platforms

The `tpa scan` and `tpa ci` commands auto-detect the CI platform from the file path:

| Platform | Auto-detected file(s) | Parser |
|---|---|---|
| **GitHub Actions** | `.github/workflows/*.yml` | Jobs → steps → `run:` |
| **GitLab CI** | `.gitlab-ci.yml` | Top-level job → `script:` |
| **CircleCI** | `.circleci/config.yml` | Jobs → steps → `run:` (string or dict) |
| **Azure Pipelines** | `azure-pipelines.yml` | Stages → jobs → `script:` / `bash:` / `pwsh:` |
| **Travis CI** | `.travis.yml` | `before_script:`, `script:`, `after_success:` |
| **Bitbucket Pipelines** | `bitbucket-pipelines.yml` | Pipelines → step → `script:` |
| **Jenkins** | `Jenkinsfile` | Regex extracts `sh '...'` from `stage()` blocks |

All platforms recognize 50+ test commands including `pytest`, `go test`, `cargo test`, `dotnet test`, `rspec`, `phpunit`, `behat`, `jest`, `vitest`, `cypress`, `playwright`, `sbt test`, `gradlew test`, `ctest`, and more.

```bash
# Any of these are parsed automatically
tpa ci .github/workflows/ci.yml
tpa ci .gitlab-ci.yml
tpa ci .circleci/config.yml
tpa ci azure-pipelines.yml
tpa ci .travis.yml
tpa ci bitbucket-pipelines.yml
tpa ci Jenkinsfile
```

---

## Installation

```bash
# From source
git clone https://github.com/your-org/test-pyramid-analyzer
cd test-pyramid-analyzer
pip install -e .

# Or once published:
pip install test-pyramid-analyzer
```

Requires **Python 3.9+**.

---

## Quick Start

```bash
# Scan a local repository (console output)
tpa scan /path/to/my-repo

# Scan and include CI pipeline analysis
tpa scan /path/to/my-repo --ci .github/workflows/ci.yml

# Export a JSON report
tpa scan /path/to/my-repo --output json --out-file report.json

# Generate a beautiful HTML report
tpa scan /path/to/my-repo --output html --out-file report.html

# Use a custom rules file
tpa scan /path/to/my-repo --config my-rules.yaml

# Debug mode — see per-file scores and signal breakdown
tpa scan /path/to/my-repo --debug

# Exclude directories
tpa scan /path/to/my-repo --exclude vendor,third_party

# Parse just a CI pipeline
tpa ci .github/workflows/ci.yml
tpa ci .gitlab-ci.yml
tpa ci Jenkinsfile
```

---

## Commands

### `tpa scan <repo_path>`

Scan a repository and classify all discovered test files.

| Option | Default | Description |
|---|---|---|
| `--config PATH` | built-in | Custom rules YAML (deep-merged on top of defaults) |
| `--output FORMAT` | `console` | `console` \| `json` \| `html` |
| `--out-file PATH` | stdout | Write report to a file |
| `--ci PATH` | auto-detect | CI pipeline file to parse (any supported platform) |
| `--exclude DIRS` | — | Comma-separated directory names to skip |
| `--debug` | off | Explain Mode — full per-file signal breakdown, scores, and confidence |

### `tpa ci <pipeline_file>`

Parse a CI pipeline file and show detected test steps.

| Option | Default | Description |
|---|---|---|
| `--output FORMAT` | `console` | `console` \| `json` |
| `--out-file PATH` | stdout | Write output to a file |

---

## Explain Mode (`--debug`)

Add `--debug` to any `tpa scan` command to see exactly **why** each file was classified into its category — every signal, its source, the matched text, and its weight contribution.

```bash
tpa scan /path/to/my-repo --debug
```

### Output per file

```
  tests/unit/test_calculator.py  python  ────────────────────────────────────
  Signals Detected  (4 signals)

 Source      Signal                   Matched              Weight  → Type
─────────────────────────────────────────────────────────────────────────────
 code        mock / patch / stub/fake mock  ·  MagicMock     +3.6  unit
 code        assert / assertEquals    assertEqual  ·  …       +1.5  unit
 framework   unittest                 import unittest         +2.5  unit
 path        /unit/                   /unit/                  +3.0  unit

  Score Breakdown  (total: 10.6)

  Unit          ████████████████████████  10.6  ←
  Integration   ░░░░░░░░░░░░░░░░░░░░░░░░   0.0
  E2E           ░░░░░░░░░░░░░░░░░░░░░░░░   0.0

  → UNIT  confidence: 100%  ████████████████████
```

### Ambiguous file

When two types score close together the file is flagged instead of guessing:

```
  ⚠  Ambiguous Classification
  Competing types too close — integration: 6.0  vs  unit: 5.5  (gap: 4.0% of total)
```

### End-of-run summary table

After all files the explain view closes with a compact one-line-per-file summary:

```
 File                                   Lang    Classification   Conf   Unit   Intg   E2E   Signals
──────────────────────────────────────────────────────────────────────────────────────────────────
 tests/e2e/test_login_flow.py           python  e2e              0.97    1.5    0.0  43.0       8
 tests/integration/test_db_connection.py python integration      0.88    1.5   11.5   0.0       4
 tests/unit/test_calculator.py          python  unit             1.00   10.6    0.0   0.0       4
```

### Signal sources explained

| Source | What it detects | Example match |
|---|---|---|
| `path` | Directory name in the file path | `/e2e/`, `/unit/`, `/integration/` |
| `framework` | Import or annotation of a known test framework | `import playwright`, `@SpringBootTest` |
| `code` | Regex pattern inside the file body | `page.goto(`, `psycopg2`, `mock.patch` |
| `plugin` | Language-specific heuristic from a plugin | `@pytest.mark.integration`, `*IT.java` suffix |

---

## Scoring Engine

Each test file is scored across three dimensions:

```
scores = {
  "unit":        Σ weights of unit-related signals,
  "integration": Σ weights of integration-related signals,
  "e2e":         Σ weights of e2e-related signals,
}

confidence     = max(scores.values()) / sum(scores.values())
classification = argmax(scores)   # unless gap < threshold → "ambiguous"
```

### Signal sources (applied in order)

| Source | Example | Weight range |
|---|---|---|
| **Path pattern** | file lives in `/e2e/` or `/integration/` | 1.5 – 3.5 |
| **Framework import** | `import playwright`, `@SpringBootTest`, `extends GebSpec` | 1.5 – 5.0 |
| **Code pattern** | `cy.visit(`, `psycopg2`, `mock.patch`, `#[sqlx::test]` | 0.5 – 3.5 |
| **Plugin heuristic** | `@pytest.mark.integration`, `*IT.java` suffix, `type: :system` | 2.0 – 4.5 |

---

## Custom Rules

Create a YAML file that overrides only the sections you need. Everything is deep-merged on top of the built-in defaults, so you only specify what differs.

```yaml
# my-rules.yaml
version: "2.0"

# Add a new language not in the defaults
languages:
  swift:
    extensions: [".swift"]
    test_file_patterns:
      - "*Tests.swift"
      - "*Spec.swift"

signals:
  # Add extra path-based signals
  path_patterns:
    e2e:
      - {pattern: "/smoke/",    weight: 3.0}
      - {pattern: "/contract/", weight: 2.5}

  # Add framework detection for the new language
  frameworks:
    unit:
      - name: "XCTest"
        languages: ["swift"]
        imports: ["import XCTest", "XCTestCase"]
        weight: 2.5

    e2e:
      - name: "XCUITest"
        languages: ["swift"]
        imports: ["XCUIApplication"]
        weight: 4.5

scoring:
  ambiguity_threshold: 0.20
  min_confidence: 0.35
```

```bash
tpa scan ./my-swift-repo --config my-rules.yaml
```

---

## Plugin System

For language-specific heuristics that go beyond what a YAML rule can express (naming conventions, decorator patterns, AST-level analysis), extend `LanguagePlugin`:

```python
# my_swift_plugin.py
from test_pyramid_analyzer.plugins.base import LanguagePlugin
from test_pyramid_analyzer.plugins import register_plugin
from pathlib import Path

class SwiftPlugin(LanguagePlugin):
    name = "swift"
    extensions = [".swift"]
    test_file_patterns = ["*Tests.swift", "*Spec.swift"]

    def extra_signals(self, file_path: Path, content: str, rules: dict):
        signals = []

        # XCUITest → E2E
        if "XCUIApplication" in content:
            signals.append({
                "test_type": "e2e",
                "source": "framework",
                "name": "XCUITest (UI automation)",
                "weight": 4.5,
                "matched_text": "XCUIApplication",
            })

        # Networking in tests → integration
        if "URLSession" in content or "Alamofire" in content:
            signals.append({
                "test_type": "integration",
                "source": "framework",
                "name": "URLSession / Alamofire (network test)",
                "weight": 2.5,
                "matched_text": "URLSession / Alamofire",
            })

        return signals

register_plugin(SwiftPlugin())
```

---

## Anti-Pattern Detection

| Anti-pattern | Condition | Severity |
|---|---|---|
| **Ice Cream Cone** | E2E > 30 % | warning / error |
| **Hourglass** | Integration < 10 % AND E2E > 20 % | warning |
| **Testing Trophy (over-rotated)** | Unit < 15 % AND Integration > 50 % | warning |
| **Insufficient Unit Tests** | Unit < 20 % | warning |
| **No Integration Tests** | Integration = 0 % | warning |

---

## Project Structure

```
test-pyramid-analyzer/
├── action.yml               ← GitHub Action metadata (inputs, outputs, branding)
├── Dockerfile               ← Docker image for the GitHub Action (python:3.11-slim)
├── entrypoint.sh            ← Action entrypoint: scan → outputs → PR comment → gates
├── LICENSE                  ← MIT
├── src/test_pyramid_analyzer/
│   ├── cli.py               ← Typer CLI (scan / ci / version)
│   ├── models.py            ← Data models (Signal, TestFileResult, …)
│   ├── rules_loader.py      ← YAML rules loading & deep-merge
│   ├── scanner.py           ← Repository file discovery
│   ├── parser.py            ← Signal extraction (path / framework / code)
│   ├── scorer.py            ← Weighted score aggregation
│   ├── confidence.py        ← Confidence & ambiguity calculation
│   ├── classifier.py        ← End-to-end orchestration
│   ├── anti_patterns.py     ← Anti-pattern detection & recommendations
│   ├── ci_parser.py         ← Multi-platform CI pipeline parser
│   ├── report_generator.py  ← Console / JSON / HTML output
│   ├── debug_printer.py     ← Explain Mode renderer (--debug)
│   ├── pr_commenter.py      ← GitHub PR comment poster (idempotent)
│   ├── config/
│   │   └── default_rules.yaml    ← 12 languages, 100+ frameworks
│   ├── templates/
│   │   └── report.html.j2        ← Dark-themed Chart.js report
│   └── plugins/
│       ├── base.py               ← LanguagePlugin ABC
│       ├── python_plugin.py      ← pytest marks, django_db, e2e markers
│       ├── java_plugin.py        ← Spring annotations, IT naming
│       ├── javascript_plugin.py  ← Cypress, Playwright, RTL, MSW
│       ├── go_plugin.py          ← testcontainers-go, chromedp, rod
│       ├── ruby_plugin.py        ← RSpec type metadata, Capybara, rack-test
│       ├── csharp_plugin.py      ← WebApplicationFactory, Selenium, SpecFlow
│       ├── rust_plugin.py        ← cfg(test), sqlx::test, actix-web::test
│       ├── kotlin_plugin.py      ← MockK, Kotest, Spring Boot, Ktor
│       ├── php_plugin.py         ← Behat, Laravel Dusk, Codeception
│       ├── cpp_plugin.py         ← Google Test, Catch2, doctest, Boost.Test
│       ├── groovy_plugin.py      ← Spock, Geb, Testcontainers
│       └── scala_plugin.py       ← ScalaTest, AkkaTestKit, Gatling
├── tests/
│   ├── fixtures/sample_repo/     ← Sample repo + GitHub Actions workflow
│   ├── test_scanner.py
│   ├── test_classifier.py
│   ├── test_scorer.py
│   ├── test_confidence.py
│   ├── test_anti_patterns.py
│   └── test_ci_parser.py
└── pyproject.toml
```

---

## Development

```bash
# Install with dev extras
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=test_pyramid_analyzer --cov-report=term-missing

# Lint
ruff check src/ tests/
```

---

## Example Output

### Console

```
  Test Pyramid Analyzer
  Repo: /home/user/my-service
  Scanned: 2024-01-15T10:23:45+00:00

  Test Distribution
  ╭──────────────┬───────┬─────────┬────────────────────────────────╮
  │ Type         │ Count │   Share │ Distribution                   │
  ├──────────────┼───────┼─────────┼────────────────────────────────┤
  │ Unit         │    48 │  64.0 % │ ████████████████████░░░░░░░░░░ │
  │ Integration  │    18 │  24.0 % │ ████████░░░░░░░░░░░░░░░░░░░░░░ │
  │ E2E          │     6 │   8.0 % │ ███░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
  │ Ambiguous    │     3 │   4.0 % │ █░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
  ╰──────────────┴───────┴─────────┴────────────────────────────────╯

  Anti-Pattern Check
  ╭─────────────────────────┬────────┬─────────────────────────────╮
  │ Pattern                 │ Status │ Details                     │
  ├─────────────────────────┼────────┼─────────────────────────────┤
  │ Ice Cream Cone          │ ✓ OK   │ …                           │
  │ Hourglass               │ ✓ OK   │ …                           │
  ╰─────────────────────────┴────────┴─────────────────────────────╯

  Recommendations
   1. Test pyramid looks healthy! Unit: 64.0%, Integration: 24.0%, E2E: 8.0%.

  CI Pipeline — Github Actions
  ╭──────────────────────┬──────────────────────────┬─────────────╮
  │ Step                 │ Command                  │ Hint        │
  ├──────────────────────┼──────────────────────────┼─────────────┤
  │ Run unit tests       │ python -m pytest tests/  │ unit        │
  │ Run integration tests│ pytest -m integration    │ integration │
  │ Run E2E tests        │ pytest tests/e2e/ -m e2e │ e2e         │
  ╰──────────────────────┴──────────────────────────┴─────────────╯
```

### JSON

```json
{
  "repo_path": "/home/user/my-service",
  "timestamp": "2024-01-15T10:23:45+00:00",
  "total_test_files": 75,
  "distribution": {"unit": 0.64, "integration": 0.24, "e2e": 0.08},
  "counts": {"unit": 48, "integration": 18, "e2e": 6, "ambiguous": 3},
  "anti_patterns": [
    {"name": "Ice Cream Cone", "detected": false, "severity": "warning"}
  ],
  "recommendations": ["Test pyramid looks healthy! ..."],
  "test_files": [
    {
      "path": "tests/unit/test_user_service.py",
      "language": "python",
      "classification": "unit",
      "confidence": 0.8750,
      "scores": {"unit": 7.0, "integration": 1.0, "e2e": 0.0},
      "signals": [
        {"type": "unit", "source": "path_pattern", "name": "/unit/", "weight": 3.0},
        {"type": "unit", "source": "framework",    "name": "unittest", "weight": 2.5},
        {"type": "unit", "source": "code_pattern", "name": "mock / patch / stub", "weight": 1.5}
      ]
    }
  ],
  "ci_pipeline": {
    "tool": "github_actions",
    "steps": [
      {"name": "Run unit tests", "command": "pytest tests/unit/", "test_type_hint": "unit"}
    ]
  }
}
```

---

## Changelog

### v3.0

- **Explain Mode** (`--debug`): full per-file signal breakdown showing source, matched text, weight, and score bars — plus ambiguity warnings when types are too close
- **PR Comment** (`pr_commenter.py`): GitHub Action posts a structured markdown comment on every pull request with distribution table, anti-patterns, and recommendations; idempotent — updates the existing comment on re-runs instead of duplicating it
- **GitHub Action** (`action.yml` + `Dockerfile` + `entrypoint.sh`): run the full analysis directly in any GitHub workflow with quality-gate inputs (`min-unit-percentage`, `max-e2e-percentage`, `fail-on-anti-patterns`) and structured outputs
- **Release automation** (`.github/workflows/release.yml`): push a semver tag to auto-create a GitHub Release and update the floating `v1` tag

### v2.0

- **9 new language plugins**: Go, Ruby, C# (.NET), Rust, Kotlin, PHP, C/C++, Groovy, Scala
- **100+ frameworks** added to `default_rules.yaml` across all supported languages
- **6 additional CI platforms**: GitLab CI, CircleCI, Azure Pipelines, Travis CI, Bitbucket Pipelines, Jenkins
- **50+ CI command patterns** now recognized (`cargo test`, `rspec`, `phpunit`, `behat`, `dotnet test`, `sbt test`, `ctest`, …)
- **Tightened code patterns** to reduce false positives across language boundaries
- **Auto-detect all CI files** when `--ci` flag is omitted

### v1.0

- Initial release: Python, Java, JavaScript/TypeScript
- GitHub Actions CI parsing
- Console, JSON, HTML output
- Anti-pattern detection (Ice Cream Cone, Hourglass, Testing Trophy)

---

## License

MIT
