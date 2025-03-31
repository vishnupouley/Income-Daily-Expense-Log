from typing import Dict
from expenses_log.services.base_list_service import BaseListService
from expenses_log.services.base_service import BaseService
from utilities.exception_handler import handle_exception
from schema.list_schema import ListServiceConfig
from month_log.models import MonthLog


class MonthLogService:
    
    @staticmethod
    async def get_list_data(config_data: Dict) -> Dict:

        config_data["app"] = "month_log"
        config_data["model"] = "MonthLog"
        config = ListServiceConfig(**config_data)
        return await BaseListService.process_list_service(config)
    
