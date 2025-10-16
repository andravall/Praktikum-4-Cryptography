from itertools import product

# === Konversi dan operasi dasar ===
def to_bytes(hexstr):
    s = hexstr.strip().replace(" ", "").replace("\n", "")
    if len(s) % 2:
        raise ValueError("Jumlah digit hex harus genap.")
    return bytes.fromhex(s)

def xor_bytes(a, b):
    return bytes(x ^ y for x, y in zip(a, b))

def printable(bs):
    return all(9 == b or 10 == b or 13 == b or 32 <= b <= 126 for b in bs)

# === Data input dari soal ===
k1    = to_bytes("3c3f0193af37d2ebbc50cc6b91d27cf61197")
k21   = to_bytes("ff76edcad455b6881b92f726987cbf30c68c")
k23   = to_bytes("611568312c102d4d921f26199d39fe973118")
k1234 = to_bytes("91ec5a6fa8a12f908f161850c591459c3887")
f45   = to_bytes("0269dd12fe3435ea63f63aef17f8362cdba8")

# === Pulihkan KEY2, KEY3, KEY4 ===
key2 = xor_bytes(k21, k1)
key3 = xor_bytes(k23, key2)
key4 = xor_bytes(xor_bytes(xor_bytes(k1234, k1), key3), key2)

# === Hitung FLAG ^ KEY5 ===
fx = xor_bytes(f45, key4)

# === Cari KEY5 berdasarkan crib cry{ ===
crib = b"cry{"
candidates = []

for offset in range(4):
    if len(fx) < offset + 4:
        continue
    # Ambil bagian fx untuk menentukan KEY5 awal
    frag = fx[offset:offset+4]
    k5_guess = bytes(x ^ y for x, y in zip(frag, crib))
    # Bentuk KEY5 berulang
    key_full = bytes(k5_guess[(i - offset) % 4] for i in range(len(fx)))
    flag_try = xor_bytes(fx, key_full)
    candidates.append((offset, k5_guess, flag_try))

# === Penilaian hasil ===
def score(bs):
    val = 0
    if printable(bs): val += 2
    text = bs.decode(errors="ignore")
    if "cry{" in text: val += 3
    if "}" in text: val += 1
    if text.startswith("cry{"): val += 2
    return val

best = max(candidates, key=lambda c: score(c[2]))

# === Cetak hasil seperti contoh teman ===
print("Jumlah kandidat:", len(candidates))
for off, k5, fl in candidates:
    txt = fl.decode(errors="replace")
    print(f"\n[Offset {off}] KEY5={k5.hex()}  printable={printable(fl)}")
    print(txt)

print("\n=== Pilihan terbaik ===")
print("Offset:", best[0])
print("KEY5 (4 bytes):", best[1].hex())
print("FLAG:", best[2].decode(errors='replace'))