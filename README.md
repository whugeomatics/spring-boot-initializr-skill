# Spring Boot Initializr Skill

Spring Boot project generator for AI agents — powered by the official Spring Initializr API (start.spring.io)

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://www.python.org/)
[![Spring Boot](https://img.shields.io/badge/Spring%20Boot-4.x-brightgreen)](https://spring.io/projects/spring-boot)
[![Cursor](https://img.shields.io/badge/Cursor-rule%20included-blue)](https://cursor.sh)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-skill%20included-blueviolet)](https://claude.ai/code)

**Generate production-ready Spring Boot projects directly from your AI agent**

</div>

---

## Features

- 🚀 Generate Spring Boot projects with any combination of Spring starters
- 🔄 Real-time metadata — always fetches the latest versions and dependencies from start.spring.io
- ✅ Validates dependency IDs, compatibility ranges, Java version, Spring Boot version, and package name before calling
  the API
- 🛠️ Supports Maven, Gradle Groovy DSL, and Gradle Kotlin DSL
- 📦 Auto-extracts the generated ZIP; skips extraction safely if directory already exists
- 💡 Smart suggestions for mistyped dependency IDs
- 🗂️ 1-hour local metadata cache to reduce API round-trips (bypass with `--force`)
- 🖥️ Works with **Codex**, **Claude Code**, **Cursor**, and other AI agents

---

## Prerequisites

| Requirement | Details                           |
|-------------|-----------------------------------|
| Python      | 3.8 or newer                      |
| Internet    | Required to reach start.spring.io |
| pip package | `requests >= 2.31.0`              |

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-org/spring-boot-initializr-skill.git
cd spring-boot-initializr-skill

# 2. Install the Python dependency
pip install -r spring-boot-initializr/scripts/requirements.txt
```

---

## Agent Setup

### Codex

```bash
cp -r spring-boot-initializr ~/.agents/skills/spring-boot-initializr
```

### Claude Code

```bash
cp -r spring-boot-initializr ~/.claude/skills/spring-boot-initializr
```

### Cursor

Copy the bundled Cursor rule into your project:

```bash
mkdir -p <your-project>/.cursor/rules
cp .cursor/rules/spring-boot-initializr.mdc <your-project>/.cursor/rules/
```

Cursor will automatically activate the rule when you open Java, Kotlin, or Gradle/Maven files and ask to
create a Spring Boot project.

### Copilot / Other Agents

Point your agent at `spring-boot-initializr/SKILL.md` as the instruction source, then invoke the script
directly from the terminal.

---

## Usage

### Generate a Project

```bash
# Minimal — live metadata defaults with script fallbacks (Gradle, Java 17, metadata default Boot)
python spring-boot-initializr/scripts/spring-initializr.py generate \
  --groupId com.example \
  --artifactId my-app \
  --dependencies web,data-jpa,mysql

# Maven project targeting Java 21
python spring-boot-initializr/scripts/spring-initializr.py generate \
  --type maven-project \
  --groupId com.example \
  --artifactId my-app \
  --javaVersion 21 \
  --dependencies web,security,data-jpa,postgresql,lombok

# Write to a specific directory
python spring-boot-initializr/scripts/spring-initializr.py generate \
  --groupId com.example --artifactId my-app \
  --output-dir ~/projects
```

The script will:

1. Fetch metadata (from 1-hour cache or live from API)
2. Validate parameters against live metadata, including dependency compatibility ranges
3. Call `GET https://start.spring.io/starter.zip`
4. Extract the project to `{output-dir}/{artifactId}/` (or keep the ZIP if the directory is not empty)

### Explore Available Options

```bash
# List Spring Boot versions
python spring-boot-initializr/scripts/spring-initializr.py --list-versions

# List all dependencies (with descriptions)
python spring-boot-initializr/scripts/spring-initializr.py --list-deps

# Filter by category
python spring-boot-initializr/scripts/spring-initializr.py --list-deps --category web

# Search by keyword
python spring-boot-initializr/scripts/spring-initializr.py --search-deps redis

# Validate before generating
python spring-boot-initializr/scripts/spring-initializr.py --validate-deps web,data-jpa,mysql

# Force-refresh the local metadata cache
python spring-boot-initializr/scripts/spring-initializr.py --list-versions --force
```

### Common Dependencies

| Request         | Dependency ID    |
|-----------------|------------------|
| REST API, Web   | `web`            |
| Reactive Web    | `webflux`        |
| JPA / Hibernate | `data-jpa`       |
| MySQL           | `mysql`          |
| PostgreSQL      | `postgresql`     |
| Redis           | `data-redis`     |
| MongoDB         | `data-mongodb`   |
| Security        | `security`       |
| OAuth2          | `oauth2-client`  |
| Kafka           | `kafka`          |
| RabbitMQ        | `amqp`           |
| Actuator        | `actuator`       |
| Lombok          | `lombok`         |
| DevTools        | `devtools`       |
| Testcontainers  | `testcontainers` |

---

## Project Structure

```
spring-boot-initializr-skill/
├── spring-boot-initializr/          # Core skill (Codex / Claude Code)
│   ├── SKILL.md                     # Agent instructions
│   ├── scripts/
│   │   ├── spring-initializr.py     # Main CLI script
│   │   └── requirements.txt         # Python dependencies
│   └── references/
│       └── api-reference.md         # Spring Initializr API reference
├── .cursor/
│   └── rules/
│       └── spring-boot-initializr.mdc   # Cursor agent rule
├── LICENSE
└── README.md
```

---

## Error Handling

| Error                         | Cause                                             | Fix                                                  |
|-------------------------------|---------------------------------------------------|------------------------------------------------------|
| `Invalid dependencies: xyz`   | Unknown dependency ID                             | Run `--search-deps xyz` for suggestions              |
| `Incompatible dependencies`   | Dependency does not support selected Boot version | Use `--list-versions` or omit `--bootVersion`        |
| `Java X not supported`        | Java version not in metadata                      | Run `--list-versions`                                |
| `Version X.Y.Z not available` | Boot version not in metadata                      | Run `--list-versions`                                |
| `Failed to fetch metadata`    | Network issue                                     | Check connectivity; cached data used if < 1 hour old |
| `Directory already exists`    | Extract target not empty                          | Rename or use `--output-dir`                         |

---

## Changelog

| Version   | Summary                                                                                                                                                                                                                                                                                            |
|-----------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **1.3.0** | Read defaults from live metadata when available; validate dependency compatibility ranges and package names; add safe ZIP extraction; use ASCII CLI status output; clarify script path resolution and Spring Cloud BOM guidance                                                                    |
| **1.2.0** | Fixed retry backoff consistency; fixed `suggest_alternatives` case sensitivity and fuzzy-match false positives; fixed `HTTPError` handling (`e.response` vs bare `response`); removed non-standard `-dep` alias; added `--output-dir`; added Cursor rule; added Claude plugin marketplace manifest |
| 1.1.0     | Fixed `packageName` hyphen/underscore stripping; removed hardcoded Java versions; added `websocket` to mapping; Spring Cloud BOM warning; corrected `description` default                                                                                                                          |
| 1.0.0     | Initial release                                                                                                                                                                                                                                                                                    |

---

## License

MIT License
