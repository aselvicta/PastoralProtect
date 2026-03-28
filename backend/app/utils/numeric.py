def ndvi_to_micro(value: float) -> int:
    return int(round(float(value) * 1_000_000))


def ndvi_from_micro(micro: int) -> float:
    return micro / 1_000_000
