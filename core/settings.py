"""Application settings and shared constants."""

from functools import lru_cache
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "HVAC Factory Ops"
    database_url: str = Field("sqlite:///./hvac_factory_ops.db", env="DATABASE_URL")
    steel_density_kg_m3: float = Field(7850.0, env="STEEL_DENSITY_KG_M3")
    waste_factor: float = Field(0.0, env="WASTE_FACTOR")

    class Config:
        env_file = ".env"
        case_sensitive = False

    @validator("waste_factor")
    def validate_waste_factor(cls, v: float) -> float:
        if v < 0:
            raise ValueError("waste_factor must be zero or positive")
        return v


def mm_to_m(value_mm: float) -> float:
    return value_mm / 1000.0


def mm2_to_m2(value_mm2: float) -> float:
    return value_mm2 / 1_000_000.0


@lru_cache
def get_settings() -> Settings:
    return Settings()


