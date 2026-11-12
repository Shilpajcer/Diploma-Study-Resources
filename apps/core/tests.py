import shutil
import tempfile
from unittest.mock import patch

from django.core import mail
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import ContactSubmission, Scheme


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

