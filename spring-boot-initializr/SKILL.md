---
name: spring-boot-initializr
description: Generates Spring Boot projects using the official Spring Initializr API. Fetches live versions and dependencies from start.spring.io. Use when user wants to create a new Spring Boot project with specific dependencies.
license: MIT
compatibility: Requires python3.8+ and internet access
metadata:
  version: 1.3.0
allowed-tools: Python Read Write Bash Http
---

# Spring Boot Project Generator

## Overview

This skill generates Spring Boot project skeletons using the official Spring Initializr API. Always fetches the latest
available Spring Boot versions and dependencies from start.spring.io.

**Important:** The `generate` command automatically fetches live metadata and validates project parameters. Separate
metadata fetching is only needed when users ask exploratory questions (e.g., "what versions are available?").

The skill parses the Spring Initializr metadata API response, which provides:

- Available Spring Boot versions (including SNAPSHOT and milestone releases)
- Complete dependency hierarchy with categories and descriptions
- Supported Java versions (**fetched live from API** — do NOT hardcode; typically 17, 21, 24+)
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

Gather required information through conversation. groupId and artifactId are strongly recommended — ask for them if
not provided, or offer to use defaults. Other fields fall back to live metadata defaults when the API exposes them,
with conservative script fallbacks only when metadata does not provide a default.

| Field        | Recommended | Default                                                       | Example                      |
|--------------|-------------|---------------------------------------------------------------|------------------------------|
| type         | No          | gradle-project                                                | maven-project                |
| groupId      | **Yes**     | com.example                                                   | com.mycompany                |
| artifactId   | **Yes**     | demo                                                          | user-service                 |
| version      | No          | 0.0.1-SNAPSHOT                                                | 1.0.0                        |
| name         | No          | artifactId value                                              | User Service API             |
| description  | No          | "Spring Boot application"                                     | REST API for user management |
| packageName  | No          | {groupId}.{artifactId} (**hyphens AND underscores stripped**) | com.mycompany.userservice    |
| packaging    | No          | jar                                                           | jar                          |
| javaVersion  | No          | 17                                                            | 21                           |
| language     | No          | java                                                          | kotlin                       |
| bootVersion  | No          | Metadata default (fetched live)                               | omit unless a version is required |
| dependencies | No          | empty                                                         | web,data-jpa,mysql           |

> ⚠️ **packageName rule**: Java package names must be lowercase with no hyphens or underscores.
> If artifactId is `user-service` or `user_service`, packageName must be `com.example.userservice`
> (both `-` and `_` removed). The script derives this automatically if `--packageName` is omitted.

### Step 2: (Optional) Explore Available Options

Only use this step when the user explicitly asks about available versions or dependencies. Do NOT run these before
every project generation.

Resolve `scripts/spring-initializr.py` relative to this `SKILL.md` file. If the skill is installed at
`~/.agents/skills/spring-boot-initializr`, run commands from that directory or use the absolute script path.

List available Spring Boot versions:

```bash
python scripts/spring-initializr.py --list-versions
```

List all dependencies by category:

```bash
python scripts/spring-initializr.py --list-deps
```

List dependencies in a specific category:

```bash
python scripts/spring-initializr.py --list-deps --category web
```

Search for specific dependencies:

```bash
python scripts/spring-initializr.py --search-deps mysql
```

Check if a specific version is available:

```bash
python scripts/spring-initializr.py --check-version <version>
```

Validate dependencies before generation (optional early check):

```bash
python scripts/spring-initializr.py --validate-deps web,data-jpa,mysql
```

Force-refresh the local metadata cache:

```bash
python scripts/spring-initializr.py --list-versions --force
```

### Step 3: Map Natural Language to Dependencies

Based on API metadata categories, map user requests to dependency IDs:

| Category         | User Says                             | Dependency ID          |
|------------------|---------------------------------------|------------------------|
| Web              | REST API, web service, MVC            | web                    |
| Web              | reactive, non-blocking, WebFlux       | webflux                |
| Web              | GraphQL                               | graphql                |
| Web              | WebSocket                             | websocket              |
| Template Engines | Thymeleaf, HTML template              | thymeleaf              |
| Security         | security, login, authentication       | security               |
| Security         | OAuth2, OAuth client                  | oauth2-client          |
| Security         | JWT, resource server                  | oauth2-resource-server |
| SQL              | JPA, Hibernate, ORM, database         | data-jpa               |
| SQL              | MySQL                                 | mysql                  |
| SQL              | PostgreSQL, Postgres                  | postgresql             |
| SQL              | H2, in-memory database                | h2                     |
| NoSQL            | Redis, cache                          | data-redis             |
| NoSQL            | MongoDB                               | data-mongodb           |
| Messaging        | RabbitMQ, AMQP                        | amqp                   |
| Messaging        | Kafka                                 | kafka                  |
| I/O              | batch processing, Batch               | batch                  |
| Ops              | monitoring, Actuator                  | actuator               |
| Testing          | Testcontainers, integration tests     | testcontainers         |
| Developer Tools  | hot reload, DevTools                  | devtools               |
| Developer Tools  | Lombok                                | lombok                 |
| Spring Cloud     | config client ⚠️ see note below       | cloud-config-client    |
| Spring Cloud     | service discovery, Eureka ⚠️          | cloud-eureka           |
| Spring Cloud     | API gateway ⚠️                        | cloud-gateway          |

> ⚠️ **Spring Cloud note**: Spring Initializr normally adds the compatible Spring Cloud BOM for selected Cloud
> dependencies. Re-check https://spring.io/projects/spring-cloud#overview if you manually change Spring Boot or
> Spring Cloud versions after generation.

> ℹ️ `spring-boot-starter-test` is automatically included in all generated projects — no need to add it manually.

### Step 4: Generate Project

Use the Python script to generate the project. The script automatically:

- Reads from a 1-hour local metadata cache (or fetches live if expired / `--force`)
- Validates dependency IDs, dependency compatibility ranges, Java version, Spring Boot version, and package name
- Calls the API and downloads the ZIP file
- **If the target directory `{artifactId}` does not exist or is empty**:
    - Extracts the project into a subdirectory named `{artifactId}`
    - Deletes the ZIP file — only the extracted folder remains
- **If the target directory `{artifactId}` already exists and is not empty**:
    - Skips auto-extraction to avoid overwriting
    - Keeps the ZIP file and prints manual extraction instructions

Minimal invocation (uses live metadata defaults; script fallbacks are Gradle, Java 17, latest metadata default Boot):

```bash
python scripts/spring-initializr.py generate \
  --groupId com.example \
  --artifactId demo \
  --dependencies web,data-jpa,mysql
```

Full invocation with all options shown:

```bash
python scripts/spring-initializr.py generate \
  --type gradle-project \
  --groupId com.example \
  --artifactId demo \
  --version 0.0.1-SNAPSHOT \
  --name Demo \
  --description "Demo project" \
  --packageName com.example.demo \
  --packaging jar \
  --javaVersion 17 \
  --language java \
  --bootVersion <version> \
  --dependencies web,data-jpa,mysql
```

Write project to a specific directory:

```bash
python scripts/spring-initializr.py generate \
  --groupId com.example --artifactId demo \
  --output-dir /workspace/projects
```

The script calls: `GET https://start.spring.io/starter.zip`

### Step 5: Provide Output to User

After successful generation, respond based on the result:

**If project was auto-extracted:**

**✅ Project generated and extracted:** `{artifactId}/`

```bash
cd {artifactId}
```

Database configuration (if JPA + MySQL/PostgreSQL included):
Edit `src/main/resources/application.properties`:

```properties
spring.datasource.url=jdbc:mysql://localhost:3306/{artifactId}
spring.datasource.username=root
spring.datasource.password=yourpassword
spring.jpa.hibernate.ddl-auto=update
```

**If auto-extraction was skipped (directory already exists):**

**✅ Project ZIP saved:** `{artifactId}.zip`

**⚠️ Directory `{artifactId}` already exists — auto-extract skipped.**

```bash
# Option 1: extract to a new directory
unzip {artifactId}.zip -d {artifactId}-new && cd {artifactId}-new

# Option 2: rename existing, then rerun
mv {artifactId} {artifactId}-backup
```

**Import to IDE:**

- IntelliJ IDEA: File → Open → select `pom.xml` (Maven) or `build.gradle` (Gradle)
- VS Code: Install "Extension Pack for Java", then open the project folder

## Script Commands Reference

| Command                            | Purpose                                                  |
|------------------------------------|----------------------------------------------------------|
| `--fetch-metadata`                 | Fetch and print full metadata JSON                       |
| `--list-versions`                  | List all available Spring Boot versions                  |
| `--list-deps`                      | List all available dependencies by category              |
| `--list-deps --category <name>`    | List dependencies in a specific category                 |
| `--search-deps <keyword>`          | Search dependencies by keyword (searches id/name/desc)   |
| `--validate-deps <ids>`            | Validate comma-separated dependency IDs                  |
| `--check-version <version>`        | Check if a Spring Boot version is available              |
| `--force`                          | Bypass cache; force-fetch fresh metadata from API        |
| `generate [options]`               | Generate and extract the project                         |
| `generate ... --output-dir <dir>`  | Write project to a specific output directory             |

## Error Handling

### API Unreachable

⚠️ Cannot reach start.spring.io

Steps to resolve:
1. Check network connectivity and retry
2. If a valid cache exists (< 1 hour old), the script will use it automatically
3. If the cache is stale and the API is unreachable, use https://start.spring.io manually

### Invalid Dependencies

❌ Invalid dependencies: `xyz`

Run `--search-deps xyz` or `--list-deps` to find the correct ID. The script also prints suggestions:

```
❌ Invalid: xyz
   'xyz' → did you mean: web, webflux, websocket?
```

### Version Not Found

⚠️ Version X.Y.Z not available

Run `--list-versions` to see the current list. Do not rely on static version examples because Spring Boot versions
change frequently.

### Missing Required Fields

📋 Please provide:

- `--groupId` (e.g., `com.example`)
- `--artifactId` (e.g., `my-app`)

Or proceed with defaults by omitting both (uses `com.example` / `demo`).

## Example Conversations

### Example 1: Complete Request

User: "Create a Spring Boot project with group com.mycompany, artifact user-api, use web, jpa, and postgresql"

Action:
1. Map: jpa → `data-jpa`, postgresql → `postgresql`
2. Derive packageName: `com.mycompany.userapi` (hyphen in `user-api` stripped)
3. Run:
   ```bash
   python scripts/spring-initializr.py generate \
     --groupId com.mycompany --artifactId user-api \
     --packageName com.mycompany.userapi \
     --dependencies web,data-jpa,postgresql
   ```
4. Return extracted project with PostgreSQL config snippet

### Example 2: Partial Request

User: "Generate a Spring Boot REST API"

Action: Ask for missing recommended fields:

> I'll create a REST API project for you! Please provide:
> 1. **groupId** — your organization identifier (e.g., `com.example`)
> 2. **artifactId** — the project name (e.g., `my-api`)
>
> Or reply **"use defaults"** to proceed with `com.example` / `demo`.

### Example 3: Query Available Versions

User: "What Spring Boot versions are available?"

Action:
```bash
python scripts/spring-initializr.py --list-versions
```

### Example 4: Artifact with Hyphens / Underscores

User: "Create project with groupId com.acme, artifactId order_service, add web and kafka"

Action:
- artifactId: `order_service`
- packageName: `com.acme.orderservice` ← underscore removed
- Run:
  ```bash
  python scripts/spring-initializr.py generate \
    --groupId com.acme --artifactId order_service \
    --packageName com.acme.orderservice \
    --dependencies web,kafka
  ```

## Installation

### Codex

```bash
cp -r spring-boot-initializr ~/.agents/skills/
pip install -r spring-boot-initializr/scripts/requirements.txt
```

### Claude Code

```bash
# Copy skill to Claude Code skills directory
cp -r spring-boot-initializr ~/.claude/skills/
pip install -r spring-boot-initializr/scripts/requirements.txt
```

### Cursor

The skill ships a ready-to-use Cursor rule at `.cursor/rules/spring-boot-initializr.mdc`.
Copy that file into your project's `.cursor/rules/` directory:

```bash
cp .cursor/rules/spring-boot-initializr.mdc <your-project>/.cursor/rules/
pip install -r spring-boot-initializr/scripts/requirements.txt
```

Cursor will automatically activate the rule when you open Java/Kotlin/Gradle/Maven files.

### Copilot / Other Agents

Follow your agent's skill / instruction-file installation guide. Point the agent at
`spring-boot-initializr/SKILL.md` as the instruction source.

## Important Notes

1. **No redundant API calls** — The `generate` command fetches live metadata automatically. Only use `--fetch-metadata`
   or `--list-versions` when the user explicitly asks about available options.

2. **Metadata cache** — Metadata is cached locally for 1 hour at
   `~/.cache/spring-initializr-skill/metadata.json`. The cache is used automatically on subsequent
   calls. Use `--force` to bypass it and fetch fresh data from start.spring.io.

3. **Validate when helpful** — Use `--validate-deps` before generation to catch typos and compatibility issues early.

4. **Spring Boot 4.x requires Java 17+.**

5. **Package naming** — Lowercase, no hyphens, no underscores, dots as separators. The script
   derives the default packageName by stripping `-` and `_` from artifactId. Override with
   `--packageName` if you need a custom package structure.

6. **Spring Cloud BOM** — Spring Initializr normally adds the compatible Spring Cloud BOM for selected Cloud
   dependencies. Re-check the version matrix at https://spring.io/projects/spring-cloud#overview if you manually
   change Spring Boot or Spring Cloud versions after generation.

## License

MIT License
