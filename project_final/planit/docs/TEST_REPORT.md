# Test report (v1.4)

Automated suite: **104 tests** (`python manage.py test planner.tests`).

| File | Tests |
|---|---|
| test_domain.py | 7 |
| test_services.py | 10 |
| test_models.py | 10 |
| test_api.py | 12 |
| test_api_extended.py | 8 |
| test_auth.py | 14 |
| test_frontend_contract.py | 8 |
| test_v13.py | 28 |
| test_v14.py | 7 |
| **Total** | **104** |

## Environment note (honest)
The suite was run by the author's assistant on **Django 5.2.7**. `requirements.txt` pins **Django 6.1.2**, which could not be installed in that environment. Run the suite on your own install and record the result here:

```
python manage.py test planner.tests
Ran ___ tests ... OK   (Django ___ , Python ___ , date ___)
```

## Browser checks (Chromium, 1360px and 390px)
Login, sign-up pattern feedback, Today, Tasks (status counts), Month view, add exam with review tasks, duplicate, course template, no horizontal scroll.

## Not done
User evaluation (usability testing with real students) has not been performed.
