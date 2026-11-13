import os
import shutil
import tempfile
from unittest.mock import patch

from django.core import mail
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import (
    ContactSubmission,
    Scheme,
    Branch,
    SchemeBranch,
    Semester,
    Subject,
    ResourceCategory,
    Resource,
)
from .admin import ResourceAdminForm


class AboutPageTests(TestCase):
    def setUp(self):
        Scheme.objects.get_or_create(name="C-15", defaults={"slug": "c-15", "is_active": True})
        Scheme.objects.get_or_create(name="C-20", defaults={"slug": "c-20", "is_active": True})
        Scheme.objects.get_or_create(name="C-25", defaults={"slug": "c-25", "is_active": True})

    def test_about_page_renders_required_sections_and_links(self):
        response = self.client.get(reverse("about"))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")

        self.assertNotIn("is on the way", html)
        for expected_text in [
            "About Diploma Study Hub",
            "Empowering Karnataka Diploma Students with Accessible and Organised Learning Resources.",
            "Our Mission",
            "Our Vision",
            "Subject-wise Notes",
            "Previous Year Question Papers",
            "Lab Manuals",
            "Official Syllabus",
            "Important Questions",
            "Solved Question Papers",
            "DTE Updates",
            "Who Can Use Our Platform?",
            "C-15",
            "C-20",
            "C-25",
            "Organised Subject-wise Resources",
            "Easy Navigation",
            "Free Access to Available Materials",
            "Semester-wise Learning Resources",
            "Student-friendly Interface",
            "Founder &amp; Developer",
            "Co-Founder &amp; Developer",
            "Start Your Learning Journey Today!",
            "Explore Study Materials",
            reverse("materials"),
        ]:
            self.assertIn(expected_text, html)

    def test_existing_routes_still_work(self):
        home_res = self.client.get(reverse("home"))
        self.assertEqual(home_res.status_code, 200)
        home_html = home_res.content.decode("utf-8")
        for num in range(1, 7):
            self.assertIn(f'<span class="sem-card__num">{num}</span>', home_html)
            self.assertIn(f'?semester={num}', home_html)
        self.assertIn("6 semesters", home_html)
        self.assertEqual(self.client.get(reverse("materials")).status_code, 200)


class ContactPageAndApiTests(TestCase):
    def setUp(self):
        cache.clear()
        self.temp_media = tempfile.mkdtemp()
        self.media_override = override_settings(MEDIA_ROOT=self.temp_media)
        self.media_override.enable()

    def tearDown(self):
        self.media_override.disable()
        shutil.rmtree(self.temp_media, ignore_errors=True)
        cache.clear()

    def test_contact_page_unconfigured_contact_details(self):
        with override_settings(
            CONTACT_INFO={
                "general_email": "",
                "support_email": "",
                "materials_email": "",
                "feedback_email": "",
                "support_phone": "",
                "office_address": "",
                "admin_notification_email": "",
            }
        ):
            response = self.client.get(reverse("contact"))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")

        self.assertNotIn("is on the way", html)
        self.assertIn("Get in Touch", html)
        self.assertIn("Official contact details will be announced soon.", html)
        self.assertNotIn("mailto:", html)
        self.assertNotIn("dev-only-insecure-key", html)

        for label in [
            "General Enquiries",
            "Technical Support",
            "Study Material Contribution",
            "Feedback and Suggestions",
            "General Enquiry",
            "Technical Issue",
            "Study Material Request",
            "Contribute Study Materials",
            "Feedback",
            "Other",
            "How can I download study materials?",
            "Can I contribute notes?",
            "How can I report incorrect study materials?",
            "Is Diploma Study Hub free?",
            "Together, Let's Make Learning Easier.",
            reverse("materials"),
        ]:
            self.assertIn(label, html)

    def test_contact_page_configured_contact_details(self):
        with override_settings(
            CONTACT_INFO={
                "general_email": "hello@diplomahub.example",
                "support_email": "",
                "materials_email": "",
                "feedback_email": "",
                "support_phone": "+910000000000",
                "office_address": "Bengaluru, Karnataka",
                "admin_notification_email": "",
            }
        ):
            response = self.client.get(reverse("contact"))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")
        self.assertIn("mailto:hello@diplomahub.example", html)
        self.assertIn("Bengaluru, Karnataka", html)

    def test_api_rejects_get_method(self):
        response = self.client.get(reverse("contact_submit_api"))
        self.assertEqual(response.status_code, 405)

    def test_valid_submission_without_attachment_saves_to_db(self):
        payload = {
            "full_name": "  Aarav   K  ",
            "email": "Aarav@Example.com",
            "subject": "general_enquiry",
            "message": "Hello, I would like to know when C-20 CSE Sem 5 notes will be added.",
            "website": "",
        }
        response = self.client.post(reverse("contact_submit_api"), data=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data["ok"])
        self.assertEqual(ContactSubmission.objects.count(), 1)

        sub = ContactSubmission.objects.first()
        self.assertEqual(sub.full_name, "Aarav K")
        self.assertEqual(sub.email, "aarav@example.com")
        self.assertEqual(sub.subject, "general_enquiry")
        self.assertIsNotNone(sub.created_at)
        self.assertFalse(sub.attachment)

    def test_valid_submission_with_pdf_attachment(self):
        pdf_file = SimpleUploadedFile(
            "../../evil_name.pdf",
            b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n",
            content_type="application/pdf",
        )
        response = self.client.post(
            reverse("contact_submit_api"),
            data={
                "full_name": "Kavya S",
                "email": "kavya@example.com",
                "subject": "contribute_study_materials",
                "message": "Sharing unit 1 notes PDF for review and verification.",
                "attachment": pdf_file,
            },
        )
        self.assertEqual(response.status_code, 201)
        sub = ContactSubmission.objects.first()
        self.assertTrue(bool(sub.attachment))
        self.assertEqual(sub.attachment_original_name, "evil_name.pdf")
        self.assertTrue(sub.attachment.name.startswith("contact_attachments/"))
        self.assertNotIn("..", sub.attachment.name)

    def test_invalid_inputs_return_400_and_do_not_save(self):
        response = self.client.post(
            reverse("contact_submit_api"),
            data={
                "full_name": "A",
                "email": "not-an-email",
                "subject": "invalid_choice",
                "message": "short",
            },
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data["ok"])
        self.assertIn("full_name", data["errors"])
        self.assertIn("email", data["errors"])
        self.assertIn("subject", data["errors"])
        self.assertIn("message", data["errors"])
        self.assertEqual(ContactSubmission.objects.count(), 0)

    def test_disallowed_file_extension_rejected(self):
        bad_file = SimpleUploadedFile(
            "payload.html",
            b"<script>alert(1)</script>",
            content_type="text/html",
        )
        response = self.client.post(
            reverse("contact_submit_api"),
            data={
                "full_name": "Test User",
                "email": "test@example.com",
                "subject": "technical_issue",
                "message": "Reporting an issue with an uploaded attachment test.",
                "attachment": bad_file,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("attachment", response.json()["errors"])
        self.assertEqual(ContactSubmission.objects.count(), 0)

    def test_spoofed_pdf_magic_bytes_rejected(self):
        spoofed_pdf = SimpleUploadedFile(
            "notes.pdf",
            b"<html><script>alert('xss')</script></html>",
            content_type="application/pdf",
        )
        response = self.client.post(
            reverse("contact_submit_api"),
            data={
                "full_name": "Test User",
                "email": "test@example.com",
                "subject": "contribute_study_materials",
                "message": "Trying to upload a spoofed PDF file to test backend validation.",
                "attachment": spoofed_pdf,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("attachment", response.json()["errors"])
        self.assertEqual(ContactSubmission.objects.count(), 0)

    def test_oversized_attachment_rejected(self):
        big_pdf = SimpleUploadedFile(
            "huge.pdf",
            b"%PDF-1.4\n" + (b"A" * (5 * 1024 * 1024 + 100)),
            content_type="application/pdf",
        )
        response = self.client.post(
            reverse("contact_submit_api"),
            data={
                "full_name": "Test User",
                "email": "test@example.com",
                "subject": "contribute_study_materials",
                "message": "Uploading an oversized PDF to verify file size enforcement.",
                "attachment": big_pdf,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("attachment", response.json()["errors"])
        self.assertEqual(ContactSubmission.objects.count(), 0)

    def test_honeypot_blocks_spam_submission(self):
        response = self.client.post(
            reverse("contact_submit_api"),
            data={
                "full_name": "Spam Bot",
                "email": "bot@example.com",
                "subject": "feedback",
                "message": "Buy cheap links now at spam website!",
                "website": "https://spam.example",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(ContactSubmission.objects.count(), 0)

    def test_duplicate_submission_blocked_with_409(self):
        payload = {
            "full_name": "Student One",
            "email": "student@example.com",
            "subject": "study_material_request",
            "message": "Please upload C-20 CSE Semester 4 Data Structures notes.",
        }
        first = self.client.post(reverse("contact_submit_api"), data=payload)
        second = self.client.post(reverse("contact_submit_api"), data=payload)

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 409)
        self.assertEqual(ContactSubmission.objects.count(), 1)

    def test_rate_limiting_blocks_after_max_submissions(self):
        for i in range(5):
            res = self.client.post(
                reverse("contact_submit_api"),
                data={
                    "full_name": "Student Rate",
                    "email": "rate@example.com",
                    "subject": "feedback",
                    "message": f"Feedback message number {i} with unique text content.",
                },
            )
            self.assertEqual(res.status_code, 201)

        blocked = self.client.post(
            reverse("contact_submit_api"),
            data={
                "full_name": "Student Rate",
                "email": "rate@example.com",
                "subject": "feedback",
                "message": "Sixth submission should hit the rate limiter.",
            },
        )
        self.assertEqual(blocked.status_code, 429)
        self.assertEqual(ContactSubmission.objects.count(), 5)

    def test_non_js_form_post_fallback_works(self):
        response = self.client.post(
            reverse("contact"),
            data={
                "full_name": "Fallback User",
                "email": "fallback@example.com",
                "subject": "other",
                "message": "Testing server-side POST fallback without JavaScript.",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Message sent successfully")
        self.assertEqual(ContactSubmission.objects.count(), 1)

    @override_settings(
        EMAIL_CONFIGURED=True,
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="noreply@diplomahub.example",
        CONTACT_INFO={"admin_notification_email": "admin@diplomahub.example"},
    )
    def test_emails_sent_when_configured(self):
        response = self.client.post(
            reverse("contact_submit_api"),
            data={
                "full_name": "Email Test",
                "email": "student@example.com",
                "subject": "general_enquiry",
                "message": "Testing acknowledgement and admin email notifications.",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()["email_sent"])
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[0].to, ["student@example.com"])
        self.assertEqual(mail.outbox[1].to, ["admin@diplomahub.example"])

    @override_settings(
        EMAIL_CONFIGURED=True,
        CONTACT_INFO={"admin_notification_email": "admin@diplomahub.example"},
    )
    def test_db_storage_succeeds_even_if_email_sending_fails(self):
        with patch("apps.core.views.EmailMessage.send", side_effect=RuntimeError("SMTP down")):
            response = self.client.post(
                reverse("contact_submit_api"),
                data={
                    "full_name": "Resilient Test",
                    "email": "student@example.com",
                    "subject": "technical_issue",
                    "message": "Testing that DB storage still succeeds if SMTP fails.",
                },
            )
        self.assertEqual(response.status_code, 201)
        self.assertFalse(response.json()["email_sent"])
        self.assertEqual(ContactSubmission.objects.count(), 1)


class QuestionPapersPageTests(TestCase):
    def setUp(self):
        self.temp_media = tempfile.mkdtemp()
        self.media_override = override_settings(MEDIA_ROOT=self.temp_media)
        self.media_override.enable()

        # Create valid test PDF file
        materials_dir = os.path.join(self.temp_media, "study_materials")
        os.makedirs(materials_dir, exist_ok=True)
        self.pdf_content = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"

        pdf_path_1 = os.path.join(materials_dir, "math_qp_2025.pdf")
        with open(pdf_path_1, "wb") as f:
            f.write(self.pdf_content)

        pdf_path_2 = os.path.join(materials_dir, "cs_qp_2024.pdf")
        with open(pdf_path_2, "wb") as f:
            f.write(self.pdf_content)

        # Structure
        self.scheme_c20 = Scheme.objects.create(name="C-20", slug="c-20", is_active=True)
        self.scheme_c15 = Scheme.objects.create(name="C-15", slug="c-15", is_active=True)

        self.branch_cse = Branch.objects.create(
            name="Computer Science & Engineering", short_name="CSE", slug="cse"
        )
        self.branch_mech = Branch.objects.create(
            name="Mechanical Engineering", short_name="MECH", slug="mech"
        )

        sb_cse = SchemeBranch.objects.create(scheme=self.scheme_c20, branch=self.branch_cse)
        sb_mech = SchemeBranch.objects.create(scheme=self.scheme_c20, branch=self.branch_mech)

        self.sem1_cse = Semester.objects.create(scheme_branch=sb_cse, number=1)
        self.sem2_cse = Semester.objects.create(scheme_branch=sb_cse, number=2)
        self.sem1_mech = Semester.objects.create(scheme_branch=sb_mech, number=1)

        self.sub_math = Subject.objects.create(
            semester=self.sem1_cse, code="20SC11T", name="Engineering Mathematics"
        )
        self.sub_cs = Subject.objects.create(
            semester=self.sem1_cse, code="20CS11T", name="Fundamentals of Computers"
        )
        self.sub_mech = Subject.objects.create(
            semester=self.sem1_mech, code="20ME11T", name="Engineering Mechanics"
        )

        # Categories
        self.cat_prev = ResourceCategory.objects.create(
            name="Previous Question Papers", slug="previous-question-papers"
        )
        self.cat_model = ResourceCategory.objects.create(
            name="Model Question Papers", slug="model-question-papers"
        )
        self.cat_notes = ResourceCategory.objects.create(
            name="Notes", slug="notes"
        )

        # Verified Question Papers with valid files
        self.qp1 = Resource.objects.create(
            title="Engineering Mathematics – Nov 2025 QP",
            subject=self.sub_math,
            category=self.cat_prev,
            file="study_materials/math_qp_2025.pdf",
            status="verified",
            is_active=True,
            exam_year=2025,
            exam_session="Nov/Dec",
        )

        self.qp2 = Resource.objects.create(
            title="Fundamentals of Computers – Model Paper 2024",
            subject=self.sub_cs,
            category=self.cat_model,
            file="study_materials/cs_qp_2024.pdf",
            status="verified",
            is_active=True,
            exam_year=2024,
            exam_session="Model Paper",
        )

        # Unverified QP (must be excluded)
        self.qp_pending = Resource.objects.create(
            title="Pending Mathematics Paper",
            subject=self.sub_math,
            category=self.cat_prev,
            file="study_materials/math_qp_2025.pdf",
            status="pending",
            is_active=True,
            exam_year=2023,
        )

        # Notes resource (must be excluded)
        self.notes_resource = Resource.objects.create(
            title="Engineering Mathematics Notes",
            subject=self.sub_math,
            category=self.cat_notes,
            file="study_materials/math_qp_2025.pdf",
            status="verified",
            is_active=True,
        )

        # QP with missing physical file (must be excluded)
        self.qp_missing_file = Resource.objects.create(
            title="Ghost Question Paper",
            subject=self.sub_math,
            category=self.cat_prev,
            file="study_materials/non_existent.pdf",
            status="verified",
            is_active=True,
            exam_year=2021,
        )

    def tearDown(self):
        self.media_override.disable()
        shutil.rmtree(self.temp_media, ignore_errors=True)

    def test_question_papers_page_renders_successfully(self):
        response = self.client.get(reverse("question_papers"))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")

        self.assertNotIn("is on the way", html)
        self.assertIn("Question Papers Library", html)
        self.assertIn("Karnataka DTE Examinations", html)
        self.assertIn("20SC11T", html)
        self.assertIn("Engineering Mathematics", html)
        self.assertIn("20CS11T", html)
        self.assertIn("Fundamentals of Computers", html)
        self.assertIn("2025", html)
        self.assertIn("2024", html)
        self.assertIn("Download", html)
        self.assertIn("View", html)

    def test_only_verified_valid_pdf_files_shown(self):
        response = self.client.get(reverse("question_papers"))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")

        self.assertIn("Engineering Mathematics – Nov 2025 QP", html)
        self.assertIn("Fundamentals of Computers – Model Paper 2024", html)
        # Excluded items
        self.assertNotIn("Pending Mathematics Paper", html)
        self.assertNotIn("Engineering Mathematics Notes", html)
        self.assertNotIn("Ghost Question Paper", html)

    def test_search_by_subject_code_and_name(self):
        # Search by code
        res_code = self.client.get(reverse("question_papers") + "?q=20SC11T")
        self.assertEqual(res_code.status_code, 200)
        self.assertContains(res_code, "Engineering Mathematics – Nov 2025 QP")
        self.assertNotContains(res_code, "Fundamentals of Computers – Model Paper 2024")

        # Search by name
        res_name = self.client.get(reverse("question_papers") + "?q=Computers")
        self.assertEqual(res_name.status_code, 200)
        self.assertContains(res_name, "Fundamentals of Computers – Model Paper 2024")
        self.assertNotContains(res_name, "Engineering Mathematics – Nov 2025 QP")

    def test_filter_by_scheme_branch_and_semester(self):
        res_scheme = self.client.get(reverse("question_papers") + "?scheme=c-20")
        self.assertEqual(res_scheme.status_code, 200)
        self.assertContains(res_scheme, "20SC11T")

        res_wrong_scheme = self.client.get(reverse("question_papers") + "?scheme=c-15")
        self.assertEqual(res_wrong_scheme.status_code, 200)
        self.assertContains(res_wrong_scheme, "No Question Papers Found")

        res_branch = self.client.get(reverse("question_papers") + "?branch=cse")
        self.assertEqual(res_branch.status_code, 200)
        self.assertContains(res_branch, "20SC11T")

        res_sem = self.client.get(reverse("question_papers") + "?semester=1")
        self.assertEqual(res_sem.status_code, 200)
        self.assertContains(res_sem, "20SC11T")

        res_empty_sem = self.client.get(reverse("question_papers") + "?semester=5")
        self.assertEqual(res_empty_sem.status_code, 200)
        self.assertContains(res_empty_sem, "No Question Papers Found")

    def test_filter_by_examination_year(self):
        res_2025 = self.client.get(reverse("question_papers") + "?year=2025")
        self.assertEqual(res_2025.status_code, 200)
        self.assertContains(res_2025, "Engineering Mathematics – Nov 2025 QP")
        self.assertNotContains(res_2025, "Fundamentals of Computers – Model Paper 2024")

        res_2024 = self.client.get(reverse("question_papers") + "?year=2024")
        self.assertEqual(res_2024.status_code, 200)
        self.assertContains(res_2024, "Fundamentals of Computers – Model Paper 2024")
        self.assertNotContains(res_2024, "Engineering Mathematics – Nov 2025 QP")

    def test_empty_state_with_reset_button(self):
        response = self.client.get(reverse("question_papers") + "?q=NoSuchSubjectExists")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No Question Papers Found")
        self.assertContains(response, "Reset Filters")
        self.assertContains(response, reverse("question_papers"))

    def test_pagination_and_query_preservation(self):
        # Create 10 more question papers to test pagination (> 9 items)
        materials_dir = os.path.join(self.temp_media, "study_materials")
        for i in range(10):
            pdf_name = f"page_test_{i}.pdf"
            with open(os.path.join(materials_dir, pdf_name), "wb") as f:
                f.write(self.pdf_content)
            Resource.objects.create(
                title=f"Extra Paper {i}",
                subject=self.sub_math,
                category=self.cat_prev,
                file=f"study_materials/{pdf_name}",
                status="verified",
                is_active=True,
                exam_year=2025,
            )

        # Page 1
        res_p1 = self.client.get(reverse("question_papers") + "?scheme=c-20")
        self.assertEqual(res_p1.status_code, 200)
        self.assertTrue(res_p1.context["page_obj"].has_other_pages())
        self.assertEqual(len(res_p1.context["question_papers"]), 9)
        self.assertContains(res_p1, "page=2")
        self.assertContains(res_p1, "scheme=c-20")

        # Page 2
        res_p2 = self.client.get(reverse("question_papers") + "?page=2&scheme=c-20")
        self.assertEqual(res_p2.status_code, 200)
        self.assertEqual(res_p2.context["page_obj"].number, 2)

    def test_resource_admin_form_secure_pdf_validation(self):
        # Disallow non-pdf extension
        bad_ext_file = SimpleUploadedFile(
            "script.exe", b"%PDF-1.4\nfake", content_type="application/octet-stream"
        )
        form_bad_ext = ResourceAdminForm(
            data={"title": "Test", "subject": self.sub_math.id, "category": self.cat_prev.id, "status": "verified", "language": "English"},
            files={"file": bad_ext_file},
        )
        self.assertFalse(form_bad_ext.is_valid())
        self.assertIn("file", form_bad_ext.errors)

        # Disallow fake PDF with wrong header
        fake_header_file = SimpleUploadedFile(
            "document.pdf", b"<html>malicious</html>", content_type="application/pdf"
        )
        form_fake = ResourceAdminForm(
            data={"title": "Test", "subject": self.sub_math.id, "category": self.cat_prev.id, "status": "verified", "language": "English"},
            files={"file": fake_header_file},
        )
        self.assertFalse(form_fake.is_valid())
        self.assertIn("file", form_fake.errors)

        # Allow valid PDF
        good_pdf = SimpleUploadedFile(
            "legit.pdf", self.pdf_content, content_type="application/pdf"
        )
        form_good = ResourceAdminForm(
            data={"title": "Test", "subject": self.sub_math.id, "category": self.cat_prev.id, "status": "verified", "language": "English"},
            files={"file": good_pdf},
        )
        self.assertTrue(form_good.is_valid(), form_good.errors)


