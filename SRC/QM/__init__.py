# coding = utf - 8
# from __future__ import unicode_literals, print_function, absolute_import, annotations

# Let users know if they're missing any of our hard dependencies
_hard_dependencies = ("pandas", "numpy")
_missing_dependencies = []

for _dependency in _hard_dependencies:
    try:
        __import__(_dependency)
    except ImportError as _e:  # pragma: no cover
        _missing_dependencies.append(f"{_dependency}: {_e}")

if _missing_dependencies:  # pragma: no cover
    raise ImportError(
        "Unable to import required dependencies:\n" + "\n".join(_missing_dependencies)
    )
del _hard_dependencies, _dependency, _missing_dependencies

from QM.basemodel import (
    OrderOp,
    AbstractQuantitativeModel,
    BaseQuantitativeModel,
)

from QM.gm import (
    BaseGMModel,
    GrowthModel,
    HowardRothmanModel,
    MACDModel,
    RSRSModel,
    VIPAModel,
    DefensiveStrategyModel,
    SVMModel,
)

from QM.tushare import (
    BaseTuShareModel,
)

# Use __all__ to let type checkers know what is part of the public API.
# QM is a py.typed library: the public API is determined
__all__ = [
    "OrderOp",
    "AbstractQuantitativeModel",
    "BaseQuantitativeModel",
    # gm model
    "BaseGMModel",
    "GrowthModel",
    "HowardRothmanModel",
    "MACDModel",
    "RSRSModel",
    "VIPAModel",
    "DefensiveStrategyModel",
    "SVMModel",
    # tushare model
    "BaseTuShareModel",
]

# from QM.basemodel.OrderOp import OrderOp
# from QM.basemodel.AbstractQuantitativeModel import AbstractQuantitativeModel
# from QM.basemodel.BaseQuantitativeModel import BaseQuantitativeModel
# from QM.gm.GMQuantitativeModel import GMQuantitativeModel
# from QM.gm.GrowthModel import GrowthModel
# from QM.gm.HowardRothmanModel import HowardRothmanModel
# from QM.gm.MACDModel import MACDModel
