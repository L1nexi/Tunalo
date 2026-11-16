from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import sys
import zipfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION_PATH = ROOT / "src" / "app" / "version.py"
CHANGELOG_PATH = ROOT / "CHANGELOG.md"
DIST_EXE = "Tunalo.exe"
DIST_DOCS = ("README.md", "CHANGELOG.md", ".env.example")
TAG_PATTERN = re.compile(r"^v(?P<version>\d+\.\d+\.\d+)$")
VERSION_PATTERN = re.compile(r'(?m)^VERSION\s*=\s*["\'](?P<version>[^"\']+)["\']\s*$')
CHANGELOG_HEADING_PATTERN = re.compile(r"(?m)^## \[(?P<version>\d+\.\d+\.\d+)\] [-—] (?P<date>\d{4}-\d{2}-\d{2})\s*$")


class ReleaseError(Exception):
    """Raised when release metadata or distribution files are invalid."""


@dataclass(frozen=True)
class ChangelogEntry:
    version: str
    date: str
    body: str


@dataclass(frozen=True)
class ReleaseRequest:
    tag: str
    dist_dir: Path
    output_dir: Path


@dataclass(frozen=True)
class PackagePaths:
    archive: Path
    checksums: Path
    notes: Path
    manifest: Path


def parse_version(source: str) -> str:
    """Read the application version from the version module source.

    Raises:
        ReleaseError: The source has no `VERSION = "..."` assignment.

    """
    match = VERSION_PATTERN.search(source)
    if match is None:
        raise ReleaseError("Version source does not define VERSION.")
    return match.group("version")


def _clean_section(text: str) -> str:
    lines = text.strip().splitlines()
    if lines and lines[-1].strip() == "---":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def extract_changelog_entry(changelog: str, version: str) -> ChangelogEntry:
    """Return the CHANGELOG section for one version.

    Raises:
        ReleaseError: The section is missing or has no content.

    """
    headings = list(CHANGELOG_HEADING_PATTERN.finditer(changelog))
    for index, heading in enumerate(headings):
        if heading.group("version") != version:
            continue
        end = headings[index + 1].start() if index + 1 < len(headings) else len(changelog)
        body = _clean_section(changelog[heading.end() : end])
        if not body:
            raise ReleaseError(f"CHANGELOG.md section for version {version} is empty.")
        return ChangelogEntry(version=version, date=heading.group("date"), body=body)
    raise ReleaseError(f"CHANGELOG.md has no section for version {version}.")


def validate_release(tag: str, *, version_source: str, changelog: str) -> ChangelogEntry:
    """Validate that the tag, application version, and CHANGELOG agree.

    Raises:
        ReleaseError: The tag is malformed, the versions differ, or the
            CHANGELOG section is missing or empty.

    """
    match = TAG_PATTERN.fullmatch(tag)
    if match is None:
        raise ReleaseError(f"Tag {tag!r} must match v<major>.<minor>.<patch>; prerelease tags are not supported.")
    version = match.group("version")
    declared = parse_version(version_source)
    if declared != version:
        raise ReleaseError(f"Version source declares {declared} but the tag is {tag}.")
    return extract_changelog_entry(changelog, version)


def stage_distribution(dist_dir: Path, *, source_dir: Path = ROOT) -> tuple[Path, ...]:
    """Copy the executable's companion documents into the distribution directory.

    Raises:
        ReleaseError: The executable or a document is missing, or copying fails.

    """
    exe = dist_dir / DIST_EXE
    if not exe.is_file():
        raise ReleaseError(f"Missing distribution file: {exe}.")
    staged = [exe]
    for name in DIST_DOCS:
        source = source_dir / name
        if not source.is_file():
            raise ReleaseError(f"Missing distribution file: {source}.")
        target = dist_dir / name
        try:
            shutil.copyfile(source, target)
        except OSError as exc:
            raise ReleaseError(f"Could not copy {source} to {target}: {exc}") from exc
        staged.append(target)
    return tuple(staged)


def build_archive(request: ReleaseRequest) -> Path:
    """Create the release zip from the staged distribution files.

    Raises:
        ReleaseError: A staged file is missing or the archive cannot be written.

    """
    files = (DIST_EXE, *DIST_DOCS)
    missing = [str(request.dist_dir / name) for name in files if not (request.dist_dir / name).is_file()]
    if missing:
        raise ReleaseError(f"Missing distribution files: {', '.join(missing)}.")
    archive = request.output_dir / f"Tunalo-{request.tag}-windows-x64.zip"
    try:
        request.output_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as archive_file:
            for name in files:
                archive_file.write(request.dist_dir / name, arcname=name)
    except OSError as exc:
        raise ReleaseError(f"Could not create {archive}: {exc}") from exc
    return archive


def write_checksums(archive: Path, output: Path) -> Path:
    """Write a sha256sum-compatible checksum file for the release archive.

    Raises:
        ReleaseError: The archive cannot be read or the checksum file cannot be written.

    """
    try:
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        output.write_text(f"{digest}  {archive.name}\n", encoding="utf-8", newline="\n")
    except OSError as exc:
        raise ReleaseError(f"Could not write checksums for {archive}: {exc}") from exc
    return output


def render_notes(entry: ChangelogEntry) -> str:
    """Render the GitHub release body from one CHANGELOG section."""
    return f"## 本次更新\n\n{entry.body}\n"


def package_release(entry: ChangelogEntry, request: ReleaseRequest) -> PackagePaths:
    """Create the archive, checksums, notes, and asset manifest.

    Raises:
        ReleaseError: The distribution is incomplete or a release file cannot be written.

    """
    archive = build_archive(request)
    checksums = write_checksums(archive, request.output_dir / "SHA256SUMS.txt")
    notes = request.output_dir / "release-notes.md"
    manifest = request.output_dir / "assets.txt"
    try:
        notes.write_text(render_notes(entry), encoding="utf-8", newline="\n")
        manifest.write_text(f"{archive}\n{checksums}\n", encoding="utf-8", newline="\n")
    except OSError as exc:
        raise ReleaseError(f"Could not write release metadata: {exc}") from exc
    return PackagePaths(archive=archive, checksums=checksums, notes=notes, manifest=manifest)


def _read_text(path: Path) -> str:
    """Read a UTF-8 text file.

    Raises:
        ReleaseError: The file cannot be read.

    """
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ReleaseError(f"Could not read {path}: {exc}") from exc


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate and package a Tunalo release.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Check that the tag, VERSION, and CHANGELOG agree.")
    validate_parser.add_argument("--tag", required=True)

    stage_parser = subparsers.add_parser("stage", help="Copy companion documents into the distribution directory.")
    stage_parser.add_argument("--dist", type=Path, default=Path("dist"))

    package_parser = subparsers.add_parser("package", help="Build the release archive, checksums, and notes.")
    package_parser.add_argument("--tag", required=True)
    package_parser.add_argument("--dist", type=Path, default=Path("dist"))
    package_parser.add_argument("--output", type=Path, default=Path("dist/release"))

    args = parser.parse_args(argv)

    try:
        if args.command == "stage":
            staged = stage_distribution(args.dist)
            print(f"Staged {len(staged)} distribution files in {args.dist}.")
            return 0

        entry = validate_release(
            args.tag,
            version_source=_read_text(VERSION_PATH),
            changelog=_read_text(CHANGELOG_PATH),
        )
        if args.command == "validate":
            print(f"{args.tag} matches {VERSION_PATH} and {CHANGELOG_PATH}.")
            return 0

        request = ReleaseRequest(tag=args.tag, dist_dir=args.dist, output_dir=args.output)
        paths = package_release(entry, request)
        print(f"Archive: {paths.archive}")
        print(f"Checksums: {paths.checksums}")
        print(f"Notes: {paths.notes}")
        print(f"Manifest: {paths.manifest}")
        return 0
    except ReleaseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
