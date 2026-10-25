from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, Customer, Vehicle, Policy
from .models import Insurer, InsuranceProduct, CertificateTemplate

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom login serializer that packages user profile details into the JWT response."""
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['role'] = user.role
        token['full_name'] = f"{user.first_name} {user.last_name}".strip() or user.username
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'role': self.user.role,
            'role_label': self.user.get_role_display(),
            'full_name': f"{self.user.first_name} {self.user.last_name}".strip() or self.user.username,
        }
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'phone', 'first_name', 'last_name']


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'


class VehicleSerializer(serializers.ModelSerializer):
    owner_details = CustomerSerializer(source='owner', read_only=True)

    class Meta:
        model = Vehicle
        fields = '__all__'


class PolicySerializer(serializers.ModelSerializer):
    customer_details = CustomerSerializer(source='customer', read_only=True)
    vehicle_details = VehicleSerializer(source='vehicle', read_only=True)
    prime_nette = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    tva = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    prime_ttc_assureur = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    prime_totale = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Policy
        fields = '__all__'


class InsurerSerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = Insurer
        fields = [
            'id', 'name', 'legal_name', 'address', 'city', 'phone',
            'email', 'nui', 'logo', 'logo_url', 'active',
        ]

    def get_logo_url(self, obj):
        request = self.context.get('request')
        if not obj.logo:
            return None
        url = obj.logo.url
        return request.build_absolute_uri(url) if request else url


class InsuranceProductSerializer(serializers.ModelSerializer):
    insurer_name = serializers.CharField(source='insurer.name', read_only=True)

    class Meta:
        model = InsuranceProduct
        fields = [
            'id', 'insurer', 'insurer_name', 'name', 'code',
            'description', 'active',
        ]


class CertificateTemplateSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    insurer_name = serializers.CharField(
        source='product.insurer.name',
        read_only=True,
    )

    class Meta:
        model = CertificateTemplate
        fields = [
            'id', 'product', 'product_name', 'insurer_name', 'name',
            'version', 'background', 'font_file', 'page_width',
            'page_height', 'field_coordinates', 'active', 'created_at',
        ]
        read_only_fields = ['created_at']
