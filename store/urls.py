from django.urls import path

# from rest_framework.routers import SimpleRouter, DefaultRouter
from rest_framework_nested import routers
from . import views


router = routers.DefaultRouter()
router.register("products", views.ProductViewSet, basename="product")
router.register("categories", views.CategoryViewSet, basename="category")
router.register("carts", views.CartViewSet, basename="cart")
router.register("customers", views.CustomerViewSet, basename="customer")
router.register("orders", views.OrderViewSet, basename="order")

# store/products/product=1/comments/10
products_router = routers.NestedDefaultRouter(router, "products", lookup="product")
products_router.register("comments", views.CommentViewSet, basename="product-comments")

cart_item_router = routers.NestedDefaultRouter(router, "carts", lookup="cart")
cart_item_router.register("items", views.CartItemViewSet, basename="cart-items")

urlpatterns = router.urls + products_router.urls + cart_item_router.urls
