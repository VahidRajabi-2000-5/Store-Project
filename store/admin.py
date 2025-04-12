from django.contrib import admin, messages
from django.db.models import Count
from django.utils.html import format_html
from django.urls import reverse
from django.utils.http import urlencode

from . import models


@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "title",
        "top_product",
    ]
    list_per_page = 5
    list_editable = [
        "top_product",
    ]
    search_fields = [
        "title",
    ]
    autocomplete_fields = [
        "top_product",
    ]


@admin.register(models.Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "discount",
        "description",
    ]
    list_per_page = 5
    list_editable = [
        "discount",
    ]


class InventoryFilter(admin.SimpleListFilter):
    LESS_THAN_20 = "<=20"
    BETWEEN_20_AND_50 = "(21,49)"
    MORE_THAN_50 = ">=50"
    title = "Critical Inventory Status"
    parameter_name = "Inventory"

    def lookups(self, request, model_admin):
        return [
            (InventoryFilter.LESS_THAN_20, "Low"),
            (InventoryFilter.BETWEEN_20_AND_50, "Medium"),
            (InventoryFilter.MORE_THAN_50, "High"),
        ]

    def queryset(self, request, queryset):
        if self.value() == InventoryFilter.LESS_THAN_20:
            return queryset.filter(inventory__lte=20)
        if self.value() == InventoryFilter.BETWEEN_20_AND_50:
            return queryset.filter(inventory__range=(21, 49))
        if self.value() == InventoryFilter.MORE_THAN_50:
            return queryset.filter(inventory__gte=50)


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "num_of_comments",
        "name",
        "product_category",
        "unit_price",
        "inventory",
        "inventory_status",
        "datetime_created",
        "datetime_modified",
    ]
    list_per_page = 10
    list_editable = [
        "unit_price",
    ]
    ordering = [
        "-datetime_created",
    ]

    list_select_related = [
        "category",
    ]
    list_filter = [
        "datetime_created",
        InventoryFilter,
    ]
    list_display_links = [
        "id",
        "name",
    ]
    actions = [
        "clear_inventory",
    ]
    search_fields = [
        "name",
    ]
    prepopulated_fields = {
        "slug": [
            "name",
        ]
    }
    autocomplete_fields = [
        "category",
    ]

    def inventory_status(self, product: models.Product):
        if product.inventory <= 20:
            return "Low"
        if product.inventory >= 50:
            return "High"
        return "Medium"

    @admin.display(
        ordering="category__title",
    )
    def product_category(self, product: models.Product):
        return product.category.title

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .prefetch_related(
                "comments",
                "category",
            )
            .annotate(comments_count=Count("comments"))
        )

    @admin.display(description="# comment", ordering="comments_count")
    def num_of_comments(self, product: models.Product):
        # http://127.0.0.1:8000/admin/store/comment/?product__id=553
        url = (
            reverse("admin:store_comment_changelist")
            + "?"
            + urlencode(
                {
                    "product__id": product.id,
                }
            )
        )
        return format_html("<a href='{}'>{}</a>", url, product.comments_count)
        # return product.comments_count

    @admin.action(description="Clear Inventory")
    def clear_inventory(self, request, queryset):
        update_count = queryset.update(inventory=0)
        self.message_user(
            request,
            f"{update_count} of products inventory cleared to zero.",
            messages.SUCCESS,
        )


@admin.register(models.Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "birth_date",
        "full_name",
        "email",
        "phone_number",
    ]
    list_per_page = 5
    list_editable = [
        "birth_date",
        "phone_number",
    ]
    list_select_related = [
        "user",
    ]
    search_fields = [
        "user__last_name__istartswith",
        "user__first_name__istartswith",
    ]

    
    def email(self, customer: models.Customer):
        return customer.user.email

    # @admin.display(
    #     ordering="user__last_name",
    # )
    # def full_name(self, customer: models.Customer):
    #     return customer.full_name


@admin.register(models.Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = [
        "customer",
        "province",
        "city",
        "street",
    ]
    list_per_page = 5
    list_editable = [
        "province",
        "city",
        "street",
    ]


@admin.register(models.Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "product",
        "name",
        "body",
        "status",
        "datetime_created",
    ]
    list_per_page = 2
    list_editable = [
        "status",
    ]
    autocomplete_fields = [
        "product",
    ]


class OrderItemInline(admin.TabularInline):
    model = models.OrderItem
    fields = [
        "product",
        "quantity",
        "unit_price",
    ]
    extra = 1
    min_num = 1
    max_num = 20


@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "customer",
        "status",
        "datetime_created",
        "num_of_items",
    ]
    list_per_page = 5
    list_editable = [
        "status",
    ]
    list_select_related = [
        "customer__user",
    ]
    inlines = [
        OrderItemInline,
    ]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .prefetch_related("items")
            .annotate(items_count=Count("items"))
        )

    @admin.display(
        description="# items",
        ordering="items_count",
    )
    def num_of_items(self, order: models.Order):
        return order.items_count


@admin.register(models.OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "order",
        "product",
        "quantity",
        "unit_price",
    ]
    list_per_page = 5
    list_editable = [
        "quantity",
        "unit_price",
        "order",
    ]
    list_select_related = [
        "order",
        "product",
    ]
    autocomplete_fields = ["product"]


class CartItemInline(admin.TabularInline):
    model = models.CartItem
    fields = [
        "product",
        "quantity",
    ]
    extra = 1
    min_num = 1
    max_num = 20


@admin.register(models.Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "created_at",
    ]
    list_per_page = 10
    inlines = [
        CartItemInline,
    ]
    ordering = [
        "-created_at",
    ]


@admin.register(models.CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "cart",
        "product",
        "quantity",
    ]
    list_per_page = 5
    list_editable = [
        "quantity",
    ]


# admin.site.register(models.Product, ProductAdmin)
