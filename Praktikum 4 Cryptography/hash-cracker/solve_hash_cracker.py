import argparse
import hashlib
from Crypto.Hash import keccak
from pathlib import Path
import sys
import time

def load_hashes(path: Path):
    """Baca file hash, hapus spasi/linebreak, kembalikan list hexa kecil."""
    if not path.exists():
        print(f"[!] File tidak ditemukan: {path}")
        sys.exit(1)
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        lines = [line.strip().lower() for line in f if line.strip()]
    # validasi sederhana: hanya hex
    clean = []
    for L in lines:
        if all(c in "0123456789abcdef" for c in L):
            clean.append(L)
        else:
            print(f"[!] Perhatian: baris di {path} bukan hex murni: {L[:80]}{'...' if len(L)>80 else ''}")
    return clean

def try_crack(wordlist_path: Path, keccak_targets: set, md5_targets: set, try_sha3=False, progress_every=100000):
    """Iterasi wordlist dan cocokkan MD5 + Keccak-256 (opsional SHA3-256)."""
    found_keccak = {}
    found_md5 = {}
    found_sha3 = {}
    total_targets = len(keccak_targets) + len(md5_targets)
    remain = total_targets

    if not wordlist_path.exists():
        print(f"[!] Wordlist tidak ditemukan: {wordlist_path}")
        sys.exit(1)

    start = time.time()
    processed = 0
    last_report = start

    with wordlist_path.open("rb") as wl:
        for raw in wl:
            processed += 1
            pwd = raw.rstrip(b"\r\n")
            if not pwd:
                continue

            # MD5
            md5h = hashlib.md5(pwd).hexdigest()
            if md5h in md5_targets and md5h not in found_md5:
                try:
                    found_md5[md5h] = pwd.decode("utf-8", errors="replace")
                except:
                    found_md5[md5h] = repr(pwd)
                remain -= 1
                print(f"[+] MD5 found: {md5h} -> {found_md5[md5h]}")

            # Keccak-256 (legacy Keccak)
            k = keccak.new(digest_bits=256)
            k.update(pwd)
            kk = k.hexdigest()
            if kk in keccak_targets and kk not in found_keccak:
                try:
                    found_keccak[kk] = pwd.decode("utf-8", errors="replace")
                except:
                    found_keccak[kk] = repr(pwd)
                remain -= 1
                print(f"[+] Keccak-256 found: {kk} -> {found_keccak[kk]}")

            # SHA3-256 optional (jika --try-sha3 dipilih)
            if try_sha3:
                sha3h = hashlib.sha3_256(pwd).hexdigest()
                if sha3h in keccak_targets and sha3h not in found_sha3:
                    try:
                        found_sha3[sha3h] = pwd.decode("utf-8", errors="replace")
                    except:
                        found_sha3[sha3h] = repr(pwd)
                    remain -= 1
                    print(f"[+] SHA3-256 found (matches keccak-target set): {sha3h} -> {found_sha3[sha3h]}")

            # laporkan progres tiap progress_every baris
            if processed % progress_every == 0:
                now = time.time()
                speed = processed / max(1, now - start)
                print(f"[i] Diproses: {processed:,} kata. Kecepatan ~{int(speed):,} kata/detik. Remaining targets: {remain}")

            if remain <= 0:
                break

    elapsed = time.time() - start
    print(f"[i] Selesai. Diproses {processed:,} kata dalam {elapsed:.1f}s (~{int(processed/max(1,elapsed)):,}/s).")
    return found_keccak, found_md5, found_sha3

def main():
    p = argparse.ArgumentParser(description="Cracker sederhana: Keccak-256 + MD5 (wordlist)")
    p.add_argument("-w", "--wordlist", required=True, help="Path lengkap ke wordlist, mis. C:\\path\\rockyou.txt")
    p.add_argument("--keccak", default="hash_keccak256.txt", help="File berisi Keccak-256 (satu per baris)")
    p.add_argument("--md5", default="hash_md5.txt", help="File berisi MD5 (satu per baris)")
    p.add_argument("--progress", type=int, default=100000, help="Lapor progres tiap N kata (default 100000)")
    p.add_argument("--try-sha3", action="store_true", help="Juga coba SHA3-256 (kadang hash sebenarnya SHA3)")
    args = p.parse_args()

    wordlist_path = Path(args.wordlist)
    keccak_path = Path(args.keccak)
    md5_path = Path(args.md5)

    keccak_hashes = set(load_hashes(keccak_path))
    md5_hashes = set(load_hashes(md5_path))

    print(f"[i] Target: Keccak-256={len(keccak_hashes)}, MD5={len(md5_hashes)}")
    if args.try_sha3:
        print("[i] Opsi: juga akan mencoba SHA3-256 (cek kemungkinan hash SHA3)")

    found_keccak, found_md5, found_sha3 = try_crack(
        wordlist_path,
        keccak_hashes,
        md5_hashes,
        try_sha3=args.try_sha3,
        progress_every=args.progress
    )

    print("\n=== RINGKASAN HASIL ===")
    if found_keccak:
        for h, ptxt in found_keccak.items():
            print(f"Keccak-256: {h} -> {ptxt}")
    else:
        print("Keccak-256: Tidak ada hasil (pertimbangkan wordlist lain atau coba --try-sha3)")

    if found_md5:
        for h, ptxt in found_md5.items():
            print(f"MD5: {h} -> {ptxt}")
    else:
        print("MD5: Tidak ada hasil")

    if found_sha3:
        print("\nCatatan: Hasil SHA3-256 (jika ditemukan dan cocok target Keccak):")
        for h, ptxt in found_sha3.items():
            print(f"SHA3-256: {h} -> {ptxt}")

if __name__ == "__main__":
    main()
