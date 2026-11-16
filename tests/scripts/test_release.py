from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

import pytest
import release

CHANGELOG = """# Changelog

## [Unreleased]

- 待发布内容。

## [1.2.0] - 2026-11-16

摘要。

### Added

- 新功能。

## [1.1.0] — 2026-10-01

旧版本。

---

## [1.0.0] - 2026-09-01

最早版本。
"""

VERSION_SOURCE = 'VERSION = "1.2.0"\n'


def _entry() -> release.ChangelogEntry:
    return release.extract_changelog_entry(CHANGELOG, "1.2.0")


def _make_dist(root: Path, *, include_docs: bool = True, extra: bool = False) -> Path:
    dist = root / "dist"
    dist.mkdir(parents=True, exist_ok=True)
    (dist / release.DIST_EXE).write_text("exe", encoding="utf-8")
    if include_docs:
        for name in release.DIST_DOCS:
            (dist / name).write_text(f"content of {name}", encoding="utf-8")
    if extra:
        (dist / "profile.json").write_text("{}", encoding="utf-8")
    return dist


def _make_source(root: Path) -> None:
    for name in release.DIST_DOCS:
        (root / name).write_text(f"source of {name}", encoding="utf-8")


def _request(root: Path) -> release.ReleaseRequest:
    return release.ReleaseRequest(tag="v1.2.0", dist_dir=root / "dist", output_dir=root / "release")


def _configure_metadata(monkeypatch: pytest.MonkeyPatch, root: Path, *, version: str = "1.2.0") -> None:
    version_path = root / "version.py"
    version_path.write_text(f'VERSION = "{version}"\n', encoding="utf-8")
    changelog_path = root / "CHANGELOG.md"
    changelog_path.write_text(CHANGELOG, encoding="utf-8")
    monkeypatch.setattr(release, "VERSION_PATH", version_path)
    monkeypatch.setattr(release, "CHANGELOG_PATH", changelog_path)


def test_parse_version_returns_declared_version() -> None:
    assert release.parse_version(VERSION_SOURCE) == "1.2.0"


def test_parse_version_rejects_missing_assignment() -> None:
    with pytest.raises(release.ReleaseError, match="does not define VERSION"):
        release.parse_version('OTHER = "1.2.0"\n')


def test_validate_release_accepts_matching_metadata() -> None:
    entry = release.validate_release("v1.2.0", version_source=VERSION_SOURCE, changelog=CHANGELOG)

    assert entry.version == "1.2.0"
    assert entry.date == "2026-11-16"
    assert entry.body.startswith("摘要。")
    assert "旧版本" not in entry.body


def test_extract_changelog_entry_strips_trailing_separator() -> None:
    entry = release.extract_changelog_entry(CHANGELOG, "1.1.0")

    assert entry.body == "旧版本。"
    assert entry.date == "2026-10-01"


def test_validate_release_rejects_version_mismatch() -> None:
    with pytest.raises(release.ReleaseError, match="declares 1.2.0 but the tag is v1.3.0"):
        release.validate_release("v1.3.0", version_source=VERSION_SOURCE, changelog=CHANGELOG)


def test_validate_release_rejects_malformed_tag() -> None:
    with pytest.raises(release.ReleaseError, match="must match v<major>.<minor>.<patch>"):
        release.validate_release("1.2.0", version_source=VERSION_SOURCE, changelog=CHANGELOG)


def test_validate_release_rejects_missing_section() -> None:
    with pytest.raises(release.ReleaseError, match="has no section for version 1.3.0"):
        release.validate_release("v1.3.0", version_source='VERSION = "1.3.0"\n', changelog=CHANGELOG)


def test_validate_release_rejects_empty_section() -> None:
    changelog = "# Changelog\n\n## [1.2.0] - 2026-11-16\n\n---\n"

    with pytest.raises(release.ReleaseError, match="section for version 1.2.0 is empty"):
        release.validate_release("v1.2.0", version_source=VERSION_SOURCE, changelog=changelog)


def test_render_notes_uses_changelog_body() -> None:
    entry = _entry()

    assert release.render_notes(entry) == f"## 本次更新\n\n{entry.body}\n"


def test_stage_distribution_copies_documents(tmp_path: Path) -> None:
    dist = _make_dist(tmp_path, include_docs=False)
    _make_source(tmp_path)

    staged = release.stage_distribution(dist, source_dir=tmp_path)

    assert [path.name for path in staged] == [release.DIST_EXE, *release.DIST_DOCS]
    for name in release.DIST_DOCS:
        assert (dist / name).read_text(encoding="utf-8") == f"source of {name}"


def test_stage_distribution_rejects_missing_executable(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    _make_source(tmp_path)

    with pytest.raises(release.ReleaseError, match="Tunalo.exe"):
        release.stage_distribution(dist, source_dir=tmp_path)


def test_stage_distribution_rejects_missing_document(tmp_path: Path) -> None:
    dist = _make_dist(tmp_path, include_docs=False)

    with pytest.raises(release.ReleaseError, match="README.md"):
        release.stage_distribution(dist, source_dir=tmp_path)


def test_package_release_creates_archive_checksums_notes_and_manifest(tmp_path: Path) -> None:
    _make_dist(tmp_path, extra=True)
    request = _request(tmp_path)

    paths = release.package_release(_entry(), request)

    assert paths.archive.name == "Tunalo-v1.2.0-windows-x64.zip"
    with zipfile.ZipFile(paths.archive) as archive:
        assert archive.namelist() == [release.DIST_EXE, *release.DIST_DOCS]
    digest = hashlib.sha256(paths.archive.read_bytes()).hexdigest()
    assert paths.checksums.read_text(encoding="utf-8") == f"{digest}  {paths.archive.name}\n"
    assert paths.notes.read_text(encoding="utf-8").startswith("## 本次更新\n\n摘要。")
    assert paths.manifest.read_text(encoding="utf-8") == f"{paths.archive}\n{paths.checksums}\n"


def test_build_archive_rejects_missing_distribution_file(tmp_path: Path) -> None:
    _make_dist(tmp_path, include_docs=False)

    with pytest.raises(release.ReleaseError, match="README.md"):
        release.build_archive(_request(tmp_path))


def test_main_validates_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _configure_metadata(monkeypatch, tmp_path)

    assert release.main(["validate", "--tag", "v1.2.0"]) == 0
    assert "matches" in capsys.readouterr().out


def test_main_reports_validation_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _configure_metadata(monkeypatch, tmp_path)

    assert release.main(["validate", "--tag", "v1.3.0"]) == 1
    assert "declares 1.2.0" in capsys.readouterr().err


def test_main_packages_release(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _configure_metadata(monkeypatch, tmp_path)
    _make_dist(tmp_path)
    output = tmp_path / "release"

    exit_code = release.main(
        [
            "package",
            "--tag",
            "v1.2.0",
            "--dist",
            str(tmp_path / "dist"),
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    assert (output / "Tunalo-v1.2.0-windows-x64.zip").is_file()
    assert (output / "SHA256SUMS.txt").is_file()
    assert (output / "release-notes.md").is_file()
    assert (output / "assets.txt").is_file()
    assert "Archive:" in capsys.readouterr().out
