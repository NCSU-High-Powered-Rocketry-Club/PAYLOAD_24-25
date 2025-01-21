"""Module for describing the data packet for the logger to log"""

from typing import Required, TypedDict


class LoggedDataPacket(TypedDict, total=False):  # total=False means all fields are NotRequired
    """
    Represents a collection of all data that the logger can log in a line. Not every field will be
    filled in every packet.
    """

    state: Required[str]

    # IMU Data Packet Fields
    timestamp: int
    voltage: float | None
    ambientTemperature: float | None
    ambientPressure: float | None
    pressureAlt: float | None
    estCompensatedAccelX: float | None
    estCompensatedAccelY: float | None
    estCompensatedAccelZ: float | None
    estAngularRateX: float | None
    estAngularRateY: float | None
    estAngularRateZ: float | None
    magneticFieldX: float | None
    magneticFieldY: float | None
    magneticFieldZ: float | None
    estOrientQuaternionW: float | None
    estOrientQuaternionX: float | None
    estOrientQuaternionY: float | None
    estOrientQuaternionZ: float | None
    gpsLatitude: float | None
    gpsLongitude: float | None
    gpsAltitude: float | None

    # Processed Data Packet Fields
    current_altitude: float | None
    vertical_velocity: float | None
    vertical_acceleration: float | None
