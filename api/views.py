from django.http import HttpResponse
from rest_framework import generics, status
from rest_framework.response import Response
from .serializers import UserSerializer
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Prefetch, Sum, F, DecimalField
from django.db.models.functions import Coalesce
from decimal import Decimal
from reportlab.platypus import Table, TableStyle
from reportlab.pdfgen import canvas
from reportlab.lib import pagesizes
from reportlab.lib import colors
import statistics
from io import BytesIO
from .models import Product, Sale
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

class SalesReportView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        month = request.GET.get('month')
        year = request.GET.get('year')
        if not month or not year:
            return Response(
                {'error': 'Month and year parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            month = int(month)
            year = int(year)
            if month < 1 or month > 12:
                raise ValueError
        except ValueError:
            return Response(
                {'error': 'Invalid month or year format'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # fetch all users products in addition to related sales table rows
        products = Product.objects.filter(user=request.user)\
            .prefetch_related(Prefetch(
                'sales',
                queryset=Sale.objects.filter(
                    date__month=month,
                    date__year=year
                )
            ))
        
        buf = BytesIO()
        # Creating canva pdf object
        pdf = canvas.Canvas(buf, pagesize=pagesizes.A4)
        
        #pdf.setFont("Modern sans font", 12)
        pdf.drawString(72, 750, f"Monthly sales report for user: {request.user.username}")
        pdf.drawString(72, 730, f"{month}/{year}")
        
        data = [[
            "ID",
            "Product name",
            "Total sold",
            "Total income",
            "Median Price",
            "Available stock"
        ]]

        total_units_sold = 0
        total_income     = 0

        for product in products:
            sales  = product.sales.all()
            prices = [sale.unit_price for sale in sales]

            product_data = [
                product.id,
                product.name,
                sales.aggregate(total=Sum('quantity'))['total'] or 0,
                f"${sales.aggregate(total_income=Coalesce(Sum(F('quantity') * F('unit_price'), output_field=DecimalField()), Decimal('0.00')))['total_income']:.2f}",
                f"${statistics.median(prices):.2f}" if prices else "N/A",
                product.quantity
            ]
            data.append(product_data)
            total_units_sold += product_data[2]
            total_income     += float(product_data[3][1:]) if product_data[3] != '$0.00' else 0

        data.append([
            '-',
            'TOTAL',
            total_units_sold,
            f"${total_income:.2f}",
            '-',
            sum(p.quantity for p in products)
        ])

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('BACKGROUND', (0,1), (-1,-2), colors.beige),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
        ]))

        table.wrapOn(pdf, 400, 600)
        table.drawOn(pdf, 72, 600)

        pdf.showPage()
        pdf.save()

        buf.seek(0)
        response = HttpResponse(buf, content_type='application/pdf')
        return response
