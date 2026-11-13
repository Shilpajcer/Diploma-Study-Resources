import os
import uuid

from django.db import models
from django.utils import timezone


class Scheme(models.Model):
    name = models.CharField(max_length=20, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Branch(models.Model):
    name = models.CharField(max_length=150)
    short_name = models.CharField(max_length=20, unique=True)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.name


class SchemeBranch(models.Model):
    scheme = models.ForeignKey(
        Scheme, on_delete=models.CASCADE, related_name="scheme_branches"
    )
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="scheme_branches"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["scheme", "branch"],
                name="unique_scheme_branch"
            )
        ]

    def __str__(self):
        return f"{self.scheme} - {self.branch}"


class Semester(models.Model):
    scheme_branch = models.ForeignKey(
        SchemeBranch, on_delete=models.CASCADE, related_name="semesters"
    )
    number = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["number"]
        constraints = [
            models.UniqueConstraint(
                fields=["scheme_branch", "number"],
                name="unique_branch_semester"
            ),
            models.CheckConstraint(
                condition=models.Q(number__gte=1, number__lte=6),
                name="semester_number_1_to_6"
            )
        ]

    def __str__(self):
        return f"Semester {self.number} - {self.scheme_branch}"


class Subject(models.Model):
    semester = models.ForeignKey(
        Semester, on_delete=models.CASCADE, related_name="subjects"
    )
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50)

    class Meta:
        ordering = ["code"]
        constraints = [
            models.UniqueConstraint(
                fields=["semester", "code"],
                name="unique_subject_code_per_semester"
            )
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

class Unit(models.Model):
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="units"
    )
    number = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["number"]
        constraints = [
            models.UniqueConstraint(
                fields=["subject", "number"],
                name="unique_unit_per_subject"
            ),
            models.CheckConstraint(
                condition=models.Q(number__gte=1, number__lte=10),
                name="unit_number_1_to_10"
            ),
        ]

    def __str__(self):
        return f"Unit {self.number} - {self.name}"
class ResourceCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Resource(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending Verification"),
        ("verified", "Verified"),
        ("rejected", "Rejected"),
    ]

    LANGUAGE_CHOICES = [
        ("English", "English"),
        ("Kannada", "Kannada"),
        ("Both", "English and Kannada"),
    ]

    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name="resources"
    )
    category = models.ForeignKey(
        ResourceCategory, on_delete=models.PROTECT, related_name="resources"
    )
    unit = models.ForeignKey(
    Unit,
    on_delete=models.SET_NULL,
    related_name="resources",
    blank=True,
    null=True
)
    title = models.CharField(max_length=250)
    description = models.TextField(blank=True)
    language = models.CharField(
        max_length=20, choices=LANGUAGE_CHOICES, default="English"
    )
    file_url = models.URLField(blank=True)
    file = models.FileField(
        upload_to="study_materials/",
        blank=True,
        null=True
    )
    source_url = models.URLField(blank=True)
    exam_year = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        db_index=True,
        help_text="Examination year, e.g. 2020, 2024, 2025",
    )
    exam_session = models.CharField(
        max_length=40,
        blank=True,
        help_text="Examination session or month, e.g. 'Nov/Dec', 'Jun/Jul', 'Model Paper'",
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


def contact_attachment_upload_to(instance, filename):
    """Store contact attachments under a date prefix with a random UUID filename."""
    _, ext = os.path.splitext(os.path.basename(filename or ""))
    safe_ext = ext.lower() if ext else ""
    date_prefix = timezone.now().strftime("%Y/%m")
    return f"contact_attachments/{date_prefix}/{uuid.uuid4().hex}{safe_ext}"


class ContactSubmission(models.Model):
    """Stores contact form enquiries, feedback, and optional attachments."""

    SUBJECT_CHOICES = [
        ("general_enquiry", "General Enquiry"),
        ("technical_issue", "Technical Issue"),
        ("study_material_request", "Study Material Request"),
        ("contribute_study_materials", "Contribute Study Materials"),
        ("feedback", "Feedback"),
        ("other", "Other"),
    ]

    full_name = models.CharField(max_length=120)
    email = models.EmailField(max_length=254)
    subject = models.CharField(max_length=40, choices=SUBJECT_CHOICES)
    message = models.TextField(max_length=4000)
    attachment = models.FileField(
        upload_to=contact_attachment_upload_to,
        blank=True,
        null=True,
    )
    attachment_original_name = models.CharField(max_length=255, blank=True)
    submission_hash = models.CharField(max_length=64, db_index=True, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Contact Submission"
        verbose_name_plural = "Contact Submissions"

    def __str__(self):
        return f"{self.get_subject_display()} - {self.full_name} ({self.created_at:%Y-%m-%d})"