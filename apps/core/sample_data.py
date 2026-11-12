"""
DEVELOPMENT SAMPLE DATA ONLY.

Every value here is a stand-in so we can build and test the UI.
Subject codes are fake ("DEV-xxx"). In Phase 4 this file is deleted and
every list below comes from the database instead.
"""

SCHEMES = [
    {"slug": "c-15", "name": "C-15"},
    {"slug": "c-20", "name": "C-20"},
    {"slug": "c-25", "name": "C-25"},
]

BRANCHES = [
    {"slug": "cse", "name": "Computer Science Engineering", "icon": "bi-laptop"},
    {"slug": "ise", "name": "Information Science", "icon": "bi-hdd-network"},
    {"slug": "ece", "name": "Electronics & Communication", "icon": "bi-broadcast"},
    {"slug": "eee", "name": "Electrical & Electronics", "icon": "bi-lightning-charge"},
    {"slug": "mech", "name": "Mechanical Engineering", "icon": "bi-gear-wide-connected"},
    {"slug": "civil", "name": "Civil Engineering", "icon": "bi-building"},
    {"slug": "auto", "name": "Automobile Engineering", "icon": "bi-car-front"},
    {"slug": "other", "name": "Other Diploma Branches", "icon": "bi-grid-3x3-gap"},
]

SEMESTERS = [1, 2, 3, 4, 5, 6]

# Resource types shown in the hero "Quick access" panel.
CATEGORIES = [
    {"slug": "notes", "name": "Notes", "icon": "bi-journal-text", "blurb": "Subject & unit-wise"},
    {"slug": "question-paper", "name": "Question Papers", "icon": "bi-file-earmark-text", "blurb": "Previous years"},
    {"slug": "lab-manual", "name": "Lab Manuals", "icon": "bi-clipboard2-check", "blurb": "Practical records"},
    {"slug": "syllabus", "name": "Syllabus", "icon": "bi-list-check", "blurb": "Scheme-wise"},
    {"slug": "important-questions", "name": "Important Questions", "icon": "bi-star", "blurb": "Exam focused"},
    {"slug": "solved-paper", "name": "Solved Papers", "icon": "bi-check2-circle", "blurb": "With answers"},
]


def _res(title, subject, code, cat_slug, cat_name, icon, scheme, branch, sem,
         lang, fmt, uploaded, status="verified"):
    return {
        "title": title, "subject": subject, "code": code,
        "category_slug": cat_slug, "category": cat_name, "icon": icon,
        "scheme": scheme, "branch_short": branch, "semester": sem,
        "language": lang, "format": fmt, "uploaded": uploaded, "status": status,
    }


LATEST_MATERIALS = [
    _res("Unit 1 – Introduction to Data Structures", "Data Structures", "DEV-401", "notes", "Notes", "bi-journal-text", "C-20", "CSE", 4, "English", "PDF", "02 Nov 2026"),
    _res("Complete Notes – Unit 1 to 5", "Engineering Mathematics", "DEV-101", "notes", "Notes", "bi-journal-text", "C-20", "All", 1, "English", "PDF", "30 Oct 2026"),
    _res("Unit 3 Notes (Kannada)", "Applied Science", "DEV-102", "notes", "Notes", "bi-journal-text", "C-20", "All", 1, "Kannada", "PDF", "28 Oct 2026"),
    _res("Lab Manual – Programs 1 to 10", "DBMS Lab", "DEV-503", "lab-manual", "Lab Manual", "bi-clipboard2-check", "C-20", "CSE", 5, "English", "PDF", "26 Oct 2026"),
    _res("Unit 2 – Machines and Drives", "Electrical Machines", "DEV-302", "notes", "Notes", "bi-journal-text", "C-20", "EEE", 3, "English", "PDF", "25 Oct 2026", "under_verification"),
    _res("Unit 4 – Surveying Basics", "Surveying", "DEV-304", "notes", "Notes", "bi-journal-text", "C-20", "Civil", 3, "English", "PDF", "22 Oct 2026"),
]

QUESTION_PAPERS = [
    {"subject": "Data Structures", "code": "DEV-401", "scheme": "C-20", "branch": "CSE", "semester": 4, "exam": "Nov 2025", "language": "English"},
    {"subject": "Engineering Mathematics", "code": "DEV-101", "scheme": "C-20", "branch": "All", "semester": 1, "exam": "Nov 2025", "language": "English"},
    {"subject": "Database Management Systems", "code": "DEV-402", "scheme": "C-20", "branch": "CSE", "semester": 4, "exam": "Jun 2025", "language": "English"},
    {"subject": "Electrical Machines", "code": "DEV-302", "scheme": "C-20", "branch": "EEE", "semester": 3, "exam": "Nov 2024", "language": "English"},
    {"subject": "Strength of Materials", "code": "DEV-305", "scheme": "C-15", "branch": "Civil", "semester": 3, "exam": "Jun 2024", "language": "English"},
]

IMPORTANT_QUESTIONS = [
    _res("Unit-wise Important Questions", "Data Structures", "DEV-401", "important-questions", "Important Questions", "bi-star", "C-20", "CSE", 4, "English", "PDF", "01 Nov 2026"),
    _res("Most Asked Questions", "Engineering Mathematics", "DEV-101", "important-questions", "Important Questions", "bi-star", "C-20", "All", 1, "English", "PDF", "29 Oct 2026"),
    _res("Chapter-wise Important Questions", "Surveying", "DEV-304", "important-questions", "Important Questions", "bi-star", "C-20", "Civil", 3, "English", "PDF", "24 Oct 2026"),
]

RECENT_UPLOADS = [
    {"title": "Unit 1 – Introduction to Data Structures", "subject": "Data Structures", "category": "Notes", "when": "3 days ago"},
    {"title": "Previous QP – Nov 2025", "subject": "Data Structures", "category": "Question Paper", "when": "4 days ago"},
    {"title": "Lab Manual – Programs 1 to 10", "subject": "DBMS Lab", "category": "Lab Manual", "when": "1 week ago"},
    {"title": "Unit-wise Important Questions", "subject": "Data Structures", "category": "Important Questions", "when": "4 days ago"},
    {"title": "Solved Paper – Jun 2025", "subject": "Database Management Systems", "category": "Solved Paper", "when": "2 weeks ago"},
]

PREP_TOOLS = [
    {"name": "Important Questions", "icon": "bi-star", "blurb": "Unit-wise questions most useful for revision."},
    {"name": "Viva Questions", "icon": "bi-chat-square-text", "blurb": "Prepare for practical and lab viva."},
    {"name": "Solved Papers", "icon": "bi-check2-circle", "blurb": "Check your answers against solved papers."},
    {"name": "Quick Revision", "icon": "bi-lightning-charge", "blurb": "Short notes for the last few days."},
]
