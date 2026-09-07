from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter


BITSET_SIZE_BITS = 100_000_000
BITSET_SIZE_BYTES = (BITSET_SIZE_BITS + 7) // 8


@dataclass(frozen=True)
class ActiveCnpjBitsetResult:
    unique_cnpjs_ativos: int
    bits_marcados: int
    duration_ms: int
    approx_memory_mb: float
    bitset_size_bytes: int
    bitset: bytes | None = None


def build_active_cnpj_bitset(conn, include_bitset: bool = False) -> ActiveCnpjBitsetResult:
    start = perf_counter()
    bitset = bytearray(BITSET_SIZE_BYTES)
    unique_cnpjs_ativos = 0

    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT cnpj_basico
            FROM public.estabelecimentos
            WHERE situacao_cadastral = '02'
            """
        )
        for (cnpj_basico,) in cursor:
            if len(cnpj_basico) != 8 or not cnpj_basico.isdigit():
                raise ValueError(f"cnpj_basico invalido para bitset: {cnpj_basico!r}")
            index = int(cnpj_basico)
            byte_index = index >> 3
            bit_mask = 1 << (index & 7)
            if not (bitset[byte_index] & bit_mask):
                bitset[byte_index] |= bit_mask
                unique_cnpjs_ativos += 1

    duration_ms = int((perf_counter() - start) * 1000)
    return ActiveCnpjBitsetResult(
        unique_cnpjs_ativos=unique_cnpjs_ativos,
        bits_marcados=unique_cnpjs_ativos,
        duration_ms=duration_ms,
        approx_memory_mb=BITSET_SIZE_BYTES / 1024 / 1024,
        bitset_size_bytes=BITSET_SIZE_BYTES,
        bitset=bytes(bitset) if include_bitset else None,
    )


def bitset_contains(bitset: bytes | bytearray, cnpj_basico: str) -> bool:
    if len(cnpj_basico) != 8 or not cnpj_basico.isdigit():
        return False
    index = int(cnpj_basico)
    byte_index = index >> 3
    if byte_index >= len(bitset):
        return False
    return bool(bitset[byte_index] & (1 << (index & 7)))
