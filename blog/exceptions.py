from rest_framework import status
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        return response

    error_data = response.data

    if response.status_code == status.HTTP_400_BAD_REQUEST:
        response.data = {
            "success": False,
            "status_code": response.status_code,
            "message": "Validation error.",
            "errors": error_data,
        }
        return response

    detail = error_data
    if isinstance(error_data, dict):
        detail = error_data.get("detail", error_data)

    message = detail
    if not isinstance(detail, (dict, list)):
        message = str(detail)

    response.data = {
        "success": False,
        "status_code": response.status_code,
        "message": message,
    }
    return response
