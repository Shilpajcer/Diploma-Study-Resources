from datetime import timedelta
import logging
import os

from django.conf import settings
from django.core.cache import cache
from django.core.mail import EmailMessage
from django.db import models
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from . import sample_data
from .forms import ContactSubmissionForm, compute_submission_hash
from .models import (
    Scheme,
    Branch,
    SchemeBranch,
    Semester,
    Subject,
    ResourceCategory,
    ContactSubmission,
)

logger = logging.getLogger(__name__)

CONTACT_RATE_LIMIT_MAX = 5
CONTACT_RATE_LIMIT_WINDOW_SECONDS = 600
CONTACT_DUPLICATE_WINDOW_MINUTES = 10

ABOUT_WHAT_WE_PROVIDE = [
    {
        "title": "Subject-wise Notes",
        "icon": "bi-journal-text",
        "description": "Structured unit-wise and subject-wise PDF notes organised by scheme, branch, and semester.",
    },
    {
        "title": "Previous Year Question Papers",
        "icon": "bi-file-earmark-text",
        "description": "Past DTE diploma exam papers to help students understand question patterns and marking style.",
    },
    {
        "title": "Lab Manuals",
        "icon": "bi-clipboard2-check",
        "description": "Practical lab records, experiment procedures, and program manuals for laboratory courses.",
    },
    {
        "title": "Official Syllabus",
        "icon": "bi-list-check",
        "description": "Scheme-wise syllabus references so students can track prescribed units and course outcomes.",
    },
    {
        "title": "Important Questions",
        "icon": "bi-star",
        "description": "Exam-focused topic and unit question sets for targeted revision before semester tests.",
    },
    {
        "title": "Solved Question Papers",
        "icon": "bi-check2-circle",
        "description": "Worked solutions and answer references to help verify your exam preparation.",
    },
    {
        "title": "DTE Updates",
        "icon": "bi-megaphone",
        "description": "A dedicated space planned for important Karnataka DTE academic circulars and exam notices.",
    },
]

ABOUT_WHY_CHOOSE_US = [
    {
        "title": "Organised Subject-wise Resources",
        "icon": "bi-folder2-open",
        "description": "Browse directly by scheme, branch, semester, and subject instead of hunting through unorganised links.",
    },
    {
        "title": "Easy Navigation",
        "icon": "bi-compass",
        "description": "Clear step-by-step filtering lets you reach your subject page and units in just a few clicks.",
    },
    {
        "title": "Free Access to Available Materials",
        "icon": "bi-unlock",
        "description": "Every verified study material published on the platform is free to view online or download as PDF.",
    },
    {
        "title": "Semester-wise Learning Resources",
        "icon": "bi-layers",
        "description": "Structured across Semesters 1 to 6 to align with Karnataka diploma progression.",
    },
    {
        "title": "Student-friendly Interface",
        "icon": "bi-laptop",
        "description": "Readable layouts and inline PDF viewing designed to work smoothly on mobile, tablet, and desktop.",
    },
]

# Editable team configuration: update names/bios when ready to publish.
ABOUT_TEAM_MEMBERS = [
    {
        "role": "Founder & Developer",
        "icon": "bi-person-workspace",
        "summary": "Leading platform architecture, backend development, and academic resource organisation for Karnataka diploma students.",
    },
    {
        "role": "Co-Founder & Developer",
        "icon": "bi-code-square",
        "summary": "Driving frontend experience, accessibility, content curation workflows, and student-centric feature design.",
    },
]

CONTACT_FAQS = [
    {
        "id": "faq-download",
        "question": "How can I download study materials?",
        "answer": (
            "Open the Study Materials page, select your Scheme, Branch, and Semester, "
            "and open any available subject. Verified PDF materials can be read inline, "
            "opened in a new tab, or downloaded directly to your device."
        ),
    },
    {
        "id": "faq-contribute",
        "question": "Can I contribute notes?",
        "answer": (
            "Self-service student upload accounts are planned for a future version. "
            "Right now, you can share notes, lab manuals, or question papers by selecting "
            "'Contribute Study Materials' in the contact form above and attaching your file."
        ),
    },
    {
        "id": "faq-report",
        "question": "How can I report incorrect study materials?",
        "answer": (
            "Select 'Technical Issue' or 'Feedback' in the contact form above, include the "
            "scheme, branch, subject code, and what needs correction, and optionally attach "
            "a screenshot so we can review it."
        ),
    },
    {
        "id": "faq-free",
        "question": "Is Diploma Study Hub free?",
        "answer": (
            "Yes. All available study materials on Diploma Study Hub are free for Karnataka "
            "diploma students to view and download without requiring a paid subscription."
        ),
    },
]


def home(request):
    context = {
        "schemes": sample_data.SCHEMES,
        "branches": sample_data.BRANCHES,
        "semesters": sample_data.SEMESTERS,
        "categories": sample_data.CATEGORIES,
        "latest_materials": sample_data.LATEST_MATERIALS,
        "question_papers": sample_data.QUESTION_PAPERS,
        "important_questions": sample_data.IMPORTANT_QUESTIONS,
        "recent_uploads": sample_data.RECENT_UPLOADS,
        "prep_tools": sample_data.PREP_TOOLS,
        
    }
    return render(request, "public/home.html", context)


def materials(request):
    schemes = Scheme.objects.filter(is_active=True)
    branches = Branch.objects.none()
    semesters = Semester.objects.none()
    subjects = Subject.objects.none()

    selected_scheme = None
    selected_branch = None
    selected_semester = None

    scheme_slug = request.GET.get("scheme")
    branch_slug = request.GET.get("branch")
    semester_number = request.GET.get("semester")

    if scheme_slug:
        selected_scheme = get_object_or_404(
            Scheme, slug=scheme_slug, is_active=True
        )

        branches = Branch.objects.filter(
            scheme_branches__scheme=selected_scheme
        ).distinct()

    if branch_slug:
        selected_branch = get_object_or_404(
            Branch, slug=branch_slug
        )

        if selected_scheme:
            scheme_branch = get_object_or_404(
                SchemeBranch,
                scheme=selected_scheme,
                branch=selected_branch,
            )
        else:
            available_mappings = SchemeBranch.objects.filter(
                branch=selected_branch
            ).select_related("scheme")

            context = {
                "schemes": schemes,
                "available_mappings": available_mappings,
                "selected_branch": selected_branch,
            }
            return render(request, "public/materials.html", context)

        semesters = Semester.objects.filter(
            scheme_branch=scheme_branch
        )

    if semester_number and selected_scheme and selected_branch:
        selected_semester = get_object_or_404(
            Semester,
            scheme_branch__scheme=selected_scheme,
            scheme_branch__branch=selected_branch,
            number=semester_number,
        )

        subjects = Subject.objects.filter(
            semester=selected_semester
        )

    context = {
        "schemes": schemes,
        "branches": branches,
        "semesters": semesters,
        "subjects": subjects,
        "selected_scheme": selected_scheme,
        "selected_branch": selected_branch,
        "selected_semester": selected_semester,
    }

    return render(request, "public/materials.html", context)

def subject_detail(request, subject_id):
    subject = get_object_or_404(
        Subject.objects.select_related(
            "semester",
            "semester__scheme_branch",
            "semester__scheme_branch__scheme",
            "semester__scheme_branch__branch",
        ),
        id=subject_id,
    )
# Fetch all units belonging to this subject
    units = subject.units.all()
    resources = subject.resources.filter(
        status="verified",
        is_active=True,
    ).select_related("category", "unit")

    categories = ResourceCategory.objects.filter(
        resources__subject=subject,
        resources__status="verified",
        resources__is_active=True,
    ).distinct()

    selected_category = request.GET.get("category")

    if selected_category:
        resources = resources.filter(
            category__slug=selected_category
        )

    search_query = request.GET.get("q", "").strip()

    if search_query:
        resources = resources.filter(
            models.Q(title__icontains=search_query) |
            models.Q(description__icontains=search_query)
        )

    context = {
        "subject": subject,
        "units": units,
        "resources": resources,
        "categories": categories,
        "selected_category": selected_category,
        "search_query": search_query,
    }

    return render(request, "public/subject_detail.html", context)


def coming_soon(request, title="This page"):
    return render(
        request,
        "public/coming_soon.html",
        {"page_title": title},
    )


def _get_client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _build_contact_cards():
    info = getattr(settings, "CONTACT_INFO", {})
    office_address = info.get("office_address", "")
    support_phone = info.get("support_phone", "")

    def _card(title, icon, email_key, fallback_note):
        email = info.get(email_key, "")
        return {
            "title": title,
            "icon": icon,
            "email": email,
            "phone": support_phone if email_key in ("general_email", "support_email") else "",
            "address": office_address if email_key == "general_email" else "",
            "is_configured": bool(email or (email_key == "general_email" and (support_phone or office_address))),
            "fallback_note": fallback_note,
        }

    return [
        _card(
            "General Enquiries",
            "bi-envelope-open",
            "general_email",
            "Direct contact details will be announced soon. Use the form below for any general questions.",
        ),
        _card(
            "Technical Support",
            "bi-tools",
            "support_email",
            "Support contact details will be announced soon. Report broken links or bugs via the form below.",
        ),
        _card(
            "Study Material Contribution",
            "bi-file-earmark-arrow-up",
            "materials_email",
            "Contribution inbox details will be announced soon. You can attach notes or papers in the form below.",
        ),
        _card(
            "Feedback and Suggestions",
            "bi-chat-dots",
            "feedback_email",
            "Feedback contact details will be announced soon. Share suggestions anytime using the form below.",
        ),
    ]


def _send_contact_emails(submission):
    """Send student acknowledgement and admin notification when email is configured."""
    if not getattr(settings, "EMAIL_CONFIGURED", False):
        return False

    info = getattr(settings, "CONTACT_INFO", {})
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@localhost")
    sent_any = False

    try:
        ack = EmailMessage(
            subject=f"[{settings.SITE_NAME}] We received your message (#{submission.id})",
            body=(
                f"Hello {submission.full_name},\n\n"
                f"Thank you for contacting {settings.SITE_NAME}.\n"
                f"We have received your submission under '{submission.get_subject_display()}' "
                f"(Reference #{submission.id}).\n\n"
                "Our team will review it and get back to you if a response is needed.\n\n"
                f"— {settings.SITE_NAME}"
            ),
            from_email=from_email,
            to=[submission.email],
        )
        ack.send(fail_silently=False)
        sent_any = True

        admin_email = info.get("admin_notification_email", "")
        if admin_email:
            admin_msg = EmailMessage(
                subject=f"[{settings.SITE_NAME}] New Contact: {submission.get_subject_display()} (#{submission.id})",
                body=(
                    f"Name: {submission.full_name}\n"
                    f"Email: {submission.email}\n"
                    f"Subject: {submission.get_subject_display()}\n"
                    f"Submitted: {submission.created_at:%Y-%m-%d %H:%M:%S %Z}\n"
                    f"Attachment: {submission.attachment_original_name or 'None'}\n\n"
                    f"Message:\n{submission.message}\n"
                ),
                from_email=from_email,
                to=[admin_email],
                reply_to=[submission.email],
            )
            admin_msg.send(fail_silently=False)
    except Exception:
        logger.exception("Failed to send contact email for submission #%s", submission.id)
        return False

    return sent_any


def _process_contact_submission(request):
    """Validate, rate-limit, deduplicate, and persist a contact submission."""
    client_ip = _get_client_ip(request)
    rate_key = f"contact_rl:{client_ip}" if client_ip else None
    if rate_key and (cache.get(rate_key, 0) >= CONTACT_RATE_LIMIT_MAX):
        return (
            None,
            {"__all__": ["Too many submissions in a short time. Please wait a few minutes and try again."]},
            429,
            False,
        )

    form = ContactSubmissionForm(request.POST, request.FILES)
    if not form.is_valid():
        errors = {
            field: [str(msg) for msg in msgs]
            for field, msgs in form.errors.items()
        }
        return None, errors, 400, False

    email = form.cleaned_data["email"]
    subject = form.cleaned_data["subject"]
    message = form.cleaned_data["message"]
    submission_hash = compute_submission_hash(email, subject, message)

    cutoff = timezone.now() - timedelta(minutes=CONTACT_DUPLICATE_WINDOW_MINUTES)
    if ContactSubmission.objects.filter(
        submission_hash=submission_hash,
        created_at__gte=cutoff,
    ).exists():
        return (
            None,
            {"__all__": ["This message was already submitted recently. Please wait before sending it again."]},
            409,
            False,
        )

    submission = form.save(commit=False)
    submission.submission_hash = submission_hash
    submission.ip_address = client_ip
    uploaded_file = form.cleaned_data.get("attachment")
    if uploaded_file:
        submission.attachment_original_name = os.path.basename(uploaded_file.name)[:255]
    submission.save()

    if rate_key:
        current_count = cache.get(rate_key, 0)
        cache.set(rate_key, current_count + 1, CONTACT_RATE_LIMIT_WINDOW_SECONDS)

    email_sent = _send_contact_emails(submission)
    return submission, {}, 201, email_sent


def contact(request):
    max_mb = getattr(settings, "CONTACT_MAX_ATTACHMENT_SIZE", 5 * 1024 * 1024) / (1024 * 1024)
    allowed_exts = getattr(
        settings,
        "CONTACT_ALLOWED_ATTACHMENT_EXTENSIONS",
        [".pdf", ".png", ".jpg", ".jpeg", ".webp", ".txt"],
    )
    context = {
        "contact_cards": _build_contact_cards(),
        "subject_choices": ContactSubmission.SUBJECT_CHOICES,
        "faqs": CONTACT_FAQS,
        "max_attachment_mb": f"{max_mb:g}",
        "allowed_extensions_label": ", ".join(ext.lstrip(".").upper() for ext in allowed_exts),
        "allowed_extensions_accept": ",".join(allowed_exts),
        "form_values": {},
        "form_errors": {},
        "form_general_error": "",
        "submit_success": None,
    }

    if request.method == "POST":
        submission, errors, status_code, email_sent = _process_contact_submission(request)
        if submission is not None:
            context["submit_success"] = {
                "id": submission.id,
                "subject": submission.get_subject_display(),
                "email_sent": email_sent,
            }
        else:
            context["form_errors"] = errors
            context["form_general_error"] = (
                (errors.get("__all__") or errors.get("website") or [""])[0]
            )
            context["form_values"] = {
                "full_name": request.POST.get("full_name", ""),
                "email": request.POST.get("email", ""),
                "subject": request.POST.get("subject", ""),
                "message": request.POST.get("message", ""),
            }
            return render(request, "public/contact.html", context, status=status_code)

    return render(request, "public/contact.html", context)


@require_http_methods(["POST"])
def contact_submit_api(request):
    try:
        submission, errors, status_code, email_sent = _process_contact_submission(request)
    except Exception:
        logger.exception("Unexpected error while processing contact submission")
        return JsonResponse(
            {
                "ok": False,
                "error": "An unexpected server error occurred. Please try again later.",
                "errors": {},
            },
            status=500,
        )

    if submission is None:
        general_errors = errors.get("__all__") or errors.get("website")
        top_message = (
            general_errors[0]
            if general_errors
            else "Please review the highlighted fields and correct any errors."
        )
        return JsonResponse(
            {
                "ok": False,
                "error": top_message,
                "errors": errors,
            },
            status=status_code,
        )

    return JsonResponse(
        {
            "ok": True,
            "message": f"Thank you, {submission.full_name}! Your message has been received (Reference #{submission.id}).",
            "submission": {
                "id": submission.id,
                "subject": submission.get_subject_display(),
                "created_at": submission.created_at.isoformat(),
                "has_attachment": bool(submission.attachment),
            },
            "email_sent": email_sent,
        },
        status=201,
    )


def about(request):
    schemes = list(Scheme.objects.filter(is_active=True).order_by("name"))
    scheme_names = {s.name for s in schemes}
    scheme_items = []
    for code, note in [
        ("C-15", "Legacy scheme structure configured; materials are added as verified resources become available."),
        ("C-20", "Current core scheme with active subject structure and growing verified study materials."),
        ("C-25", "Upcoming scheme slot configured to accommodate newly introduced curriculum materials."),
    ]:
        matched = next((s for s in schemes if s.name == code), None)
        scheme_items.append(
            {
                "name": code,
                "slug": matched.slug if matched else code.lower(),
                "is_configured": code in scheme_names,
                "note": note,
            }
        )

    context = {
        "what_we_provide": ABOUT_WHAT_WE_PROVIDE,
        "schemes": scheme_items,
        "why_choose_us": ABOUT_WHY_CHOOSE_US,
        "team_members": ABOUT_TEAM_MEMBERS,
    }
    return render(request, "public/about.html", context)