def safe_trunc(s: str, n: int = 8) -> str:
    return (s[:n] + "...") if s and len(s) > n else s
