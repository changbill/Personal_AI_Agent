"""Korean place names resolved by code, not by the geocoding API.

Open-Meteo's geocoding index is romanized: `language=ko` translates the labels it
returns but not the names it searches. "서울" and "제주" therefore return nothing, and
"대전" returns a village of the same name in Jeollanam-do — a wrong answer the agent
would state as fact. Since the user asks in Korean, the mapping from a Korean place name
to a coordinate is a rule the application owns rather than a question it asks a service.

Coordinates were read from Open-Meteo's own geocoding results for the romanized name,
filtered to the matching administrative region, so the forecast grid stays the one the
API would have picked for the correct city.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Place:
    name: str
    latitude: float
    longitude: float


# Suffixes a user may attach to a bare name. Stripped only when the remainder is itself
# a known name, so "대구" is never cut down to "대" by its trailing 구.
_SUFFIXES = (
    "특별자치도",
    "특별자치시",
    "특별시",
    "광역시",
    "시",
    "군",
    "구",
    "도",
)

# 17 시·도 and the larger 시. Anything smaller falls through to the geocoding API, whose
# index handles fine-grained names well enough once a KR result is preferred.
KOREAN_PLACES: dict[str, tuple[float, float]] = {
    "서울": (37.5660, 126.9784),
    "부산": (35.1017, 129.0300),
    "대구": (35.8703, 128.5911),
    "인천": (37.4565, 126.7052),
    "광주": (35.1547, 126.9156),
    "대전": (36.3491, 127.3849),
    "울산": (35.5372, 129.3167),
    "세종": (36.5924, 127.2922),
    "수원": (37.2911, 127.0089),
    "성남": (37.4386, 127.1378),
    "용인": (37.2969, 127.0804),
    "고양": (37.6564, 126.8350),
    "부천": (37.4989, 126.7831),
    "안산": (37.3236, 126.8219),
    "안양": (37.3925, 126.9269),
    "화성": (37.2068, 126.8169),
    "평택": (36.9947, 127.0889),
    "의정부": (37.7415, 127.0474),
    "남양주": (37.6367, 127.2142),
    "파주": (37.8328, 126.8169),
    "김포": (37.6236, 126.7142),
    "춘천": (37.8747, 127.7342),
    "원주": (37.3514, 127.9453),
    "강릉": (37.7527, 128.8724),
    "속초": (38.2070, 128.5918),
    "청주": (36.6372, 127.4897),
    "충주": (36.9767, 127.9287),
    "천안": (36.8065, 127.1522),
    "아산": (36.7836, 127.0042),
    "전주": (35.8219, 127.1489),
    "군산": (35.9786, 126.7114),
    "익산": (35.9439, 126.9544),
    "목포": (34.8128, 126.3918),
    "여수": (34.7606, 127.6621),
    "순천": (34.9505, 127.4878),
    "포항": (36.0292, 129.3648),
    "경주": (35.8428, 129.2117),
    "구미": (36.1136, 128.3360),
    "안동": (36.5664, 128.7227),
    "창원": (35.2281, 128.6811),
    "김해": (35.2342, 128.8811),
    "진주": (35.1928, 128.0847),
    "양산": (35.3420, 129.0336),
    "거제": (34.8138, 128.7056),
    "통영": (34.8496, 128.4278),
    "제주": (33.5097, 126.5219),
    "서귀포": (33.2533, 126.5618),
}

# A 도 covers too much area to have one temperature, so it resolves to the city the
# province is administered from. The answer names that city, so the user can see which
# point was measured instead of assuming the whole province was.
_PROVINCE_SEATS = {
    "경기": "수원",
    "강원": "춘천",
    "충청북": "청주",
    "충북": "청주",
    "충청남": "천안",
    "충남": "천안",
    "전라북": "전주",
    "전북": "전주",
    "전라남": "목포",
    "전남": "목포",
    "경상북": "안동",
    "경북": "안동",
    "경상남": "창원",
    "경남": "창원",
}


def normalize(query: str) -> str:
    """Drop the whitespace users put inside place names ("서울 특별시")."""
    return "".join(query.split())


def lookup(query: str) -> Place | None:
    """Resolve a Korean place name to a coordinate, or return None to fall through."""
    name = normalize(query)
    if not name:
        return None

    resolved = _resolve(name)
    if resolved is None:
        return None
    latitude, longitude = KOREAN_PLACES[resolved]
    return Place(name=resolved, latitude=latitude, longitude=longitude)


def _resolve(name: str) -> str | None:
    if name in KOREAN_PLACES:
        return name
    if name in _PROVINCE_SEATS:
        return _PROVINCE_SEATS[name]

    for suffix in _SUFFIXES:
        if not name.endswith(suffix):
            continue
        stem = name[: -len(suffix)]
        if stem in KOREAN_PLACES:
            return stem
        if stem in _PROVINCE_SEATS:
            return _PROVINCE_SEATS[stem]
    return None
