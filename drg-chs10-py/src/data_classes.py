from dataclasses import dataclass, field
from typing import List


@dataclass
class Diagnosis:
    diag_id: int
    diag_code: str
    diag_name: str

@dataclass
class Surgery:
    oper_id: int
    oper_code: str
    oper_name: str

@dataclass
class Patient:
    vid: str
    gender: str
    age: int
    admit_date: str
    dis_date: str
    total_cost: float
    birth_weight: float
    diagnosis: List[Diagnosis] = field(default_factory=list)
    surgery: List[Surgery] = field(default_factory=list)

@dataclass
class MDC:
    code: str
    name: str
    based: str

@dataclass
class ADRG:
    code: str
    name: str
    based: str

@dataclass
class DRG:
    code: str
    name: str
    based: str

