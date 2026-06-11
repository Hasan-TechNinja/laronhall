from django.urls import path
from . import views

urlpatterns = [
    path('products/', views.ProductsView.as_view(), name='products'),
    path('products/<slug:slug>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('cart/add/', views.AddToCart.as_view(), name='cart-add'),
    path('cart/', views.CartView.as_view(), name='cart'),
    path('cart/update/<int:id>/', views.CartUpdateView.as_view(), name='cart-update'),
    path('cart/delete/<int:id>/', views.CartDeleteView.as_view(), name='cart-delete'),
    path('checkout/', views.CreateCheckoutSessionView.as_view(), name='checkout'),
    path('checkout/guest/', views.GuestCheckoutSessionView.as_view(), name='guest-checkout'),
    path('webhook/', views.StripeWebhookView.as_view(), name='stripe-webhook'),
    path('payment/webhook/', views.StripeWebhookView.as_view(), name='stripe-webhook-alias'),
    path('payment/success/', views.PaymentSuccessView.as_view(), name='payment-success'),
    path('orders/', views.OrderView.as_view(), name='orders'),
    path('products/<slug:slug>/reviews/', views.ProductReviewListView.as_view(), name='product-reviews'),
    path('products/<slug:slug>/reviews/post/', views.ProductReviewPostView.as_view(), name='product-reviews-post'),
    path('reviews/', views.LatestReview.as_view(), name='latest-reviews'),
]