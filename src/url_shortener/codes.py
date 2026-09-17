import re
import secrets

CODE_LENGTH = 7
CODE_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
CODE_PATTERN = re.compile(r"^[A-Za-z0-9]{7}$")


def generate_code() -> str:
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


def is_valid_shape(code: str) -> bool:
    return bool(CODE_PATTERN.fullmatch(code))
