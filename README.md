# Selenium Captcha Solver
Usage example:

```
from scs.captcha import CaptchaSolver

driver.get('page with captcha')
captcha_solver = CaptchaSolver(
    driver='selenium driver', 
    google_service_account_credentials='your credentials', 
    google_project_id='your google project id'
)
captcha_solver.solve()
```
