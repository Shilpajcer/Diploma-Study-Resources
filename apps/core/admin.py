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
    list_display = (
        "title",
        "subject",
        "unit",
        "category",
        "status",
        "is_active",
    )

    search_fields = ("title", "subject__name", "subject__code")

    list_filter = (
        "status",
        "category",
        "unit",
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