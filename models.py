from django.contrib.auth.models import AbstractUser
from django.db import models
from decimal import Decimal
from datetime import date
from django.core.validators import FileExtensionValidator


class User(AbstractUser):
    """
    Custom user model supporting 5 functional roles:
    - Visiteur: Public visitor
    - Souscripteur (Client): End customer / policyholder
    - Agent: Field commercial / insurance agent
    - Gestionnaire: Underwriter / claims and policy manager
    - Administrateur: Full system administrator
    """
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrateur'
        GESTIONNAIRE = 'GESTIONNAIRE', 'Gestionnaire'
        AGENT = 'AGENT', 'Agent / Commercial'
        CLIENT = 'CLIENT', 'Souscripteur (Client)'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.AGENT)
    phone = models.CharField(max_length=30, blank=True, default='')

    def __str__(self):
        return f"{self.username} [{self.get_role_display()}]"


class Customer(models.Model):
    """Insured / Policyholder information (Souscripteur / Assuré)"""
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customer_profile'
    )
    customer_code = models.CharField(max_length=50, default='480001186')
    name = models.CharField(max_length=200, default='MME TCHAMBA PELAP LYBELLE DORCAS')
    address = models.CharField(max_length=255, default='PB YAOUNDE')
    phone = models.CharField(max_length=30, blank=True, default='')
    driver_license_number = models.CharField(max_length=50, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.customer_code})"


class Vehicle(models.Model):
    """Vehicle Technical Specifications for CIMA Actuarial Rating"""
    ENERGY_CHOICES = [
        ('DIE', 'Diesel'),
        ('ESS', 'Essence'),
    ]

    owner = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='vehicles')
    make_model = models.CharField(max_length=100, default='TOYOTA 64CTK')
    license_plate = models.CharField(max_length=30, unique=True, default='OU 923 AO')
    chassis_number = models.CharField(max_length=50, unique=True, default='JT164CT4000018658')
    fiscal_power = models.PositiveIntegerField(default=8)
    energy = models.CharField(max_length=5, choices=ENERGY_CHOICES, default='DIE')
    seats = models.PositiveIntegerField(default=5)
    first_registration_date = models.DateField(null=True, blank=True, default=date(1993, 12, 30))
    category = models.CharField(max_length=10, default='01')
    zone = models.CharField(max_length=10, default='A')
    ptac = models.CharField(max_length=20, default='1400 Kg')
    usage = models.CharField(max_length=150, default="Besoins personnels et déplacements privés")

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f"{self.make_model} [{self.license_plate}]"


class Policy(models.Model):
    """CIMA Motor Insurance Policy with Full Tariffing Calculations"""
    class PolicyStatus(models.TextChoices):
        DRAFT = 'DRAFT', 'Proposition / Devis'
        APPROVED = 'APPROVED', 'Validé / En cours'
        EXPIRED = 'EXPIRED', 'Expiré'
        SUSPENDED = 'SUSPENDED', 'Suspendu'
        REJECTED = 'REJECTED', 'Rejeté'

    policy_number = models.CharField(max_length=50, unique=True, default='48PA26000067')
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='policies')
    vehicle = models.OneToOneField(Vehicle, on_delete=models.PROTECT, related_name='policy')
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='authored_policies'
    )
    insurer = models.ForeignKey(
    'insurance.Insurer',
    on_delete=models.PROTECT,
    related_name='policies',
    null=True,
    blank=True,
)
product = models.ForeignKey(
    'insurance.InsuranceProduct',
    on_delete=models.PROTECT,
    related_name='policies',
    null=True,
    blank=True,
)
certificate_template = models.ForeignKey(
    'insurance.CertificateTemplate',
    on_delete=models.PROTECT,
    related_name='policies',
    null=True,
    blank=True,
)

    # Dates
    effective_date = models.DateField(default=date(2026, 4, 1))
    effective_time = models.CharField(max_length=10, default="17:54")
    expiration_date = models.DateField(default=date(2027, 3, 31))
    duration_label = models.CharField(max_length=50, default="1 AN (365 jrs)")

    # 1. Guarantees (Primes nettes de base)
    prime_rc = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('92497.00'))
    prime_ipt = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('10250.00'))
    prime_iac = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('2050.00'))

    # 2. Accessories & Levies
    accessoires = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('3500.00'))
    carte_rose = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('1000.00'))
    dta = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('50000.00'))

    status = models.CharField(max_length=20, choices=PolicyStatus.choices, default=PolicyStatus.APPROVED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def prime_nette(self):
        return self.prime_rc + self.prime_ipt + self.prime_iac

    @property
    def tva(self):
        base = self.prime_nette + self.accessoires
        return (base * Decimal('0.1925')).quantize(Decimal('1.00'))

    @property
    def prime_ttc_assureur(self):
        return self.prime_nette + self.accessoires + self.tva + self.carte_rose

    @property
    def prime_totale(self):
        return self.prime_ttc_assureur + self.dta

    def __str__(self):
        return f"Proposition #{self.policy_number} - {self.vehicle.license_plate}"

class Insurer(models.Model):
    """An authorized insurance company or insurance group."""
    name = models.CharField(max_length=150, unique=True)
    legal_name = models.CharField(max_length=200, blank=True, default='')
    address = models.CharField(max_length=255, blank=True, default='')
    city = models.CharField(max_length=100, blank=True, default='')
    phone = models.CharField(max_length=50, blank=True, default='')
    email = models.EmailField(blank=True, default='')
    nui = models.CharField(max_length=50, blank=True, default='')
    logo = models.ImageField(
        upload_to='insurers/logos/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['png', 'jpg', 'jpeg'])],
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
class InsuranceProduct(models.Model):
    """A product offered by one insurer, e.g. Automobile Insurance."""
    insurer = models.ForeignKey(
        Insurer,
        on_delete=models.PROTECT,
        related_name='products',
    )
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=50)
    description = models.TextField(blank=True, default='')
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['insurer__name', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['insurer', 'code'],
                name='unique_product_code_per_insurer',
            ),
        ]

    def __str__(self):
        return f'{self.insurer.name} - {self.name}'


class CertificateTemplate(models.Model):
    """Versioned PDF design associated with an insurance product."""
    product = models.ForeignKey(
        InsuranceProduct,
        on_delete=models.PROTECT,
        related_name='templates',
    )
    name = models.CharField(max_length=150)
    version = models.PositiveIntegerField(default=1)
    background = models.ImageField(
        upload_to='certificate_templates/backgrounds/',
    )
    font_file = models.FileField(
        upload_to='certificate_templates/fonts/',
        blank=True,
        null=True,
    )
    page_width = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=595.27,
        help_text='PDF points; A4 width is 595.27.',
    )
    page_height = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=841.89,
        help_text='PDF points; A4 height is 841.89.',
    )
    # Coordinates are measured from the bottom-left in PDF points.
    # Example: {"registration": [58, 570], "qr": [305, 175, 92]}
    field_coordinates = models.JSONField(default=dict, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['product', '-version']
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'version'],
                name='unique_template_version_per_product',
            ),
        ]

    def __str__(self):
        return f'{self.product} - {self.name} v{self.version}'

