---
name: spring-boot-initializr
version: 1.0.0
description: Generates Spring Boot projects using the official Spring Initializr API. Fetches live versions and dependencies from start.spring.io. Use when user wants to create a new Spring Boot project with specific dependencies.
author: DevCodeLog
license: MIT
metadata:
  allowed-tools: read, write, bash, http_request
---

# Spring Boot Project Generator

## Overview

This skill generates Spring Boot project skeletons using the official Spring Initializr API. Always fetches the latest
available Spring Boot versions and dependencies in real-time from start.spring.io.

**Important:** The `generate` command automatically fetches live metadata and validates all parameters. Separate
metadata fetching is only needed when users ask exploratory questions (e.g., "what versions are available?").

The skill parses the Spring Initializr metadata API response, which provides:

- Available Spring Boot versions (including SNAPSHOT and milestone releases)
- Complete dependency hierarchy with categories and descriptions
- Supported Java versions (17, 21, 25, 26)
- Supported languages (Java, Kotlin, Groovy)
- Build types (Maven, Gradle with Groovy/Kotlin DSL)
- Packaging options (Jar, War)

## When to Use

Activate when user:

- Asks to "create/generate a Spring Boot project"
- Mentions "start.spring.io" or "Spring Initializr"
- Needs a Spring Boot scaffold with specific dependencies (Web, JPA, Security, MySQL, etc.)
- Provides groupId/artifactId and wants a downloadable project
- Asks about available Spring Boot versions or dependencies

Do NOT activate for:

- General Java questions
- Non-Spring projects
- Existing Spring Boot project troubleshooting

## Core Workflow

### Step 1: Collect Project Configuration

Gather required information through conversation. Use metadata defaults where applicable:

| Field        | Required | API Default                             | Example                     |
|--------------|----------|-----------------------------------------|-----------------------------|
| type         | No       | gradle-project                          | maven-project               |
| groupId      | Yes      | com.example                             | com.mycompany               |
| artifactId   | Yes      | demo                                    | user-service                |
| version      | No       | 0.0.1-SNAPSHOT                          | 1.0.0                       |
| name         | No       | artifactId value                        | User Service API            |
| description  | No       | empty                                   | REST API for user management |
| packageName  | No       | {groupId}.{artifactId}                  | com.mycompany.userservice   |
| packaging    | No       | jar                                     | jar                         |
| javaVersion  | No       | 17                                      | 21                          |
| language     | No       | java                                    | kotlin                      |
| bootVersion  | No       | **Latest stable version**(fetched live) | 4.0.5                       |
| dependencies | No       | empty                                   | web,data-jpa,mysql          |

### Step 2: (Optional) Explore Available Options

Only use this step when the user explicitly asks about available versions or dependencies (e.g., "what Spring Boot
versions exist?"). Do NOT run these before every project generation.

List available Spring Boot versions:

```bash
python scripts/spring-initializr.py --list-versions
```

List all dependencies by category:

```bash
python scripts/spring-initializr.py --list-deps
```

Search for specific dependencies:

```bash
python scripts/spring-initializr.py --search-deps mysql
```

Check if a specific version is available:

```bash
python scripts/spring-initializr.py --check-version 4.0.5
```

Validate dependencies before generation (optional early check):

```bash
python scripts/spring-initializr.py --validate-deps web,data-jpa,mysql
```

### Step 3: Map Natural Language to Dependencies

Based on API metadata categories, map user requests to dependency IDs:

| Category         | User Says                       | Dependency ID          |
|------------------|---------------------------------|------------------------|
| Web              | REST API, web service, MVC      | web                    |
| Web              | reactive, non-blocking, WebFlux | webflux                |
| Web              | GraphQL                         | graphql                |
| Template Engines | Thymeleaf, HTML template        | thymeleaf              |
| Security         | security, login, authentication | security               |
| Security         | OAuth2, OAuth client            | oauth2-client          |
| Security         | JWT, resource server            | oauth2-resource-server |
| SQL              | JPA, Hibernate, ORM, database   | data-jpa               |
| SQL              | MySQL                           | mysql                  |
| SQL              | PostgreSQL, Postgres            | postgresql             |
| SQL              | H2, in-memory database          | h2                     |
| NoSQL            | Redis, cache                    | data-redis             |
| NoSQL            | MongoDB                         | data-mongodb           |
| Messaging        | RabbitMQ, AMQP                  | amqp                   |
| Messaging        | Kafka                           | kafka                  |
| I/O              | batch processing, Batch         | batch                  |
| Ops              | monitoring, Actuator            | actuator               |
| Testing          | testing, unit test              | test                   |
| Developer Tools  | hot reload, DevTools            | devtools               |
| Developer Tools  | Lombok                          | lombok                 |
| Spring Cloud     | config client                   | cloud-config-client    |
| Spring Cloud     | service discovery, Eureka       | cloud-eureka           |
| Spring Cloud     | gateway                         | cloud-gateway          |

### Step 4: Generate Project

Use the Python script to generate the project. The script automatically:

- Fetches live metadata (no need to pre-fetch)
- Validates dependencies, Java version, and Spring Boot version
- Calls the API and downloads the ZIP file
- **If the target directory `{artifactId}` does not exist or is empty**:
    - Extracts the project into a subdirectory named `{artifactId}` (e.g., `./demo/`)
    - Deletes the ZIP file – only the extracted folder remains
- **If the target directory `{artifactId}` already exists and is not empty**:
    - Skips auto-extraction to avoid overwriting
    - Keeps the ZIP file for manual extraction
    - Provides instructions for manual extraction

```bash
python scripts/spring-initializr.py generate \
  --type maven-project \
  --groupId com.example \
  --artifactId demo \
  --version 0.0.1-SNAPSHOT \
  --name Demo \
  --description "Demo project" \
  --packageName com.example.demo \
  --packaging jar \
  --javaVersion 17 \
  --language java \
  --bootVersion 4.0.5 \
  --dependencies web,data-jpa,mysql
```

The script calls the Spring Initializr API endpoint: `GET https://start.spring.io/starter.zip`

### Step 5: Provide Output to User

After successful generation, respond based on the result:

**If project was auto-extracted:**

**✅ Project generated and extracted:** `{artifactId}`

**Next steps:**

**Enter project directory:**

```bash
cd {artifactId}
```

Database configuration (if JPA included):
Edit `src/main/resources/application.properties`:

```properties
spring.datasource.url=jdbc:mysql://localhost:3306/demo
spring.datasource.username=root
spring.datasource.password=yourpassword
spring.jpa.hibernate.ddl-auto=update
```

**If auto-extraction was skipped (directory already exists):**

**✅ Project generated:** `{artifactId}.zip`

**⚠️ Directory `{artifactId}` already exists and is not empty. Auto-extraction skipped.**

**Next steps:**

**Option 1: Manually extract to a different directory:**

```bash
unzip {artifactId}.zip -d {artifactId}-new
cd {artifactId}-new
```

**Option 2: Remove/rename existing directory and rerun:**

```bash
# Remove existing directory
rm -rf {artifactId}
# Or rename it
mv {artifactId} {artifactId}-backup
# Then rerun the generate command
```

**Import to IDE:**

- IntelliJ: File -> Open -> select pom.xml
- VS Code: Install "Extension Pack for Java"

## Script Commands Reference

spring-initializr.py commands:

| Command                    | Purpose                                     |
|----------------------------|---------------------------------------------|
| --fetch-metadata           | Fetch and display full metadata             |
| --list-versions            | List all available Spring Boot versions     |
| --list-deps                | List all available dependencies by category |
| --list-deps --category Web | List dependencies in specific category      |
| --search-deps keyword      | Search dependencies by keyword              |
| --validate-deps ids        | Validate comma-separated dependency IDs     |
| --check-version version    | Check if version is available               |
| generate                   | Generate project ZIP file                   |

## Error Handling

### API Unreachable

⚠️ Cannot reach start.spring.io

Possible reasons:

- Network connection issue
- Service temporary unavailable

Fallback options:

1. Check network and retry
2. Use cached metadata from last successful request
3. Generate basic project with default configuration

### Invalid Dependencies

❌ Invalid dependencies: 'xyz'

Did you mean one of these?

- web (Spring Web MVC)
- webflux (Reactive Web)
- websocket (WebSocket support)

### Version Not Found

⚠️ Version 3.5.14 not available

Available versions:

- 4.1.0-SNAPSHOT (latest snapshot)
- 4.1.0-M4 (milestone)
- 4.0.5 (latest stable, recommended)
- 3.5.13

### Missing Required Fields

📋 Missing required information

Please provide:

- groupId: (e.g., com.example)
- artifactId: (e.g., my-app)

## Example Conversations

### Example 1: Complete Request

User: "Create a Spring Boot project with group com.mycompany, artifact user-api, use web, jpa, and postgresql"

Action:

1. Validate dependencies if needed (optional)
2. Run: python scripts/spring-initializr.py generate --groupId com.mycompany --artifactId user-api --dependencies
   web,data-jpa,postgresql
3. Return ZIP with next steps

### Example 2: Partial Request

User: "Generate a Spring Boot REST API"

Action:
I'll create a REST API project for you.

Please provide:

1. groupId: (e.g., com.example)
2. artifactId: (project name)

Or reply "use defaults" for com.example/demo.

### Example 3: Query Available Versions

User: "What Spring Boot versions are available?"

Action:
python scripts/spring-initializr.py --list-versions

## Installation

For Codex:
cp -r spring-boot-initializr ~/.agents/skills/

For Claude Code / Cursor / Copilot:
Follow your agent's skill installation instructions.

Dependencies:
pip install -r scripts/requirements.txt

## Important Notes

1. No redundant API calls - The generate command automatically fetches live metadata. Only use --fetch-metadata or
   --list-versions when the user explicitly asks about available options.

2. Validate dependencies when helpful - Use --validate-deps before generation only if you want to catch errors early,
   but it's not required.

3. Handle errors gracefully - Provide clear error messages with suggestions.

4. Cache metadata optionally - Reduce API calls but respect TTL (1 hour).

5. Spring Boot 4.x requires Java 17+.

6. Package naming convention - Lowercase, no hyphens, dots as separators.

## License

MIT License