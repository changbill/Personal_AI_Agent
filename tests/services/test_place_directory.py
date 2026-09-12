import pytest

from app.services.place_directory import KOREAN_PLACES, lookup

pytestmark = pytest.mark.unit


def test_a_bare_city_name_resolves_without_the_geocoding_api() -> None:
    place = lookup("서울")

    assert place is not None
    assert place.name == "서울"
    assert place.latitude == pytest.approx(37.5660)
    assert place.longitude == pytest.approx(126.9784)


@pytest.mark.parametrize(
    "query",
    ["서울시", "서울특별시", "서울 특별시", " 서울 "],
)
def test_the_suffixes_users_attach_resolve_to_the_same_city(query: str) -> None:
    place = lookup(query)

    assert place is not None
    assert place.name == "서울"


def test_a_name_ending_in_a_suffix_letter_is_not_cut_apart() -> None:
    place = lookup("대구")

    assert place is not None
    assert place.name == "대구"


def test_a_province_resolves_to_the_city_it_is_administered_from() -> None:
    assert lookup("경기도") is not None
    assert lookup("경기도").name == "수원"
    assert lookup("경남").name == "창원"
    assert lookup("충북").name == "청주"


def test_an_unknown_place_falls_through_to_the_caller() -> None:
    assert lookup("도쿄") is None
    assert lookup("Seoul") is None
    assert lookup("없는도시") is None


def test_an_empty_query_falls_through() -> None:
    assert lookup("") is None
    assert lookup("   ") is None


def test_every_listed_coordinate_sits_inside_korea() -> None:
    for name, (latitude, longitude) in KOREAN_PLACES.items():
        assert 33.0 <= latitude <= 38.7, name
        assert 124.5 <= longitude <= 131.0, name
