from django.forms import ValidationError
from django.shortcuts import get_object_or_404
from django.db.models import Count, F, Prefetch
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.mixins import (
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    DestroyModelMixin,
    UpdateModelMixin,
)

from rest_framework.viewsets import GenericViewSet
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAdminUser,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
    AllowAny,
    DjangoModelPermissions,
)

from django_filters.rest_framework import DjangoFilterBackend

from . import models, serializers, filters, paginations, permissions


class ProductViewSet(ModelViewSet):
    serializer_class = serializers.ProductSerializer
    queryset = models.Product.objects.select_related("category").all().order_by("-id")
    filter_backends = [
        SearchFilter,
        DjangoFilterBackend,
    ]
    search_fields = ["name", "category__title"]
    filterset_class = filters.ProductFilter
    pagination_class = PageNumberPagination
    PageNumberPagination.page_size = 10
    permission_classes = [permissions.IsAdminOrReadOnly]

    def get_serializer_context(self):
        return {"request": self.request}

    def destroy(self, request, pk):
        product = get_object_or_404(
            models.Product.objects.select_related(
                "category",
            ),
            pk=pk,
        )
        if product.order_items.count() > 0:
            return Response(
                {
                    "error": "there is some order items including this product. please remove them first."
                },
                status=status.HTTP_405_METHOD_NOT_ALLOWED,
            )
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CategoryViewSet(ModelViewSet):
    serializer_class = serializers.CategorySerializer
    queryset = (
        models.Category.objects.annotate(
            num_of_product=Count("products"),
        )
        .all()
        .order_by("-id")
    )

    permission_classes = [permissions.IsAdminOrReadOnly]

    def destroy(self, request, pk):
        category = get_object_or_404(
            models.Category.objects.annotate(
                product_count=Count("products"),
            ).all(),
            pk=pk,
        )
        if category.products.count() > 0:
            return Response(
                {
                    "error": "there is some products including this category. please remove them first."
                },
                status=status.HTTP_405_METHOD_NOT_ALLOWED,
            )
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CommentViewSet(ModelViewSet):
    serializer_class = serializers.CommentSerializer
    # queryset = models.Comment.objects.all()

    def get_queryset(self):
        product_pk = self.kwargs["product_pk"]
        return models.Comment.objects.select_related("product").filter(
            product_id=product_pk
        )

    def get_serializer_context(self):
        return {"product_pk": self.kwargs["product_pk"]}


class CartViewSet(
    CreateModelMixin, RetrieveModelMixin, DestroyModelMixin, GenericViewSet
):
    serializer_class = serializers.CartSerializer
    queryset = models.Cart.objects.prefetch_related("items__product")
    lookup_value_regex = "[0-9a-fA-F]{8}\-?[0-9a-fA-F]{4}\-?[0-9a-fA-F]{4}\-?[0-9a-fA-F]{4}\-?[0-9a-fA-F]{12}"


class CartItemViewSet(ModelViewSet):
    http_method_names = [
        "get",
        "post",
        "patch",
        "delete",
    ]
    # serializer_class = serializers.CartItemSerializer

    def get_queryset(self):
        cart_pk = self.kwargs["cart_pk"]
        return (
            models.CartItem.objects.select_related("product")
            .filter(cart_id=cart_pk)
            .all()
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.AddCartItemSerializer
        elif self.request.method == "PATCH":
            return serializers.UpdateCartItemSerializer
        return serializers.CartItemSerializer

    def get_serializer_context(self):
        return {"cart_pk": self.kwargs["cart_pk"]}


class CustomerViewSet(ModelViewSet):

    serializer_class = serializers.CustomerSerializer
    queryset = models.Customer.objects.select_related("user").all()
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=["GET", "PUT"], permission_classes=[IsAuthenticated])
    def me(self, request):
        user_id = request.user.id
        customer = get_object_or_404(models.Customer, user_id=user_id)
        if request.method == "GET":
            serializer = serializers.CustomerSerializer(customer)
            return Response(serializer.data)
        elif request.method == "PUT":
            serializer = serializers.CustomerSerializer(customer, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_426_UPGRADE_REQUIRED)

    @action(
        detail=True,
        permission_classes=[permissions.SendPrivateEmailToCustomerPermission],
    )
    def send_private_email(self, request, pk):
        return Response(f"Sending email to customer {pk=}")


class OrderViewSet(ModelViewSet):
    # permission_classes = [IsAuthenticated]
    http_method_names = [
        "get",
        "post",
        "patch",
        "delete",
        "options",
        "head",
    ]

    def get_permissions(self):
        if self.request.method in ["PATCH", "DELETE"]:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = models.Order.objects.select_related(
            "customer__user"
        ).prefetch_related(
            Prefetch(
                "items", queryset=models.OrderItem.objects.select_related("product")
            )
        )
        if self.request.user.is_staff:
            return queryset

        return queryset.filter(customer__user_id=self.request.user.id)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.OrderCreateSerializer
        
        if self.request.method == 'PATCH':
            return serializers.OrderUpdateSerializer

        if self.request.user.is_staff:
            return serializers.OrderForAdminSerializer
        return serializers.OrderSerializer

    def get_serializer_context(self):
        return {"user_id": self.request.user.id}

    def create(self, request, *args, **kwargs):
        create_order_serializer = serializers.OrderCreateSerializer(
            data=request.data,
            context={"user_id": self.request.user.id},
        )
        create_order_serializer.is_valid(raise_exception=True)
        created_order = create_order_serializer.save()

        serializer = serializers.OrderSerializer(created_order)
        return Response(serializer.data)
