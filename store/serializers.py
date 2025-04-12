from decimal import Decimal
from rest_framework import serializers
from django.utils.text import slugify
from django.db.models import F, Sum
from django.shortcuts import get_object_or_404
from django.db import transaction

from . import models


class CategorySerializer(serializers.ModelSerializer):
    num_of_product = serializers.IntegerField(read_only=True)

    class Meta:
        model = models.Category
        fields = [
            "id",
            "title",
            "description",
            "num_of_product",
        ]

    # num_of_product = serializers.SerializerMethodField()
    # def get_num_of_product(self, category: models.Category):
    #     return getattr(category, 'num_of_product', 0)


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Product
        fields = [
            "id",
            "name",
            "unit_price",
            "unit_price_after_tax",
            "inventory",
            "category",
            "description",
        ]

    unit_price_after_tax = serializers.SerializerMethodField()
    category = serializers.HyperlinkedRelatedField(
        queryset=models.Category.objects.all(),
        view_name="category-detail",
    )

    def get_unit_price_after_tax(self, product: models.Product):
        return round(product.unit_price * Decimal(1.09), 2)

    def validate(self, data):
        name = data.get("name", "")
        if len(name) < 6:
            raise serializers.ValidationError(
                {"name": "Product name length should be at least 6 characters."}
            )
        return data

    #  کار پایین رو به سیگنال دادم انجام بده
    # def create(self, validated_data):
    #     product = models.Product(**validated_data)
    #     product.slug = slugify(product.name)
    #     product.save()
    #     return product


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Comment
        fields = [
            "id",
            "name",
            "body",
            "datetime_created",
        ]

    def create(self, validated_data):
        product_pk = self.context["product_pk"]
        return models.Comment.objects.create(product_id=product_pk, **validated_data)


class CartProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Product
        fields = [
            "id",
            "name",
            "unit_price",
        ]


class UpdateCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CartItem
        fields = [
            "quantity",
        ]


class AddCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CartItem
        fields = [
            "id",
            "product",
            "quantity",
        ]

    def create(self, validated_data):
        cart_pk = self.context["cart_pk"]
        product = validated_data["product"]
        quantity = validated_data["quantity"]
        try:
            cart_item = models.CartItem.objects.get(
                cart_id=cart_pk, product_id=product.id
            )
            cart_item.quantity += quantity
            cart_item.save()
        except models.CartItem.DoesNotExist:
            cart_item = models.CartItem.objects.create(
                cart_id=cart_pk, **validated_data
            )
        self.instance = cart_item
        return cart_item


class CartItemSerializer(serializers.ModelSerializer):
    product = CartProductSerializer()
    item_total = serializers.SerializerMethodField()

    class Meta:
        model = models.CartItem
        fields = [
            "id",
            "product",
            "quantity",
            "item_total",
        ]

    def get_item_total(self, cart_item: models.CartItem):
        return cart_item.quantity * cart_item.product.unit_price


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price_cart = serializers.SerializerMethodField()

    class Meta:
        model = models.Cart
        fields = [
            "id",
            "items",
            "total_price_cart",
        ]
        read_only_fields = [
            "id",
        ]

    def get_total_price_cart(self, cart: models.Cart):
        return sum(
            [item.quantity * item.product.unit_price for item in cart.items.all()]
        )


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Customer
        fields = [
            "id",
            "username",
            "full_name",
            "phone_number",
            "birth_date",
        ]


class OrderCustomerSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=255, source="user.first_name")
    last_name = serializers.CharField(max_length=255, source="user.last_name")
    email = serializers.EmailField(source="user.email")

    class Meta:
        model = models.Customer
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "birth_date",
        ]


class OrderItemProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Product
        fields = [
            "id",
            "name",
            "unit_price",
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    product = OrderItemProductSerializer

    class Meta:
        model = models.OrderItem
        fields = [
            "id",
            "product",
            "quantity",
            "unit_price",
        ]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = models.Order
        fields = [
            "id",
            "status",
            "datetime_created",
            "items",
        ]


class OrderForAdminSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    customer = OrderCustomerSerializer()

    class Meta:
        model = models.Order
        fields = [
            "id",
            "customer",
            "status",
            "datetime_created",
            "items",
        ]


class OrderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Order
        fields = [
            "status",
        ]


class OrderCreateSerializer(serializers.Serializer):
    cart_id = serializers.UUIDField()

    def validate_cart_id(self, cart_id):
        try:
            if (
                models.Cart.objects.prefetch_related("items")
                .get(id=cart_id)
                .items.count()
                == 0
            ):
                raise serializers.ValidationError(
                    "Your cart is empty! Please add some product to it first."
                )
        except models.Cart.DoesNotExist:
            raise serializers.ValidationError("There is no cart with this cart id!")

        return cart_id

    def save(self, **kwargs):
        with transaction.atomic():
            cart_id = self.validated_data["cart_id"]
            user_id = self.context["user_id"]
            customer = get_object_or_404(models.Customer, user_id=user_id)

            order = models.Order()
            order.customer = customer
            order.save()

            cart_items = models.CartItem.objects.select_related("product").filter(
                cart_id=cart_id
            )

            order_items = [
                models.OrderItem(
                    order=order,
                    product=cart_item.product,
                    unit_price=cart_item.product.unit_price,
                    quantity=cart_item.quantity,
                )
                for cart_item in cart_items
            ]

            models.OrderItem.objects.bulk_create(order_items)
            models.Cart.objects.get(pk=cart_id).delete()

            return order
