from datetime import datetime, date

from QM.basemodel import BaseQuantitativeModel


class BaseTuShareModel(BaseQuantitativeModel):
    def __init__(self, index_list: list, now: str | datetime | date, top_count: int):
        super().__init__(index_list, now, top_count)

