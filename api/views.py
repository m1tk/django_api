from rest_framework import generics, status
from rest_framework.response import Response
from .serializers import UserSerializer
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import Product
from .serializers import ProductSerializer, SaleSerializer

class SignupView(generics.CreateAPIView):
    serializer_class = UserSerializer

class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(username=username, password=password)
        
        if not user:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        })

class ProductCreateView(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ProductView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Get all products for current user
        return Product.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        # Check if product_id is in URL parameters
        product_id = self.kwargs.get('id')
        if product_id:
            try:
                product = Product.objects.get(id=product_id, user=request.user)
                serializer = self.get_serializer(product)
                return Response(serializer.data)
            except Product.DoesNotExist:
                return Response(
                    {'error': 'Product not found or not owned by user'},
                    status=status.HTTP_404_NOT_FOUND
                )
        # Return all products if no ID specified
        return super().get(request, *args, **kwargs)

class SaleCreateView(generics.CreateAPIView):
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        product = serializer.validated_data['product']
        
        # Update product available quantity
        product.quantity -= serializer.validated_data['quantity']
        product.save()
        
        # Add new sale record
        serializer.save(
            unit_price=product.unit_price
        )
