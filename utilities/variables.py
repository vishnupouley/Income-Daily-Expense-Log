# utilities/variable.py

from django.utils.translation import gettext as _

class SuccessMessages:
    LOGIN_SUCCESS = _("Login successful!")
    WELCOME = _("Welcome to the dashboard!")
    ADD_MSG = _("Data Added Successfully")
    EDIT_MSG = _("Data Update Successfully")
    DELETE_MSG = _("Data Deleted Successfully")
    ACTIVATION_MSG = _("Activation link sent successfully")
    PASSWORD_UPDATED = _("Password has been updated successfully")

class ErrorMessages:
    LOGIN_FAILED = _("Invalid username or password.")
    METHOD_NOT_ALLOWED = _("Method not allowed")
    ERROR = _("Application Error.")
    ALREADY_EXISTS = _("{name} already exists.")
    DOES_NOT_EXISTS = _("Record does not exists.")
    EMAIL_FAILED = _("Failed to send activation email")
    FILE_UPLOAD_FAILED = _("file is not uploaded")
    TOKEN_EXPIRED = _("The password reset link is invalid or has expired. Please request a new one.")
    EMAIL_AND_URL_REQUIRED = _("Email and URL are required")
    INVALID_FORMATS = _("Only JPEG, PNG and GIF images are allowed")
    INVALID_FILE_SIZE = _("File size too large. Maximum size is 5MB")
    INVALID_ID = _("Invalid user ID")
    INVALID_TOKEN = _("Invalid Token")

class ExceptionMessages:    
    VALIDATION_ERROR = _("Invalid data provided. Please check your input.")
    DATABASE_ERROR = _("An unexpected error occurred. Please try again later.")
    EXCEPTION_ERROR = _("Something went wrong. Please contact support.")
    DATA_CONFLICT = _("Data conflict detected. Please check your input.")
    INVALID_FORMAT = _("Invalid data format. Please check and try again.")
    SYSTEM_ERROR = _("System error. Please try again later.")
    INTERNAL_ERROR = _("Internal system error. Please contact support.")
    NOT_FOUND = _("Requested data not found.")
    MULTIPLE_RECORDS_FOUND = _("Unexpected data conflict. Please contact support.")
    PERMISSION_DENIED = _("You do not have permission to perform this action.")
    INVALID_REQUEST = _("Invalid request. Please try again.")
    ATTRIBUTE_ERROR = _("A system error occurred. Please contact support.")
    MISSING_FIELDS = _("Invalid request. Required fields are missing.")
    TYPE_MISMATCH = _("Invalid data type. Please check your input.")
    INDEX_OUT_OF_RANGE = _("Invalid request. Please check your data.")
    TIMEOUT_ERROR = _("The request took too long. Please try again later.")
    INVALID_JSON = _("Invalid JSON format. Please check your input.")
    CONNECTION_ERROR = _("Network error. Please check your internet connection and try again.")
    REQUEST_FAILED = _("Failed to process the request. Please try again later.")
    
    # Newly Added Exceptions
    UNAUTHORIZED_ACCESS = _("Unauthorized access detected. Please log in and try again.")  # UnauthorizedError
    SESSION_EXPIRED = _("Your session has expired. Please log in again.")  # SessionExpiredError
    SERVICE_UNAVAILABLE = _("The service is currently unavailable. Please try again later.")  # ServiceUnavailableError
    DEPENDENCY_FAILURE = _("A required service is not responding. Please try again later.")  # ExternalServiceError
    INVALID_CREDENTIALS = _("Incorrect username or password. Please try again.")  # AuthenticationError
    FILE_NOT_FOUND = _("The requested file could not be found.")  # FileNotFoundError
    FILE_TOO_LARGE = _("The uploaded file is too large. Please upload a smaller file.")  # LargeFileError
    UNSUPPORTED_MEDIA_TYPE = _("Unsupported file format. Please check the allowed formats.")  # UnsupportedFileTypeError
    RATE_LIMIT_EXCEEDED = _("Too many requests. Please slow down and try again later.")  # RateLimitExceededError
    OPERATION_NOT_ALLOWED = _("This operation is not allowed. Please contact support.")  # OperationNotAllowedError
    PARSING_ERROR = _("Failed to process the request due to incorrect formatting.")  # ParsingError
    RESOURCE_LOCKED = _("The requested resource is currently in use. Please try again later.")  # ResourceLockedError
    INVALID_SESSION = _("Invalid or expired session. Please log in again.")  # InvalidSessionError
    # Role related exceptions
    ROLE_NOT_FOUND = _("Requested role not found.")  # RoleNotFoundError
    INVALID_ROLE_ID = _("Invalid role ID format.")  # InvalidRoleIDError
    ROLE_NAME_REQUIRED = _("Invalid request. Role name is required.")  # RoleNameRequiredError
    FAILED_TO_DELETE_ROLE = _("Failed to delete role.")  # FailedToDeleteError
