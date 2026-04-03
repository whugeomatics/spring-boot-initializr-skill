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
USER_AGENT = "spring-boot-initializr-skill/1.0"
METADATA_HEADERS = {
    "Accept": "application/vnd.initializr.v2.2+json",
    "User-Agent": USER_AGENT
}

CACHE_DIR = Path.home() / ".cache" / "spring-initializr-skill"
CACHE_FILE = CACHE_DIR / "metadata.json"
CACHE_TTL_HOURS = 1


def get_cache_dir() -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR


def load_cached_metadata() -> Optional[Dict]:
    if not CACHE_FILE.exists():
        return None
    try:
        with open(CACHE_FILE, 'r') as f:
            cached = json.load(f)
        cached_time = datetime.fromisoformat(cached.get('_cached_at', '2000-01-01'))
        if datetime.now() - cached_time > timedelta(hours=CACHE_TTL_HOURS):
            return None
        return cached.get('data')
    except (json.JSONDecodeError, KeyError, OSError):
        return None


def save_cached_metadata(data: Dict) -> None:
    get_cache_dir()
    cache_data = {
        'data': data,
        '_cached_at': datetime.now().isoformat()
    }
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache_data, f)
    except OSError:
        pass


def fetch_metadata(force_refresh: bool = False, max_retries: int = 3) -> Optional[Dict]:
    if not force_refresh:
        cached = load_cached_metadata()
        if cached:
            return cached
    for attempt in range(max_retries):
        try:
            response = requests.get(
                INITIALIZR_URL,
                headers=METADATA_HEADERS,
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            save_cached_metadata(data)
            return data
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            print(f"Timeout after {max_retries} attempts", file=sys.stderr)
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            print(f"Failed to fetch metadata: {e}", file=sys.stderr)
    return None


def get_available_versions(metadata: Dict) -> List[Dict]:
    return metadata.get('bootVersion', {}).get('values', [])


def get_latest_version(metadata: Dict) -> str:
    return metadata.get('bootVersion', {}).get('default', '4.0.5')


def get_java_versions(metadata: Dict) -> List[str]:
    java_versions = metadata.get('javaVersion', {}).get('values', [])
    return [v['id'] for v in java_versions if 'id' in v]


def validate_java_version(metadata: Dict, java_version: str) -> Tuple[bool, Optional[str]]:
    versions = get_java_versions(metadata)
    if java_version in versions:
        return True, None
    if versions:
        return False, f"Java {java_version} not supported. Available: {', '.join(versions)}"
    return True, None  # If metadata doesn't provide java versions, skip validation


def get_dependencies(metadata: Dict) -> List[Dict]:
    return metadata.get('dependencies', {}).get('values', [])


def flatten_dependencies(metadata: Dict) -> List[Dict]:
    result = []
    for category in get_dependencies(metadata):
        if 'values' in category:
            for dep in category['values']:
                dep['category'] = category.get('name', 'Unknown')
                result.append(dep)
        else:
            result.append(category)
    return result


def search_dependencies(metadata: Dict, query: str) -> List[Dict]:
    query_lower = query.lower()
    results = []
    for dep in flatten_dependencies(metadata):
        name = dep.get('name', '').lower()
        desc = dep.get('description', '').lower()
        dep_id = dep.get('id', '').lower()
        if query_lower in name or query_lower in desc or query_lower in dep_id:
            results.append(dep)
    return results[:20]


def validate_dependencies(metadata: Dict, dep_ids: List[str]) -> Tuple[List[str], List[str]]:
    valid_ids = {d['id'] for d in flatten_dependencies(metadata)}
    valid = [d for d in dep_ids if d in valid_ids]
    invalid = [d for d in dep_ids if d not in valid_ids]
    return valid, invalid


def suggest_alternatives(metadata: Dict, invalid_dep: str) -> List[str]:
    suggestions = []
    common_typos = {
        'jpa': 'data-jpa',
        'mysql-connector': 'mysql',
        'postgres': 'postgresql',
        'security-oauth2': 'oauth2-client',
        'oauth2': 'oauth2-client',
        'jwt': 'oauth2-resource-server',
    }
    if invalid_dep in common_typos:
        suggestions.append(common_typos[invalid_dep])
    for dep in flatten_dependencies(metadata):
        dep_id = dep.get('id', '')
        if invalid_dep.lower() in dep_id or dep_id in invalid_dep.lower():
            if dep_id not in suggestions:
                suggestions.append(dep_id)
    return suggestions[:3]


def check_version_available(metadata: Dict, version: str) -> bool:
    versions = get_available_versions(metadata)
    return any(v['id'] == version for v in versions)


def display_version_info(metadata: Dict) -> None:
    versions = get_available_versions(metadata)
    latest = get_latest_version(metadata)
    print(f"\nSpring Boot Versions (latest: {latest})")
    print("-" * 50)
    for v in versions[:15]:
        marker = "-> " if v['id'] == latest else "   "
        print(f"{marker}{v['id']:<20} {v.get('name', v['id'])}")
    if len(versions) > 15:
        print(f"  ... and {len(versions) - 15} more")


def display_dependencies(metadata: Dict, category: str = None) -> None:
    deps = get_dependencies(metadata)
    print("\nAvailable Dependencies")
    print("=" * 60)
    for cat in deps:
        cat_name = cat.get('name', 'Unknown')
        if category and category.lower() != cat_name.lower():
            continue
        print(f"\n{cat_name}:")
        print("-" * 40)
        for dep in cat.get('values', []):
            dep_id = dep.get('id', '')
            dep_name = dep.get('name', '')
            print(f"  * {dep_id:<28} - {dep_name}")


def generate_project(config: Dict, force_refresh: bool = False) -> Tuple[bool, str, Optional[bytes], Optional[str]]:
    metadata = fetch_metadata(force_refresh=force_refresh)
    if not metadata:
        return False, "Failed to fetch metadata. Please check network connection.", None, None

    boot_version = config.get('bootVersion')
    if boot_version and not check_version_available(metadata, boot_version):
        latest = get_latest_version(metadata)
        return False, f"Version {boot_version} not available. Latest: {latest}", None, None

    # Java version validation
    java_version = config.get('javaVersion')
    if java_version:
        valid, err_msg = validate_java_version(metadata, java_version)
        if not valid:
            return False, err_msg, None, None

    # Dependency handling: handle empty string correctly
    deps_str = config.get('dependencies', '')
    deps = [d.strip() for d in deps_str.split(',') if d.strip()] if deps_str else []

    if deps:
        valid, invalid = validate_dependencies(metadata, deps)
        if invalid:
            suggestions = []
            for inv in invalid:
                sugg = suggest_alternatives(metadata, inv)
                if sugg:
                    suggestions.append(f"{inv} -> {', '.join(sugg)}")
            if suggestions:
                return False, f"Invalid dependencies: {', '.join(invalid)}\nSuggestions: {'; '.join(suggestions)}", None, None
            return False, f"Invalid dependencies: {', '.join(invalid)}", None, None

    params = {
        'type': config.get('type', 'gradle-project'),
        'groupId': config.get('groupId', 'com.example'),
        'artifactId': config.get('artifactId', 'demo'),
        'version': config.get('version', '0.0.1-SNAPSHOT'),
        'name': config.get('name', config.get('artifactId', 'demo')),
        'description': config.get('description', 'Spring Boot application'),
        'packageName': config.get('packageName',
                                  f"{config.get('groupId', 'com.example')}.{config.get('artifactId', 'demo').replace('-', '').replace('_', '')}"),
        'packaging': config.get('packaging', 'jar'),
        'javaVersion': java_version or '17',
        'language': config.get('language', 'java'),
        'bootVersion': boot_version or get_latest_version(metadata),
        'dependencies': ','.join(deps) if deps else ''
    }
    params = {k: v for k, v in params.items() if v}

    try:
        response = requests.get(
            f"{INITIALIZR_URL}/starter.zip",
            params=params,
            timeout=30,
            headers={"User-Agent": USER_AGENT}
        )
        response.raise_for_status()
        return True, "Generated project successfully", response.content, params['artifactId']
    except requests.exceptions.Timeout:
        return False, "Request timeout. Please try again.", None, None
    except requests.exceptions.HTTPError as e:
        if response.status_code == 400:
            try:
                error_json = response.json()
                msg = error_json.get('message', 'Unknown error')
                errors = error_json.get('errors', [])
                if errors:
                    msg += "\nDetails: " + "\n".join(errors)
                return False, f"Invalid parameters: {msg}", None, None
            except:
                return False, f"Invalid parameters: {response.text[:200]}", None, None
        return False, f"HTTP error: {e}", None, None
    except requests.exceptions.RequestException as e:
        return False, f"Request failed: {e}", None, None


def main():
    parser = argparse.ArgumentParser(
        description="Spring Boot Project Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--fetch-metadata", action="store_true", help="Fetch and display metadata")
    parser.add_argument("--list-versions", action="store_true", help="List available Spring Boot versions")
    parser.add_argument("--list-deps", action="store_true", help="List all dependencies")
    parser.add_argument("--search-deps", type=str, help="Search dependencies by keyword")
    parser.add_argument("--validate-deps", type=str, help="Validate comma-separated dependency IDs")
    parser.add_argument("--check-version", type=str, help="Check if Spring Boot version is available")
    parser.add_argument("--category", type=str, help="Filter dependencies by category")
    parser.add_argument("--force", action="store_true", help="Force refresh cache")
    parser.add_argument("generate", nargs="?", help="Generate project ZIP")
    parser.add_argument("--type", choices=["maven-project", "gradle-project", "gradle-project-kotlin"], help="Build type")
    parser.add_argument("--groupId", "-g", help="Group ID")
    parser.add_argument("--artifactId", "-a", help="Artifact ID")
    parser.add_argument("--version", "-v", help="Project version")
    parser.add_argument("--name", "-n", help="Project name")
    parser.add_argument("--description", "-d", help="Project description")
    parser.add_argument("--packageName", "-p", help="Package name")
    parser.add_argument("--packaging", choices=["jar", "war"], help="Packaging type")
    parser.add_argument("--javaVersion", "-j", help="Java version")
    parser.add_argument("--language", "-l", choices=["java", "kotlin", "groovy"], help="Language")
    parser.add_argument("--bootVersion", "-b", help="Spring Boot version")
    parser.add_argument("--dependencies", "-dep", help="Comma-separated dependencies")

    args = parser.parse_args()

    if args.fetch_metadata:
        metadata = fetch_metadata(force_refresh=args.force)
        if metadata:
            print(json.dumps(metadata, indent=2))
        else:
            print("Failed to fetch metadata", file=sys.stderr)
            sys.exit(1)
        return

    if args.list_versions:
        metadata = fetch_metadata(force_refresh=args.force)
        if metadata:
            display_version_info(metadata)
        else:
            print("Failed to fetch metadata", file=sys.stderr)
            sys.exit(1)
        return

    if args.list_deps:
        metadata = fetch_metadata(force_refresh=args.force)
        if metadata:
            display_dependencies(metadata, args.category)
        else:
            print("Failed to fetch metadata", file=sys.stderr)
            sys.exit(1)
        return

    if args.search_deps:
        metadata = fetch_metadata(force_refresh=args.force)
        if metadata:
            results = search_dependencies(metadata, args.search_deps)
            if results:
                print(f"\nSearch results for '{args.search_deps}':")
                print("-" * 50)
                for dep in results:
                    print(f"  * {dep['id']:<28} - {dep.get('name', dep['id'])}")
                    print(f"    Category: {dep.get('category', 'Unknown')}")
            else:
                print(f"No dependencies found matching '{args.search_deps}'")
        else:
            print("Failed to fetch metadata", file=sys.stderr)
            sys.exit(1)
        return

    if args.validate_deps:
        metadata = fetch_metadata(force_refresh=args.force)
        if metadata:
            dep_list = [d.strip() for d in args.validate_deps.split(',')]
            valid, invalid = validate_dependencies(metadata, dep_list)
            if valid:
                print(f"Valid: {', '.join(valid)}")
            if invalid:
                print(f"Invalid: {', '.join(invalid)}")
                for inv in invalid:
                    suggestions = suggest_alternatives(metadata, inv)
                    if suggestions:
                        print(f"   Did you mean: {', '.join(suggestions)}?")
        else:
            print("Failed to fetch metadata", file=sys.stderr)
            sys.exit(1)
        return

    if args.check_version:
        metadata = fetch_metadata(force_refresh=args.force)
        if metadata:
            if check_version_available(metadata, args.check_version):
                print(f"Version {args.check_version} is available")
            else:
                print(f"Version {args.check_version} is not available")
                display_version_info(metadata)
        else:
            print("Failed to fetch metadata", file=sys.stderr)
            sys.exit(1)
        return

    if args.generate == "generate" or any([args.groupId, args.artifactId]):
        if not args.groupId:
            print("Missing required: --groupId", file=sys.stderr)
            sys.exit(1)
        if not args.artifactId:
            print("Missing required: --artifactId", file=sys.stderr)
            sys.exit(1)
        config = {
            'type': args.type,
            'groupId': args.groupId,
            'artifactId': args.artifactId,
            'version': args.version,
            'name': args.name,
            'description': args.description,
            'packageName': args.packageName,
            'packaging': args.packaging,
            'javaVersion': args.javaVersion,
            'language': args.language,
            'bootVersion': args.bootVersion,
            'dependencies': args.dependencies
        }
        config = {k: v for k, v in config.items() if v is not None}
        success, message, content, artifact_id = generate_project(config, force_refresh=args.force)
        print(message)
        if success and content:
            zip_path = Path.cwd() / f"{artifact_id}.zip"
            try:
                with open(zip_path, "wb") as f:
                    f.write(content)
                print(f"📦 ZIP saved to: {zip_path}")
            except OSError as e:
                print(f"❌ Failed to write ZIP file: {e}", file=sys.stderr)
                print(f"   Target path: {zip_path}", file=sys.stderr)
                print(f"   Please check disk space and write permissions.", file=sys.stderr)
                sys.exit(1)
            except Exception as e:
                print(f"❌ Unexpected error writing ZIP file: {e}", file=sys.stderr)
                sys.exit(1)

            extract_dir = Path.cwd() / artifact_id

            if extract_dir.exists() and any(extract_dir.iterdir()):
                # Directory exists and not empty – do not auto-extract
                print(f"⚠️  Directory '{artifact_id}' already exists and is not empty.", file=sys.stderr)
                print(f"   Auto-extraction skipped to avoid overwriting.", file=sys.stderr)
                print(f"   You can manually extract the project with:", file=sys.stderr)
                print(f"   unzip {zip_path} -d {artifact_id}", file=sys.stderr)
                print(f"   Or remove/rename the existing directory and rerun.", file=sys.stderr)
            else:
                # Safe to extract
                try:
                    extract_dir.mkdir(parents=True, exist_ok=True)
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_dir)
                    zip_path.unlink()
                    print(f"✅ Project extracted to: {extract_dir.resolve()}")
                    print(f"\nNext steps:")
                    print(f"  cd {artifact_id}")
                except (zipfile.BadZipFile, OSError) as e:
                    print(f"❌ Failed to extract project: {e}", file=sys.stderr)
                    print(f"   ZIP file is saved at: {zip_path}", file=sys.stderr)
                    sys.exit(1)

        if not success:
            sys.exit(1)
        return

    parser.print_help()


if __name__ == "__main__":
    main()