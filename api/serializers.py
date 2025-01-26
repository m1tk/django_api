from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from .models import Product, Sale

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'password']

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)

class Products(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password']

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'quantity', 'unit_price', 'user', 'created_at']
        read_only_fields = ['user', 'created_at']

class SaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sale
        fields = ['id', 'product', 'quantity', 'unit_price', 'date']
        read_only_fields = ['date', 'unit_price']
        
    def validate(self, data):
        # Ensure user owns the product
        if data['product'].user != self.context['request'].user:
            raise serializers.ValidationError("You don't own this product")

        # Check if we have enough units
        if data['quantity'] > data['product'].quantity:
            raise serializers.ValidationError(
                f"Not enough stock. Available: {data['product'].quantity}"
            )
                
        return data
