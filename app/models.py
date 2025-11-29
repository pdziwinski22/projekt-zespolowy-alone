from dataclasses import dataclass


@dataclass
class OperationLog:
    original_filename: str
    result_filename: str
    effect: str
    ai_description: str
    tokens_in: int
    tokens_out: int
    created_at: str
