from django.urls import path
from .views import LoginView, SignupView, ProductCreateView, SaleCreateView

urlpatterns = [
    path('signup', SignupView.as_view(), name='signup'),
    path('login', LoginView.as_view(), name='login'),
    
    path('product/create', ProductCreateView.as_view(), name='product-create'),
    path('sale/create', SaleCreateView.as_view(), name='sale-create'),
]
