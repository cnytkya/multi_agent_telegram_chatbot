import hashlib
import hmac

# Bu salt'ı gizli tut — repo'da kalabilir çünkü key üretmek için salt + gizli seed gerekir
_SALT = "mатб-2026-cnytkya"

# Geçerli key listesi (generate_key.py ile üretilen key'lerin hash'leri)
# Yeni key eklemek için: generate_key.py çalıştır, çıktıyı buraya ekle
_VALID_KEY_HASHES: set[str] = {
    "1d9058588b36418289f05ed80933fbf70e2a5cd1a539e168be027ebe81038ff6",  # cnytkya
}


def _hash_key(key: str) -> str:
    return hashlib.sha256(key.strip().encode()).hexdigest()


def validate_license(key: str | None) -> None:
    if not key:
        raise SystemExit(
            "\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "  LICENSE_KEY bulunamadı.\n"
            "  Kullanmak için: github.com/cnytkya ile iletişime geç\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        )

    key_hash = _hash_key(key.strip())

    if key_hash not in _VALID_KEY_HASHES:
        raise SystemExit(
            "\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "  Geçersiz LICENSE_KEY.\n"
            "  Kullanmak için: github.com/cnytkya ile iletişime geç\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        )
