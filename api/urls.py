from django.urls import path
from .views import LoginView, SignupView, ProductCreateView, ProductView, SaleCreateView, SalesReportView

urlpatterns = [
    path('signup', SignupView.as_view(), name='signup'),
    path('login', LoginView.as_view(), name='login'),
    
    path('product/create', ProductCreateView.as_view(), name='product-create'),
    path('product/status', ProductView.as_view(), name='product-status'),
    path('product/status/<int:id>', ProductView.as_view(), name='product-status'),
    path('sale/create', SaleCreateView.as_view(), name='sale-create'),

    path('report/<int:month>/<int:year>', SalesReportView.as_view(), name='sales-report'),
]
