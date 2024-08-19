## Paypal Python API example
---

* Install packages
`pip install requirements.txt -r`

* Steps 
  1. Create Account and Sign in with *https://developer.paypal.com/*
  2. Login and go to Dashboard
  3. Click "apps & Credentials"
  4. "Create App"
  5. Find "Client ID" and "Client Secret"


* Set "Client ID" and "Client Secret" into '.env'

* Set "Redirect URL" and "scope"
  ![image](https://github.com/JoliLin/paypal_example/blob/main/img/paypal_set_redirect.png)

  ```
  -> Log in with Paypal
  -> Advanced Settings
  -> Add URL and select 'Information requested from customers'
  ```

* Notice
  * There is a testing 'Sandbox Account' in 'Testing Tools'. It can be used to test for payment.
