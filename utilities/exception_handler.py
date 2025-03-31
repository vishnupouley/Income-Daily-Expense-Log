import logging
import inspect
import traceback
from django.core.exceptions import (
    ValidationError, ObjectDoesNotExist, PermissionDenied, SuspiciousOperation
)
from django.db import DatabaseError, IntegrityError, OperationalError, DataError
from django.http import Http404
from django.utils.translation import gettext as _
from utilities.variables import ExceptionMessages  

logger = logging.getLogger(__name__)

def get_class_function_name():
    """
    Dynamically retrieves the current class name and function name.
    Returns: "ClassName.function_name" if inside a class, otherwise just "function_name".
    """
    stack = inspect.stack()
    class_name = stack[2].frame.f_locals.get("self", None).__class__.__name__ if "self" in stack[2].frame.f_locals else ""
    function_name = stack[1].function  # Get the current function name

    return f"{class_name}.{function_name}" if class_name else function_name

def handle_exception(e, extra_info=""):
    """
    Handles and logs exceptions dynamically across all service files.
    
    Args:
        e: The exception object.
        extra_info (str): Additional context information (like ID or query details).
    
    Raises:
        ValueError with an appropriate translated error message.
    """
    error_location = get_class_function_name()

    if isinstance(e, ValidationError):
        logger.exception(f"Validation error: {error_location} {extra_info}: {str(e)}")
        raise ValidationError(_(ExceptionMessages.VALIDATION_ERROR))

    elif isinstance(e, ObjectDoesNotExist):
        logger.error(f"Object not found: {error_location} {extra_info}: {str(e)}", exc_info=True)
        raise ObjectDoesNotExist(_(ExceptionMessages.NOT_FOUND))

    elif isinstance(e, PermissionDenied):
        logger.warning(f"Permission denied: {error_location} {extra_info}: {str(e)}")
        raise PermissionDenied(_(ExceptionMessages.PERMISSION_DENIED))

    elif isinstance(e, Http404):
        logger.error(f"Page not found: {error_location} {extra_info}: {str(e)}")
        raise Http404(_(ExceptionMessages.NOT_FOUND))

    elif isinstance(e, IntegrityError):
        logger.error(f"Integrity error: {error_location} {extra_info}: {str(e)}", exc_info=True)
        raise IntegrityError(_(ExceptionMessages.DATA_CONFLICT))

    elif isinstance(e, DatabaseError):
        logger.error(f"Database error: {error_location} {extra_info}: {str(e)}", exc_info=True)
        raise DatabaseError(_(ExceptionMessages.DATABASE_ERROR))

    elif isinstance(e, OperationalError):
        logger.error(f"Operational error: {error_location} {extra_info}: {str(e)}", exc_info=True)
        raise OperationalError(_(ExceptionMessages.SYSTEM_ERROR))

    elif isinstance(e, DataError):
        logger.error(f"Data error: {error_location} {extra_info}: {str(e)}", exc_info=True)
        raise DataError(_(ExceptionMessages.INVALID_FORMAT))

    elif isinstance(e, SuspiciousOperation):
        logger.warning(f"Suspicious operation detected: {error_location} {extra_info}: {str(e)}")
        raise SuspiciousOperation(_(ExceptionMessages.INVALID_REQUEST))

    elif isinstance(e, TypeError):
        logger.exception(f"Type error: {error_location} {extra_info}: {str(e)}")
        raise TypeError(_(ExceptionMessages.TYPE_MISMATCH))

    elif isinstance(e, KeyError):
        logger.exception(f"Key error: {error_location} {extra_info}: {str(e)}")
        raise KeyError(_(ExceptionMessages.MISSING_FIELDS))

    elif isinstance(e, AttributeError):
        logger.exception(f"Attribute error: {error_location} {extra_info}: {str(e)}")
        raise AttributeError(_(ExceptionMessages.ATTRIBUTE_ERROR))

    elif isinstance(e, IndexError):
        logger.exception(f"Index error: {error_location} {extra_info}: {str(e)}")
        raise IndexError(_(ExceptionMessages.INDEX_OUT_OF_RANGE))

    elif isinstance(e, TimeoutError):
        logger.error(f"Timeout error: {error_location} {extra_info}: {str(e)}", exc_info=True)
        raise TimeoutError(_(ExceptionMessages.TIMEOUT_ERROR))

    elif isinstance(e, ConnectionError):
        logger.error(f"Connection error: {error_location} {extra_info}: {str(e)}", exc_info=True)
        raise ConnectionError(_(ExceptionMessages.CONNECTION_ERROR))

    elif isinstance(e, FileNotFoundError):
        logger.error(f"File not found: {error_location} {extra_info}: {str(e)}", exc_info=True)
        raise FileNotFoundError(_(ExceptionMessages.FILE_NOT_FOUND))

    elif isinstance(e, IOError):
        logger.error(f"Input/output error: {error_location} {extra_info}: {str(e)}", exc_info=True)
        raise IOError(_(ExceptionMessages.REQUEST_FAILED))

    elif isinstance(e, MemoryError):
        logger.critical(f"Memory error: {error_location} {extra_info}: {str(e)}", exc_info=True)
        raise MemoryError(_(ExceptionMessages.SYSTEM_ERROR))

    elif isinstance(e, ValueError):
        logger.exception(f"Value error: {error_location} {extra_info}: {str(e)}")
        raise e

    else:
        logger.critical(f"Unexpected error: {error_location} {extra_info}: {str(e)}\n{traceback.format_exc()}")
        raise ValueError(_(ExceptionMessages.EXCEPTION_ERROR))
