#!/usr/bin/env python3
"""
Spring Boot Project Generator
Fetches metadata and generates projects via start.spring.io API
"""

import json
import sys
import time
import argparse
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

try:
    import requests
except ImportError:
    print("Missing dependency: requests", file=sys.stderr)
    print("Run: pip install requests", file=sys.stderr)
    sys.exit(1)

INITIALIZR_URL = "https://start.spring.io"
USER_AGENT = "spring-boot-initializr-skill/1.2"
METADATA_HEADERS = {
    "Accept": "application/vnd.initializr.v2.2+json",
    "User-Agent": USER_AGENT,
}

CACHE_DIR = Path.home() / ".cache" / "spring-initializr-skill"
CACHE_FILE = CACHE_DIR / "metadata.json"
CACHE_TTL_HOURS = 1


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

def get_cache_dir() -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR


def load_cached_metadata() -> Optional[Dict]:
    if not CACHE_FILE.exists():
        return None
    try:
        with open(CACHE_FILE, "r") as f:
            cached = json.load(f)
        cached_time = datetime.fromisoformat(cached.get("_cached_at", "2000-01-01"))
        if datetime.now() - cached_time > timedelta(hours=CACHE_TTL_HOURS):
            return None
        return cached.get("data")
    except (json.JSONDecodeError, KeyError, OSError):
        return None


def save_cached_metadata(data: Dict) -> None:
    get_cache_dir()
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump({"data": data, "_cached_at": datetime.now().isoformat()}, f)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Network
# ---------------------------------------------------------------------------

def fetch_metadata(force_refresh: bool = False, max_retries: int = 3) -> Optional[Dict]:
    """Fetch Spring Initializr metadata, using a 1-hour local cache unless force_refresh=True."""
    if not force_refresh:
        cached = load_cached_metadata()
        if cached:
            return cached

    for attempt in range(max_retries):
        try:
            response = requests.get(INITIALIZR_URL, headers=METADATA_HEADERS, timeout=15)
            response.raise_for_status()
            data = response.json()
            save_cached_metadata(data)
            return data
        except requests.exceptions.Timeout:
            wait = 2 ** attempt
            if attempt < max_retries - 1:
                print(f"Timeout, retrying in {wait}s… ({attempt + 1}/{max_retries})", file=sys.stderr)
                time.sleep(wait)
            else:
                print(f"Timeout after {max_retries} attempts.", file=sys.stderr)
        except requests.exceptions.RequestException as e:
            wait = 2 ** attempt  # FIX B1: consistent exponential backoff for all errors
            if attempt < max_retries - 1:
                print(f"Request failed ({e}), retrying in {wait}s… ({attempt + 1}/{max_retries})", file=sys.stderr)
                time.sleep(wait)
            else:
                print(f"Failed to fetch metadata: {e}", file=sys.stderr)
    return None


# ---------------------------------------------------------------------------
# Metadata helpers
# ---------------------------------------------------------------------------

def get_available_versions(metadata: Dict) -> List[Dict]:
    return metadata.get("bootVersion", {}).get("values", [])


def get_latest_version(metadata: Dict) -> str:
    return metadata.get("bootVersion", {}).get("default", "4.0.5")


def get_java_versions(metadata: Dict) -> List[str]:
    return [v["id"] for v in metadata.get("javaVersion", {}).get("values", []) if "id" in v]


def validate_java_version(metadata: Dict, java_version: str) -> Tuple[bool, Optional[str]]:
    versions = get_java_versions(metadata)
    if not versions or java_version in versions:
        return True, None
    return False, f"Java {java_version} not supported. Available: {', '.join(versions)}"


def get_dependencies(metadata: Dict) -> List[Dict]:
    return metadata.get("dependencies", {}).get("values", [])


def flatten_dependencies(metadata: Dict) -> List[Dict]:
    result = []
    for category in get_dependencies(metadata):
        for dep in category.get("values", []):
            dep["category"] = category.get("name", "Unknown")
            result.append(dep)
    return result


def search_dependencies(metadata: Dict, query: str) -> List[Dict]:
    q = query.lower()
    return [
        dep for dep in flatten_dependencies(metadata)
        if q in dep.get("name", "").lower()
        or q in dep.get("description", "").lower()
        or q in dep.get("id", "").lower()
    ][:20]


def validate_dependencies(metadata: Dict, dep_ids: List[str]) -> Tuple[List[str], List[str]]:
    valid_ids = {d["id"] for d in flatten_dependencies(metadata)}
    return [d for d in dep_ids if d in valid_ids], [d for d in dep_ids if d not in valid_ids]


def suggest_alternatives(metadata: Dict, invalid_dep: str) -> List[str]:
    # FIX B2: normalise to lowercase before dict lookup
    key = invalid_dep.lower()
    common_aliases: Dict[str, str] = {
        "jpa":              "data-jpa",
        "mysql-connector":  "mysql",
        "postgres":         "postgresql",
        "mongodb":          "data-mongodb",
        "mongo":            "data-mongodb",
        "redis":            "data-redis",
        "rabbit":           "amqp",
        "rabbitmq":         "amqp",
        "kafka-streams":    "kafka",
        "spring-batch":     "batch",
        "spring-security":  "security",
        "spring-web":       "web",
        "oauth2":           "oauth2-client",
        "security-oauth2":  "oauth2-client",
        "jwt":              "oauth2-resource-server",
        "test":             "testcontainers",
    }
    suggestions: List[str] = []
    if key in common_aliases:
        suggestions.append(common_aliases[key])

    # FIX B3: guard against overly short partial matches (min 3 chars)
    if len(key) >= 3:
        for dep in flatten_dependencies(metadata):
            dep_id = dep.get("id", "")
            if dep_id not in suggestions and (key in dep_id or dep_id.startswith(key)):
                suggestions.append(dep_id)

    return suggestions[:3]


def check_version_available(metadata: Dict, version: str) -> bool:
    return any(v["id"] == version for v in get_available_versions(metadata))


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def display_version_info(metadata: Dict) -> None:
    versions = get_available_versions(metadata)
    latest = get_latest_version(metadata)
    print(f"\nSpring Boot Versions  (default: {latest})")
    print("-" * 50)
    for v in versions[:15]:
        marker = "-> " if v["id"] == latest else "   "
        print(f"{marker}{v['id']:<22} {v.get('name', v['id'])}")
    if len(versions) > 15:
        print(f"   … and {len(versions) - 15} more (use --fetch-metadata for the full list)")


def display_dependencies(metadata: Dict, category: Optional[str] = None) -> None:
    print("\nAvailable Dependencies")
    print("=" * 60)
    for cat in get_dependencies(metadata):
        cat_name = cat.get("name", "Unknown")
        if category and category.lower() != cat_name.lower():
            continue
        print(f"\n[{cat_name}]")
        print("-" * 40)
        for dep in cat.get("values", []):
            dep_id   = dep.get("id", "")
            dep_name = dep.get("name", "")
            desc     = dep.get("description", "")
            print(f"  {dep_id:<30} {dep_name}")
            if desc:
                print(f"    └─ {desc[:85]}{'…' if len(desc) > 85 else ''}")


# ---------------------------------------------------------------------------
# Package name derivation
# ---------------------------------------------------------------------------

def derive_package_name(group_id: str, artifact_id: str) -> str:
    """
    Derive a valid Java package name from groupId + artifactId.
    Matches Spring Initializr behaviour: strip hyphens AND underscores,
    then lowercase the result.
    e.g. com.example + user-service  -> com.example.userservice
         com.example + order_manager -> com.example.ordermanager
    """
    safe = artifact_id.replace("-", "").replace("_", "").lower()
    return f"{group_id}.{safe}"


# ---------------------------------------------------------------------------
# Project generation
# ---------------------------------------------------------------------------

def generate_project(
    config: Dict,
    force_refresh: bool = False,
) -> Tuple[bool, str, Optional[bytes], Optional[str]]:
    metadata = fetch_metadata(force_refresh=force_refresh)
    if not metadata:
        return False, "Failed to fetch metadata. Please check your network connection.", None, None

    # Validate Spring Boot version
    boot_version = config.get("bootVersion")
    if boot_version and not check_version_available(metadata, boot_version):
        latest = get_latest_version(metadata)
        return False, f"Version '{boot_version}' not available. Latest stable: {latest}", None, None

    # Validate Java version
    java_version = config.get("javaVersion")
    if java_version:
        ok, err = validate_java_version(metadata, java_version)
        if not ok:
            return False, err, None, None

    # Validate dependencies
    deps_str = config.get("dependencies", "") or ""
    deps = [d.strip() for d in deps_str.split(",") if d.strip()]
    if deps:
        _, invalid = validate_dependencies(metadata, deps)
        if invalid:
            hints = []
            for inv in invalid:
                sugg = suggest_alternatives(metadata, inv)
                hints.append(f"  '{inv}'" + (f" → did you mean: {', '.join(sugg)}?" if sugg else ""))
            return False, "Invalid dependencies:\n" + "\n".join(hints), None, None

    group_id    = config.get("groupId",    "com.example")
    artifact_id = config.get("artifactId", "demo")

    params: Dict[str, str] = {
        "type":        config.get("type",        "gradle-project"),
        "groupId":     group_id,
        "artifactId":  artifact_id,
        "version":     config.get("version",     "0.0.1-SNAPSHOT"),
        "name":        config.get("name",        artifact_id),
        "description": config.get("description", "Spring Boot application"),
        "packageName": config.get("packageName") or derive_package_name(group_id, artifact_id),
        "packaging":   config.get("packaging",   "jar"),
        "javaVersion": java_version or "17",
        "language":    config.get("language",    "java"),
        "bootVersion": boot_version or get_latest_version(metadata),
        "dependencies": ",".join(deps),
    }
    # Remove truly empty values (e.g. empty dependencies string → API uses no deps)
    params = {k: v for k, v in params.items() if v}

    try:
        response = requests.get(
            f"{INITIALIZR_URL}/starter.zip",
            params=params,
            timeout=30,
            headers={"User-Agent": USER_AGENT},
        )
        response.raise_for_status()
        return True, "Generated project successfully", response.content, artifact_id

    except requests.exceptions.Timeout:
        return False, "Request timed out. Please try again.", None, None

    except requests.exceptions.HTTPError as e:
        # FIX B4: use e.response instead of bare `response`; fix bare except
        resp = e.response
        if resp is not None and resp.status_code == 400:
            try:
                body  = resp.json()
                msg   = body.get("message", "Unknown error")
                errs  = body.get("errors", [])
                if errs:
                    msg += "\nDetails:\n" + "\n".join(f"  - {x}" for x in errs)
                return False, f"Invalid parameters: {msg}", None, None
            except Exception:
                return False, f"Invalid parameters: {resp.text[:300]}", None, None
        return False, f"HTTP error: {e}", None, None

    except requests.exceptions.RequestException as e:
        return False, f"Request failed: {e}", None, None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Spring Boot Project Generator — powered by start.spring.io",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Generate a project (Gradle, Java 21, web + JPA + MySQL):
    python spring-initializr.py generate \\
        --groupId com.example --artifactId my-app \\
        --javaVersion 21 --dependencies web,data-jpa,mysql

  Maven project:
    python spring-initializr.py generate \\
        --groupId com.example --artifactId my-app \\
        --type maven-project --dependencies web,security

  List versions / dependencies:
    python spring-initializr.py --list-versions
    python spring-initializr.py --list-deps --category web
    python spring-initializr.py --search-deps redis

  Validate dependencies before generating:
    python spring-initializr.py --validate-deps web,data-jpa,mysql

  Force-refresh metadata cache:
    python spring-initializr.py --list-versions --force
""",
    )

    # ── Exploration commands ────────────────────────────────────────────────
    parser.add_argument("--fetch-metadata", action="store_true",
                        help="Fetch and print full metadata JSON")
    parser.add_argument("--list-versions",  action="store_true",
                        help="List available Spring Boot versions")
    parser.add_argument("--list-deps",      action="store_true",
                        help="List all available dependencies by category")
    parser.add_argument("--search-deps",    metavar="KEYWORD",
                        help="Search dependencies by keyword")
    parser.add_argument("--validate-deps",  metavar="IDS",
                        help="Validate comma-separated dependency IDs")
    parser.add_argument("--check-version",  metavar="VERSION",
                        help="Check if a specific Spring Boot version is available")
    parser.add_argument("--category",       metavar="NAME",
                        help="Filter --list-deps output by category name")
    parser.add_argument("--force",          action="store_true",
                        help="Bypass local metadata cache and fetch fresh data")

    # ── Generate subcommand ─────────────────────────────────────────────────
    parser.add_argument("generate", nargs="?",
                        help="Generate a Spring Boot project (requires --groupId and --artifactId)")

    # ── Project configuration ───────────────────────────────────────────────
    parser.add_argument("--type",
                        choices=["maven-project", "gradle-project", "gradle-project-kotlin"],
                        help="Build tool (default: gradle-project)")
    parser.add_argument("--groupId",      "-g", metavar="ID",
                        help="Maven group ID, e.g. com.example")
    parser.add_argument("--artifactId",   "-a", metavar="ID",
                        help="Maven artifact ID / project name, e.g. my-app")
    parser.add_argument("--version",      "-v", metavar="VER",
                        help="Project version (default: 0.0.1-SNAPSHOT)")
    parser.add_argument("--name",         "-n", metavar="NAME",
                        help="Display name (default: artifactId)")
    parser.add_argument("--description",  "-d", metavar="DESC",
                        help="Short description of the project")
    parser.add_argument("--packageName",  "-p", metavar="PKG",
                        help="Root Java package (default: derived from groupId.artifactId, "
                             "hyphens and underscores stripped)")
    parser.add_argument("--packaging",    choices=["jar", "war"],
                        help="Packaging type (default: jar)")
    parser.add_argument("--javaVersion",  "-j", metavar="VER",
                        help="Java version, e.g. 17, 21 (default: 17)")
    parser.add_argument("--language",     "-l", choices=["java", "kotlin", "groovy"],
                        help="Programming language (default: java)")
    parser.add_argument("--bootVersion",  "-b", metavar="VER",
                        help="Spring Boot version (default: latest stable, fetched live)")
    # FIX B6: removed non-standard "-dep" short alias
    parser.add_argument("--dependencies", metavar="IDS",
                        help="Comma-separated dependency IDs, e.g. web,data-jpa,mysql")
    parser.add_argument("--output-dir",   metavar="DIR",
                        help="Directory where the project is written (default: current directory)")

    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve() if args.output_dir else Path.cwd()

    # ── Dispatch exploration commands ────────────────────────────────────────
    if args.fetch_metadata:
        meta = fetch_metadata(force_refresh=args.force)
        if meta:
            print(json.dumps(meta, indent=2))
        else:
            print("Failed to fetch metadata.", file=sys.stderr)
            sys.exit(1)
        return

    if args.list_versions:
        meta = fetch_metadata(force_refresh=args.force)
        if meta:
            display_version_info(meta)
        else:
            print("Failed to fetch metadata.", file=sys.stderr)
            sys.exit(1)
        return

    if args.list_deps:
        meta = fetch_metadata(force_refresh=args.force)
        if meta:
            display_dependencies(meta, args.category)
        else:
            print("Failed to fetch metadata.", file=sys.stderr)
            sys.exit(1)
        return

    if args.search_deps:
        meta = fetch_metadata(force_refresh=args.force)
        if not meta:
            print("Failed to fetch metadata.", file=sys.stderr)
            sys.exit(1)
        results = search_dependencies(meta, args.search_deps)
        if results:
            print(f"\nSearch results for '{args.search_deps}':")
            print("-" * 55)
            for dep in results:
                desc = dep.get("description", "")
                print(f"  {dep['id']:<30} [{dep.get('category', '?')}]  {dep.get('name', '')}")
                if desc:
                    print(f"    {desc[:85]}{'…' if len(desc) > 85 else ''}")
        else:
            print(f"No dependencies found matching '{args.search_deps}'.")
        return

    if args.validate_deps:
        meta = fetch_metadata(force_refresh=args.force)
        if not meta:
            print("Failed to fetch metadata.", file=sys.stderr)
            sys.exit(1)
        dep_list = [d.strip() for d in args.validate_deps.split(",") if d.strip()]
        valid, invalid = validate_dependencies(meta, dep_list)
        if valid:
            print(f"✅ Valid:   {', '.join(valid)}")
        if invalid:
            print(f"❌ Invalid: {', '.join(invalid)}")
            for inv in invalid:
                sugg = suggest_alternatives(meta, inv)
                if sugg:
                    print(f"   '{inv}' → did you mean: {', '.join(sugg)}?")
        if not invalid:
            print("All dependencies are valid.")
        return

    if args.check_version:
        meta = fetch_metadata(force_refresh=args.force)
        if not meta:
            print("Failed to fetch metadata.", file=sys.stderr)
            sys.exit(1)
        if check_version_available(meta, args.check_version):
            print(f"✅ Version {args.check_version} is available.")
        else:
            print(f"❌ Version {args.check_version} is not available.")
            display_version_info(meta)
        return

    # ── Generate project ─────────────────────────────────────────────────────
    # FIX B5: require BOTH groupId AND artifactId to trigger without the 'generate' keyword
    if args.generate == "generate" or (args.groupId and args.artifactId):
        if not args.groupId:
            print("❌ Missing --groupId  (e.g. --groupId com.example)", file=sys.stderr)
            sys.exit(1)
        if not args.artifactId:
            print("❌ Missing --artifactId  (e.g. --artifactId my-app)", file=sys.stderr)
            sys.exit(1)

        config = {k: v for k, v in {
            "type":         args.type,
            "groupId":      args.groupId,
            "artifactId":   args.artifactId,
            "version":      args.version,
            "name":         args.name,
            "description":  args.description,
            "packageName":  args.packageName,
            "packaging":    args.packaging,
            "javaVersion":  args.javaVersion,
            "language":     args.language,
            "bootVersion":  args.bootVersion,
            "dependencies": args.dependencies,
        }.items() if v is not None}

        success, message, content, artifact_id = generate_project(config, force_refresh=args.force)
        print(message)

        if success and content:
            output_dir.mkdir(parents=True, exist_ok=True)
            zip_path = output_dir / f"{artifact_id}.zip"
            try:
                zip_path.write_bytes(content)
                print(f"📦 ZIP saved: {zip_path}")
            except OSError as e:
                print(f"❌ Cannot write ZIP: {e}", file=sys.stderr)
                sys.exit(1)

            extract_dir = output_dir / artifact_id
            if extract_dir.exists() and any(extract_dir.iterdir()):
                print(f"⚠️  '{extract_dir}' already exists and is not empty — skipping auto-extract.",
                      file=sys.stderr)
                print(f"   Manual extract:  unzip {zip_path} -d {extract_dir}-new", file=sys.stderr)
                print(f"   Or rename first: mv {extract_dir} {extract_dir}-backup", file=sys.stderr)
            else:
                try:
                    extract_dir.mkdir(parents=True, exist_ok=True)
                    with zipfile.ZipFile(zip_path, "r") as zf:
                        zf.extractall(extract_dir)
                    zip_path.unlink()
                    print(f"✅ Extracted to: {extract_dir.resolve()}")
                    print(f"\nNext steps:\n  cd {extract_dir}")
                except (zipfile.BadZipFile, OSError) as e:
                    print(f"❌ Extraction failed: {e}", file=sys.stderr)
                    print(f"   ZIP preserved at: {zip_path}", file=sys.stderr)
                    sys.exit(1)

        if not success:
            sys.exit(1)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
