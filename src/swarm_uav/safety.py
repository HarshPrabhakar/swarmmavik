"""Mission preflight checks for a simple geographic operating boundary."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class Point:
    latitude_deg: float
    longitude_deg: float
    relative_altitude_m: float


@dataclass(frozen=True)
class Geofence:
    """Axis-aligned demo fence; coordinates are inclusive and altitude is relative."""

    min_latitude_deg: float
    max_latitude_deg: float
    min_longitude_deg: float
    max_longitude_deg: float
    min_altitude_m: float
    max_altitude_m: float

    def __post_init__(self) -> None:
        bounds = (
            self.min_latitude_deg,
            self.max_latitude_deg,
            self.min_longitude_deg,
            self.max_longitude_deg,
            self.min_altitude_m,
            self.max_altitude_m,
        )
        if not all(isfinite(value) for value in bounds):
            raise ValueError("geofence bounds must be finite numbers")
        if not -90 <= self.min_latitude_deg < self.max_latitude_deg <= 90:
            raise ValueError("latitude bounds must be ordered within [-90, 90]")
        if not -180 <= self.min_longitude_deg < self.max_longitude_deg <= 180:
            raise ValueError("longitude bounds must be ordered within [-180, 180]")
        if self.min_latitude_deg >= self.max_latitude_deg:
            raise ValueError("minimum latitude must be less than maximum latitude")
        if self.min_longitude_deg >= self.max_longitude_deg:
            raise ValueError("minimum longitude must be less than maximum longitude")
        if self.min_altitude_m >= self.max_altitude_m:
            raise ValueError("minimum altitude must be less than maximum altitude")

    def contains(self, point: Point) -> bool:
        coordinates = (point.latitude_deg, point.longitude_deg, point.relative_altitude_m)
        if not all(isfinite(value) for value in coordinates):
            return False
        return (
            -90 <= point.latitude_deg <= 90
            and -180 <= point.longitude_deg <= 180
            and self.min_latitude_deg <= point.latitude_deg <= self.max_latitude_deg
            and self.min_longitude_deg <= point.longitude_deg <= self.max_longitude_deg
            and self.min_altitude_m <= point.relative_altitude_m <= self.max_altitude_m
        )

    def validate_route(self, points: list[Point]) -> None:
        if not points:
            raise ValueError("mission route must contain at least one point")
        for index, point in enumerate(points, start=1):
            if not self.contains(point):
                raise ValueError(f"route point {index} is outside the configured geofence")
