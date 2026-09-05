from __future__ import annotations

import hashlib
import json
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path


class SourceArtifactError(ValueError):
    """Erro de dominio para uma origem RFB invalida."""


_ZIP_KIND_PATTERNS = [
    ("Empresas", re.compile(r"^Empresas\d+\.zip$", re.IGNORECASE)),
    ("Estabelecimentos", re.compile(r"^Estabelecimentos\d+\.zip$", re.IGNORECASE)),
    ("Socios", re.compile(r"^Socios\d+\.zip$", re.IGNORECASE)),
    ("Cnaes", re.compile(r"^Cnaes\.zip$", re.IGNORECASE)),
    ("Municipios", re.compile(r"^Municipios\.zip$", re.IGNORECASE)),
    ("Motivos", re.compile(r"^Motivos\.zip$", re.IGNORECASE)),
    ("Naturezas", re.compile(r"^Naturezas\.zip$", re.IGNORECASE)),
    ("Paises", re.compile(r"^Paises\.zip$", re.IGNORECASE)),
    ("Qualificacoes", re.compile(r"^Qualificacoes\.zip$", re.IGNORECASE)),
    ("Simples", re.compile(r"^Simples\.zip$", re.IGNORECASE)),
]

REQUIRED_ZIP_KINDS = [kind for kind, _ in _ZIP_KIND_PATTERNS]


@dataclass(frozen=True)
class ZipArtifact:
    kind: str
    zip_name: str
    zip_path: Path
    sha256: str
    zip_size_bytes: int
    member_name: str
    member_size_bytes: int
    member_crc32: int
    member_compress_size_bytes: int


@dataclass(frozen=True)
class IgnoredZip:
    zip_name: str
    zip_path: Path


@dataclass(frozen=True)
class ZipInventory:
    zip_files: list[ZipArtifact]
    ignored: list[IgnoredZip]

    @property
    def fingerprint(self) -> str:
        payload = [
            {
                "kind": item.kind,
                "zip_name": item.zip_name,
                "sha256": item.sha256,
                "member_name": item.member_name,
                "member_size_bytes": item.member_size_bytes,
                "member_crc32": item.member_crc32,
            }
            for item in sorted(self.zip_files, key=lambda value: (value.kind, value.zip_name))
        ]
        encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


def classify_zip_name(zip_name: str) -> str | None:
    for kind, pattern in _ZIP_KIND_PATTERNS:
        if pattern.match(zip_name):
            return kind
    return None


def inspect_zip_artifact(zip_path: Path) -> ZipArtifact:
    zip_path = Path(zip_path)
    if not zip_path.is_file():
        raise SourceArtifactError(f"ZIP inexistente: {zip_path}")

    # O preflight calcula o SHA do ZIP compactado, mas nao valida o membro inteiro.
    hasher = hashlib.sha256()
    with zip_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    sha256 = hasher.hexdigest()

    try:
        with zipfile.ZipFile(zip_path) as archive:
            members = [member for member in archive.infolist() if not member.is_dir()]
    except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
        raise SourceArtifactError(f"ZIP invalido: {zip_path.name}") from exc

    if not members:
        raise SourceArtifactError(f"ZIP sem membro regular: {zip_path.name}")
    if len(members) != 1:
        raise SourceArtifactError(
            f"ZIP deve conter um unico membro regular: {zip_path.name}"
        )
    member = members[0]

    kind = classify_zip_name(zip_path.name)
    if kind is None:
        raise SourceArtifactError(f"ZIP nao reconhecido: {zip_path.name}")

    return ZipArtifact(
        kind=kind,
        zip_name=zip_path.name,
        zip_path=zip_path,
        sha256=sha256,
        zip_size_bytes=zip_path.stat().st_size,
        member_name=member.filename,
        member_size_bytes=member.file_size,
        member_crc32=member.CRC,
        member_compress_size_bytes=member.compress_size,
    )


def discover_zip_inventory(source_dir: Path | str) -> ZipInventory:
    source_path = Path(source_dir)
    zip_files: list[ZipArtifact] = []
    ignored: list[IgnoredZip] = []

    for item in sorted(source_path.iterdir(), key=lambda path: path.name.lower()):
        if item.is_dir():
            continue
        if item.suffix.lower() != ".zip":
            continue
        if item.name.lower() == "download.zip":
            ignored.append(IgnoredZip(zip_name=item.name, zip_path=item))
            continue
        kind = classify_zip_name(item.name)
        if kind is None:
            ignored.append(IgnoredZip(zip_name=item.name, zip_path=item))
            continue
        zip_files.append(inspect_zip_artifact(item))

    return ZipInventory(zip_files=zip_files, ignored=ignored)


def required_zip_kind_set() -> set[str]:
    return set(REQUIRED_ZIP_KINDS)


def missing_required_zip_kinds(inventory: ZipInventory) -> set[str]:
    present = {item.kind for item in inventory.zip_files}
    return required_zip_kind_set() - present
