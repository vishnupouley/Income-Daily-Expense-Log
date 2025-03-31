from asgiref.sync import sync_to_async

from utilities.exception_handler import handle_exception
# Service Classes
class BaseService:
    @staticmethod 
    async def get_valid_items(model_class, schema_class):
        """
        Generic method to get all valid  items for any model
        """
        try:

            items = await sync_to_async(list)(model_class.objects.all()) # issue of synct_to_async due to select and prefetch relations
            return [schema_class.model_validate(item) for item in items]
        
        except Exception as e:
            handle_exception(e)
        
    @staticmethod
    async def get_by_id(model_class, schema_class, id: int):
        """
        Generic method to get an item by ID for any model
        """
        try:

            item = await model_class.objects.aget(id=id)
            return schema_class.model_validate(item)
        
        except Exception as e:
            handle_exception(e)
            
    @staticmethod
    async def get_or_create_data(model_class, value:str):
        """
        get the field name also from the args
        """
        exists = await model_class.objects.filter(name=value).aexists()
        if not exists:
            obj = await model_class.objects.acreate(name=value)
        else:
            obj = await model_class.objects.aget(name=value)
        
        return obj