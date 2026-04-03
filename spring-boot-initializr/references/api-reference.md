# Spring Initializr API Reference

## Base URL

https://start.spring.io

## Endpoints

### Get Metadata

GET /
Accept: application/vnd.initializr.v2.2+json

Returns complete metadata including available versions, dependencies, and defaults.

### Generate Project ZIP

GET /starter.zip

Query parameters:

| Parameter    | Description                  | Example            |
|--------------|------------------------------|--------------------|
| type         | Build type                   | maven-project      |
| groupId      | Organization identifier      | com.example        |
| artifactId   | Project name                 | demo               |
| version      | Project version              | 0.0.1-SNAPSHOT     |
| name         | Display name                 | Demo               |
| description  | Project description          | Demo project       |
| packageName  | Java package                 | com.example.demo   |
| packaging    | Packaging type               | jar                |
| javaVersion  | Java version                 | 17                 |
| language     | Language                     | java               |
| bootVersion  | Spring Boot version          | 4.0.5              |
| dependencies | Comma-separated dependencies | web,data-jpa,mysql |

## Available Spring Boot Versions

| Version        | Type        | Java Requirement |
|----------------|-------------|------------------|
| 4.1.0-SNAPSHOT | Snapshot    | 17+              |
| 4.1.0-M4       | Milestone   | 17+              |
| 4.0.5          | Stable      | 17+              |
| 3.5.13         | Maintenance | 17+              |

Note: Always fetch current metadata for the latest list.

## Response Examples

### Successful Generation

HTTP 200 with application/zip content type. Returns a ZIP file containing the complete Spring Boot project.

### Error Response

HTTP 400 with JSON body:
{
"message": "Invalid dependency: invalid-dependency",
"errors": [...]
}