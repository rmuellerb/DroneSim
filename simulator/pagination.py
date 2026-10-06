from rest_framework.pagination import LimitOffsetPagination

class CappedLimitOffsetPagination(LimitOffsetPagination):
    max_limit = 1000
