from enum import Enum


class ProductType(str, Enum):
    RECTANGULAR_DUCT = "RECTANGULAR_DUCT"
    AHU_CABINET = "AHU_CABINET"
    FITTING_DUCT = "FITTING_DUCT"


