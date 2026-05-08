from fastapi import status

HTTP_OK = status.HTTP_200_OK
HTTP_CREATED = status.HTTP_201_CREATED
HTTP_NO_CONTENT = status.HTTP_204_NO_CONTENT

HTTP_BAD_REQUEST = status.HTTP_400_BAD_REQUEST
HTTP_UNAUTHORIZED = status.HTTP_401_UNAUTHORIZED
HTTP_FORBIDDEN = status.HTTP_403_FORBIDDEN
HTTP_NOT_FOUND = status.HTTP_404_NOT_FOUND
HTTP_CONFLICT = status.HTTP_409_CONFLICT
HTTP_UNPROCESSABLE_ENTITY = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)

AUTHENTICATION_ERROR_RESPONSES = {
    HTTP_UNAUTHORIZED: {"description": "Missing or invalid bearer token"},
}

REGISTER_ERROR_RESPONSES = {
    HTTP_CONFLICT: {"description": "User with the same email or nickname exists"},
    HTTP_UNPROCESSABLE_ENTITY: {"description": "Invalid request payload"},
}

LOGIN_ERROR_RESPONSES = {
    HTTP_UNAUTHORIZED: {"description": "Invalid email or password"},
    HTTP_UNPROCESSABLE_ENTITY: {"description": "Invalid request payload"},
}
