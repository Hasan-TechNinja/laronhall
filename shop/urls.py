from django.urls import path
from . import views

urlpatterns = [
    path('products/', views.ProductsView.as_view(), name='products'),
    path('products/<slug:slug>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('cart/add/', views.AddToCart.as_view(), name='cart-add'),
    path('cart/', views.CartView.as_view(), name='cart'),
    path('cart/update/<int:id>/', views.CartUpdateView.as_view(), name='cart-update'),
    path('cart/delete/<int:id>/', views.CartDeleteView.as_view(), name='cart-delete'),
]