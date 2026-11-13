from django import forms
from django.contrib import admin
from .models import (
    Scheme,
    Branch,
    SchemeBranch,
    Semester,
    Subject,
    Unit,
    ResourceCategory,
    Resource,
    ContactSubmission,
)


class ResourceAdminForm(forms.ModelForm):
    """Secure validation for study material and question paper file uploads."""

    class Meta:
        model = Resource
        fields = "__all__"

    def clean_file(self):
        uploaded = self.cleaned_data.get("file")
        if uploaded and hasattr(uploaded, "file"):
            name = (uploaded.name or "").lower()
            if not name.endswith(".pdf"):
                raise forms.ValidationError(
                    "Only PDF documents (.pdf) are allowed for study materials and question papers."
                )
            if uploaded.size <= 0:
                raise forms.ValidationError("The uploaded file is empty.")
            if uploaded.size > 25 * 1024 * 1024:
                raise forms.ValidationError(
                    "File size exceeds the 25 MB maximum limit."
                )
            pos = uploaded.tell() if hasattr(uploaded, "tell") else 0
            try:
                uploaded.seek(0)
                header = uploaded.read(1024)
            finally:
                uploaded.seek(pos)
            if not header.startswith(b"%PDF-"):
                raise forms.ValidationError(
                    "Invalid file content: the file does not match a valid PDF document header."
                )
        return uploaded


@admin.register(Scheme)
class SchemeAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    search_fields = ("name",)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("name", "short_name", "slug")
    search_fields = ("name", "short_name")


@admin.register(SchemeBranch)
class SchemeBranchAdmin(admin.ModelAdmin):
    list_display = ("scheme", "branch")
    list_filter = ("scheme", "branch")


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ("number", "scheme_branch")
    list_filter = ("number",)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "semester")
    search_fields = ("code", "name")
    list_filter = ("semester",)

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("number", "name", "subject")
    search_fields = ("name", "subject__name", "subject__code")
    list_filter = ("subject",)

@admin.register(ResourceCategory)
class ResourceCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    form = ResourceAdminForm
    list_display = (
        "title",
        "subject",
        "category",
        "exam_year",
        "exam_session",
        "status",
        "is_active",
    )

    search_fields = (
        "title",
        "subject__name",
        "subject__code",
        "exam_year",
        "exam_session",
    )

    list_filter = (
        "status",
        "category",
        "exam_year",
        "language",
        "is_active",
    )


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "subject", "created_at", "is_resolved")
    list_filter = ("subject", "is_resolved", "created_at")
    search_fields = ("full_name", "email", "message", "attachment_original_name")
    readonly_fields = (
        "created_at",
        "submission_hash",
        "ip_address",
        "attachment_original_name",
    )