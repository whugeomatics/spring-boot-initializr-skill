# Spring Initializr API Reference

## Base URL

```
https://start.spring.io
```

## Endpoints

### Get Metadata

```
GET /
Accept: application/vnd.initializr.v2.2+json
```

Returns complete metadata including available versions, dependencies, and defaults. **Always fetch this live** — do not
hardcode versions or dependency lists, as they change with each release.

### Generate Project ZIP

```
GET /starter.zip
```

Query parameters:

| Parameter    | Description                   | Example                           |
|--------------|-------------------------------|-----------------------------------|
| type         | Build type                    | gradle-project                    |
| groupId      | Organization identifier       | com.example                       |
| artifactId   | Project name                  | demo                              |
| version      | Project version               | 0.0.1-SNAPSHOT                    |
| name         | Display name                  | Demo                              |
| description  | Project description           | Demo project for com.example:demo |
| packageName  | Java package (**no hyphens**) | com.example.demo                  |
| packaging    | Packaging type                | jar                               |
| javaVersion  | Java version                  | 17                                |
| language     | Language                      | java                              |
| bootVersion  | Spring Boot version           | 4.0.5                             |
| dependencies | Comma-separated dependencies  | web,data-jpa,mysql                |

> ⚠️ `packageName` must be a valid Java identifier: lowercase letters, digits, and dots only. Hyphens are **not**
> allowed. If the artifactId contains hyphens (e.g., `user-service`), strip them for packageName:
> `com.example.userservice`.

## API Defaults

These are the defaults returned by the metadata endpoint as of the last review. **Always use live metadata** — these
values may change between releases.

| Parameter   | Default value                           |
|-------------|-----------------------------------------|
| type        | gradle-project                          |
| groupId     | com.example                             |
| artifactId  | demo                                    |
| version     | 0.0.1-SNAPSHOT                          |
| description | Demo project for {groupId}:{artifactId} |
| packaging   | jar                                     |
| javaVersion | 17                                      |
| language    | java                                    |
| bootVersion | latest stable (from metadata)           |

## Available Spring Boot Versions

> ⚠️ This table is a point-in-time snapshot. Always call `GET /` to retrieve the current list.

| Version        | Type        | Java Requirement |
|----------------|-------------|------------------|
| 4.1.0-SNAPSHOT | Snapshot    | 17+              |
| 4.1.0-M4       | Milestone   | 17+              |
| 4.0.5          | Stable ✅    | 17+              |
| 3.5.13         | Maintenance | 17+              |

## Response

### Successful Generation

`HTTP 200` with `Content-Type: application/zip`. Returns a ZIP file containing the complete Spring Boot project.

### Error Response

`HTTP 400` with JSON body:

```json
{
  "message": "Invalid dependency: invalid-dependency",
  "errors": [
    ...
  ]
}
```

Common causes:

- Unknown dependency ID — use `--search-deps` or `--list-deps` to find correct IDs
- Invalid Spring Boot version — use `--list-versions` to see available options
- Invalid Java version — check supported versions via live metadata
- `packageName` contains illegal characters (e.g., hyphens)
