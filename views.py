from django.http import FileResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.renderers import BaseRenderer

from .models import Customer, Vehicle, Policy
from .serializers import CustomerSerializer, VehicleSerializer, PolicySerializer
from .permissions import IsStaffMember, IsGestionnaireOrAdmin, PolicyAccessPermission
from .pdf_generator import generate_vehicle_certificate

from .models import Insurer, InsuranceProduct, CertificateTemplate
from .serializers import (
    InsurerSerializer,
    InsuranceProductSerializer,
    CertificateTemplateSerializer,
)

class PassthroughRenderer(BaseRenderer):
    """Bypasses DRF content negotiation so binary PDF streams download cleanly."""
    media_type = 'application/pdf'
    format = 'pdf'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsStaffMember]


class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [IsStaffMember]


class PolicyViewSet(viewsets.ModelViewSet):
    queryset = Policy.objects.all()
    serializer_class = PolicySerializer
    permission_classes = [PolicyAccessPermission]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Policy.objects.none()
        if user.is_superuser or user.role in ['ADMIN', 'GESTIONNAIRE', 'AGENT']:
            return Policy.objects.all()
        if user.role == 'CLIENT' and hasattr(user, 'customer_profile'):
            return Policy.objects.filter(customer=user.customer_profile)
        return Policy.objects.none()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'], url_path='approve', permission_classes=[IsGestionnaireOrAdmin])
    def approve_policy(self, request, pk=None):
        policy = self.get_object()
        policy.status = Policy.PolicyStatus.APPROVED
        policy.save()
        return Response({'status': 'Police validée avec succès.', 'policy_status': policy.status})

    @action(detail=True, methods=['post'], url_path='reject', permission_classes=[IsGestionnaireOrAdmin])
    def reject_policy(self, request, pk=None):
        policy = self.get_object()
        policy.status = Policy.PolicyStatus.REJECTED
        policy.save()
        return Response({'status': 'Police rejetée.', 'policy_status': policy.status})

    @action(detail=True, methods=['post'], url_path='suspend', permission_classes=[IsGestionnaireOrAdmin])
    def suspend_policy(self, request, pk=None):
        policy = self.get_object()
        policy.status = Policy.PolicyStatus.SUSPENDED
        policy.save()
        return Response({'status': 'Police suspendue.', 'policy_status': policy.status})
    ##modif
    @action(
        detail=True,
        methods=['get'],
        url_path='download-certificate',
        permission_classes=[IsAuthenticated],
        renderer_classes=[PDFRenderer],
    )
    def download_certificate(self, request, pk=None):
        policy = self.get_object()
        pdf_file = generate_vehicle_certificate(policy)
        identifier = policy.attestation_number or policy.policy_number
        filename = f'certificate_{identifier}.pdf'
        return FileResponse(
            pdf_file,
            as_attachment=True,
            filename=filename,
            content_type='application/pdf',
        )

class PDFRenderer(BaseRenderer):
    media_type = 'application/pdf'
    format = 'pdf'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data


class InsurerViewSet(viewsets.ModelViewSet):
    queryset = Insurer.objects.filter(active=True)
    serializer_class = InsurerSerializer
    permission_classes = [IsAuthenticated]


class InsuranceProductViewSet(viewsets.ModelViewSet):
    queryset = InsuranceProduct.objects.filter(active=True).select_related('insurer')
    serializer_class = InsuranceProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        insurer_id = self.request.query_params.get('insurer')
        if insurer_id:
            queryset = queryset.filter(insurer_id=insurer_id)
        return queryset


class CertificateTemplateViewSet(viewsets.ModelViewSet):
    queryset = CertificateTemplate.objects.filter(active=True).select_related(
        'product',
        'product__insurer',
    )
    serializer_class = CertificateTemplateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        product_id = self.request.query_params.get('product')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        return queryset


# Add this action inside your existing PolicyViewSet.
# Your existing PolicyViewSet must allow authenticated users and use get_object().

    @action(
        detail=True,
        methods=['get'],
        url_path='download-certificate',
        permission_classes=[IsAuthenticated],
        renderer_classes=[PDFRenderer],
    )
    def download_certificate(self, request, pk=None):
        policy = self.get_object()
        pdf_file = generate_vehicle_certificate(policy)
        identifier = policy.attestation_number or policy.policy_number
        filename = f'certificate_{identifier}.pdf'
        return FileResponse(
            pdf_file,
            as_attachment=True,
            filename=filename,
            content_type='application/pdf',
        )

