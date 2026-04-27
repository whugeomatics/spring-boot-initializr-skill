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

| Parameter    | Description                                          | Example                           |
|--------------|------------------------------------------------------|-----------------------------------|
| type         | Build type                                           | gradle-project                    |
| groupId      | Organization identifier                              | com.example                       |
| artifactId   | Project name                                         | demo                              |
| version      | Project version                                      | 0.0.1-SNAPSHOT                    |
| name         | Display name                                         | Demo                              |
| description  | Project description                                  | Demo project for com.example:demo |
| packageName  | Java package (**lowercase, no hyphens/underscores**) | com.example.demo                  |
| packaging    | Packaging type                                       | jar                               |
| javaVersion  | Java version                                         | 17                                |
| language     | Language                                             | java                              |
| bootVersion  | Spring Boot version                                  | metadata default                  |
| dependencies | Comma-separated dependencies                         | web,data-jpa,mysql                |

> `packageName` should use lowercase letters, digits, and dots only. Hyphens and underscores are stripped from the
> derived package name. If the artifactId contains hyphens (e.g., `user-service`), strip them for packageName:
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
| bootVersion | default from live metadata              |

## Available Spring Boot Versions

Always call `GET /` or run `--list-versions` to retrieve the current list. Do not rely on static version examples,
because Spring Boot releases and milestone availability change frequently.

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
- Dependency is incompatible with the selected Spring Boot version — choose a compatible Boot version or omit
  `--bootVersion`
- Invalid Spring Boot version — use `--list-versions` to see available options
- Invalid Java version — check supported versions via live metadata
- `packageName` contains illegal characters (e.g., hyphens or underscores)
