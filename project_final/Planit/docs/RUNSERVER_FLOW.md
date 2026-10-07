# How Django Opens the Home Page

```text
Terminal
python manage.py runserver
        │
        ▼
manage.py
sets DJANGO_SETTINGS_MODULE=config.settings
        │
        ▼
config/settings.py
ROOT_URLCONF=config.urls
        │
        ▼
config/urls.py
path("", include("planner.urls"))
        │
        ▼
planner/urls.py
path("", views.today_page, name="today")
        │
        ▼
planner/views.py
today_page(request)
        │
        ▼
render(request, "planner/today.html", context)
        │
        ▼
HTML response
        │
        ▼
Browser loads base.html + today.html
        │
        ▼
api.js / ui.js / today.js
        │
        ▼
GET /api/today/
        │
        ▼
Django ORM + domain/services
        │
        ▼
JsonResponse
        │
        ▼
Fetch -> DOM
```

The browser chooses the URL; Django routing chooses the view; the view chooses the template. The server does not search for an HTML file automatically.
