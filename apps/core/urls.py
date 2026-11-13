from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),

    # TEMPORARY routes. Each one is replaced by a real view in its phase.
    path("materials/", views.materials, name="materials"),
    path("subject/<int:subject_id>/", views.subject_detail, name="subject_detail"),
    path("question-papers/", views.question_papers, name="question_papers"),
    path("syllabus/", views.coming_soon, {"title": "Syllabus"}, name="syllabus"),                       # Phase 3
    path("dte-updates/", views.coming_soon, {"title": "DTE Updates"}, name="dte_updates"),              # Phase 8
    path("exam-prep/", views.coming_soon, {"title": "Examination Preparation"}, name="exam_prep"),      # Phase 8
    path("search/", views.coming_soon, {"title": "Search"}, name="search"),                             # Phase 7
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("api/contact/", views.contact_submit_api, name="contact_submit_api"),
    # V2 routes (only linked when the matching feature flag is enabled)
    path("login/", views.coming_soon, {"title": "Login"}, name="login"),
    path("register/", views.coming_soon, {"title": "Register"}, name="register"),
    path("contribute/", views.coming_soon, {"title": "Contribute Material"}, name="contribute"),
    path("request-material/", views.coming_soon, {"title": "Request Material"}, name="request_material"),
]
