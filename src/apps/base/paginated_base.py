from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination settings for the API results."""

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 100
