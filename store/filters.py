from django_filters import rest_framework  as filters

from django.db.models import Q
from . import models


class ProductFilter(filters.FilterSet):
    price = filters.RangeFilter(field_name="unit_price")
    name = filters.CharFilter(field_name="name", lookup_expr="icontains")
    categories = filters.ModelMultipleChoiceFilter(
        field_name="category", queryset=models.Category.objects.all()
    )
    created_created = filters.DateTimeFilter(field_name="datetime_created", lookup_expr="lte")
    # inventory_levels = filters.AllValuesMultipleFilter(field_name="inventory")
    # ordering = filters.OrderingFilter(fields=("name", "unit_price",'inventory'))
    ordering = filters.OrderingFilter(
        fields=["name", "unit_price", "inventory"]
    )
    class Meta:
        model = models.Product
        fields = {
            "inventory": ["gt", "lt"],
        }
    
  