# Spring Boot Initializr Skill

Spring Boot project generator for Codex and AI agents, using the official Spring Initializr API

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://www.python.org/)
[![Spring Boot](https://img.shields.io/badge/Spring%20Boot-3.x-brightgreen)](https://spring.io/projects/spring-boot)

**Generate production-ready Spring Boot projects directly from your AI agent**

</div>

---

## Features

- Generate Spring Boot projects with specific dependencies
- Real-time fetching of latest versions and dependencies
- Automatic validation of dependencies, Java version, and Spring Boot version
- Support for Maven, Gradle (Groovy/Kotlin DSL)
- Automatic project extraction and cleanup
- Graceful error handling with helpful suggestions

## Prerequisites

- **Internet connection**: Required to fetch metadata and generate projects from start.spring.io
- **Python 3.8+**: The script is written in Python
- **Dependencies**: Install required Python packages  (see Installation below)

## Installation

```bash
# Install dependencies
pip install -r scripts/requirements.txt
```

## Usage

### Generate a Project

```bash
python scripts/spring-initializr.py generate \
  --groupId com.example \
  --artifactId my-app \
  --dependencies web,data-jpa,mysql
```

The script will:

- Fetch the latest metadata
- Validate all parameters
- Generate the project
- If the target directory doesn't exist or is empty: extract it to `./my-app/` and clean up the ZIP file
- If the target directory exists and is not empty: keep the ZIP file and provide manual extraction instructions

### Explore Available Options

```bash
# List available Spring Boot versions
python scripts/spring-initializr.py --list-versions

# List all dependencies
python scripts/spring-initializr.py --list-deps

# Search for specific dependencies
python scripts/spring-initializr.py --search-deps mysql

# Validate dependencies
python scripts/spring-initializr.py --validate-deps web,data-jpa,mysql
```

### Common Dependencies

| Request       | Dependency ID   |
|---------------|-----------------|
| REST API, Web | `web`           |
| Reactive Web  | `webflux`       |
| JPA, Database | `data-jpa`      |
| MySQL         | `mysql`         |
| PostgreSQL    | `postgresql`    |
| Security      | `security`      |
| OAuth2        | `oauth2-client` |
| Actuator      | `actuator`      |
| Lombok        | `lombok`        |
| DevTools      | `devtools`      |

## Project Structure

```
spring-boot-initializr-skill/
├── spring-boot-initializr/
│   ├── SKILL.md              # Skill metadata and instructions
│   ├── scripts/
│   │   ├── spring-initializr.py  # Main script
│   │   └── requirements.txt      # Python dependencies
│   └── references/
│       └── api-reference.md      # API documentation
├── LICENSE
└── README.md
```

## Error Handling

The script provides helpful error messages for:

- Invalid dependencies (with suggestions)
- Unsupported Java versions
- Unavailable Spring Boot versions
- Network connectivity issues

## License

MIT License