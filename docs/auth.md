# Authentication Portal

## Purpose

The authentication portal performs the following tasks:

1. Manages new domain registration.
2. Manages new user registration and links new users to existing domains.
3. Manages user logins and session cookies.
4. Collects social media credentials and sets up timeslots.
5. Provides password reset services to users who forget their passwords.

## Credential Encryption

We encrypt social media credentials before we store them in the database. We use Password-Based Key Derivation Function 2 (PBKDF2), which is part of RSA Laboratories' Public-Key Cryptography Standards. We elected for this option because:

1. Legitimate users only need to compute once, while attackers will need to run billions of computations to decrypt it. Even if the database is compromised, the likelihood of attackers obtaining social media credentials by brute force is prohibitively low.
2. PBKDF2 requires a salt, which is randomly generated sequence of bytes. This helps prevent against pre-computed hash attacks.
3. It allows us to store and transport social media credentials safely. Even if our database is compromised or our communications are intercepted, attackers will be unable to decrypt the sensitive information without the password.

We store both variables required for this operation, `SECRET_KEY` and `SALT`, as environmental variables.

## Login Defense

To protect our users, we limit the number of login attempts per day. If the password for a given user account is entered incorrectly more than 7 times, the offending IP address is added to a blocklist. The blocklist refreshes at midnight (UTC time). Password reset functionality is not restricted by the blocklist.

Login defense functionality redirects to `/login-defense` and is recorded by Sentry as `endpoint = 'auth.login', status_code=303`.

## Endpoints

### /login

If the user is already logged in, they will be redirected to the user dashboard (unless a fresh login is required, like for editing and deleting time slots).

If the user has incorrectly entered their credentials, the page will refresh and they will have another opportunity to log in.

If the user has incorrectly entered their credentials more than 7 times, Login Defense functionality will be triggered. See the Login Defense section for more information.

Possible errors:

- "ERROR: Invalid email or password": The database queried the `email` and `password` values provided, and either there is no user with that email, the password is incorrect, or both. This could be because there was a typo or because your account has been deleted. If you suspect the latter, confirm with your domain admin.
- "Invalid email address": Make sure your submission is an email address with the following format: {email}@{domain}. (For example: steve@apple.com.)

### /logout

Logs the user out and redirects them to the IcyFire homepage.

### /register/domain

If the user is already logged in, they will be redirected to the user dashboard.

This endpoint is for domain admins. Registering a new domain actually does two things -- it generates a new Domain, and it generates a new user account with domain admin priviledges. The `Email`, `Password`, and `Verify password` fields are used to generate the user account; the `Choose a name for your domain` and `Activation code` fields generate the domain.

Here are specific requirements:

- Email: This needs to be a valid email so that we can contact you if needed.
- Password: This can be anything you want, as long as it is 8 characters or more. We recommend that you [choose a strong password] (https://blog.avast.com/strong-password-ideas) that hasn't been [seen in a breach before] (https://haveibeenpwned.com/Passwords).
- Verify password: Re-enter your password again to make sure there are no typos.
- Domain name: Choose a name for your domain. This is so that new users can connect to your domain when they register. This can be a maximum of 120 characters long.
- Activation code: This is on your receipt. If you have misplaced your receipt, please contact us.

Click "Register" when you are finished.

Possible errors:

- "Please use a different email address.": We checked and there is already an account that exists with that email address.
- "Activation code incorrect. Please try again or contact your agent for assistance.": The activation code entered does not match our records. Check for typos or contact us.
- "Invalid email address": Make sure your submission is an email address with the following format: {email}@{domain}. (For example: steve@apple.com.)
- "Field must be at least 8 characters long.": The password you entered is less than 8 characters long.
- "Field cannot be longer than 120 characters.": Either the email or domain name you entered are too long.
- "Passwords must match.": The `Password` and `Verify password` fields are different. Make sure there are no typos.
- "Please choose a different domain name.": We checked and there is already a domain that exists with that domain name.

### /register/user

If the user is already logged in, they will be redirected to the user dashboard.

This endpoint is for new users registering with an existing domain. The `Email`, `Password`, and `Verify password` fields are used to generate the user account; the `Domain name` is used to link the user to the domain. 

As a safety measure, all new users have no CRUD permissions by default. After registering, talk to your domain admin about giving you the permissions you need.

Here are specific requirements:

- Email: This needs to be a valid email so that we can contact you if needed.
- Password: This can be anything you want, as long as it is 8 characters or more. We recommend that you [choose a strong password] (https://blog.avast.com/strong-password-ideas) that hasn't been [seen in a breach before] (https://haveibeenpwned.com/Passwords).
- Verify password: Re-enter your password again to make sure there are no typos.
- Domain name: The name of the domain that you are trying to link to. If you don't know it, ask your domain admin.

Possible errors:

- "Please use a different email address.": We checked and there is already an account that exists with that email address.
- "Invalid email address": Make sure your submission is an email address with the following format: {email}@{domain}. (For example: steve@apple.com.)
- "Field must be at least 8 characters long.": The password you entered is less than 8 characters long.
- "Field cannot be longer than 120 characters.": The email you entered is too long.
- "Passwords must match.": The `Password` and `Verify password` fields are different. Make sure there are no typos.
- "That domain doesn't exist. Please try again or contact your administrator for assistance.": We checked and that domain name doesn't exist. There is either a typo or the domain has been removed. Talk to your coworkers and/or domain admin for possible solutions.

### /register/contractor

If the user is already logged in, they will be redirected to the user dashboard.

Unauthorized use of this endpoint may cause internal disruptions and will be prosecuted to the fullest extent of the law.

This endpoint is for new contractors registering with IcyFire. Registering as a contractor does two things -- it generates a user account with limited permissions, and depending on the information given, it generates the appropriate contractor object. The `Email`, `Password`, `Verify password` fields are used to generate the user account; the `First name`, `Last name`, and `Phone number` fields are used to generate the contractor object; and the remaining fields are used to generate both the user account and contractor object.

As a safety measure, all new contractors have no CRUD permissions by default. After registering, talk to your domain admin about giving you the permissions you need.

Here are specific requirements:

- What state are you in?: If you are the Nation Lead, select "Not applicable." Otherwise, select your state.
- What is the name of your team?: If you are the Nation Lead or are a Region Lead, select "Not applicable." Otherwise, select your team name. If you are unsure, ask your coworkers.
- What is your agent number?: If you are not an Agent, select "Not applicable." Otherwise, select your agent number. If you are unsure, ask your Team Lead.
- First name: Feel free to enter your preferred name if it is different from your legal name. This is to personalize our communications with you and present you to potential customers.
- Last name: Your surname.
- Phone number: Your cell phone number, without any hyphens.
- Email: Your IcyFire email address. We use this to communicate with you and to confirm your involvement with IcyFire.
- Password: This can be anything you want, as long as it is 8 characters or more. We recommend that you [choose a strong password] (https://blog.avast.com/strong-password-ideas) that hasn't been [seen in a breach before] (https://haveibeenpwned.com/Passwords).
- Verify password: Re-enter your password again to make sure there are no typos.

Possible errors:

- "Field cannot be longer than 50 characters.": First and last name lengths are limited to 50 characters.
- "Field must be between 10 and 10 characters long.": For the phone number, we are expecting 10 numbers with no hyphens.
- "Numbers only, please.": For the phone number, we are expecting 10 numbers with no hyphens.
- "We're expecting something like 1112223333, not 111-222-3333.": For the phone number, we are expecting 10 numbers with no hyphens.
- "Invalid email address": Make sure your submission is an email address with the following format: {email}@{domain}. (For example: steve@apple.com.)
- "Please use an IcyFire email address.": Your email needs to end in "@icy-fire.com". Contact your supervisor if you don't have one.
- "Field must be at least 8 characters long.": The password you entered is less than 8 characters long.
- "Passwords must match.": The `Password` and `Verify password` fields are different. Make sure there are no typos.
- "Please use a different email address.": An account already exists with the email address you provided. Begin password recovery or talk to your supervisor.
- "A user already exists with that CRTA code. Please contact your administrator.": CRTA stands for Country-Region-Team-Agent and is unique to each contractor. The location and team data you provided in the form helped generate your CRTA code. The CRTA code generated by the form already exists in the database, which is prohibiting your account from being generated. Please contact your supervisor.

### /reset-password-request

If the user is already logged in, they will be redirected to the user dashboard.

This endpoint is for users who want to change their password. Entering your email address and clicking "Request password reset" will send you an email with a unique reset token and instructions on how to finish the process. If the request is successful, you will be redirected to the login page and you will see text that says "Check your email for instructions to reset your password". The email will be from "noreply@icy-fire.com".

Possible errors:

- "Invalid email address": Make sure your submission is an email address with the following format: {email}@{domain}. (For example: steve@apple.com.)

### /reset-password/{token}

If the user is already logged in, they will be redirected to the user dashboard.

If the reset token matches the one in the database, you will be redirected to a form where you can reset your password. Enter your new password and click "Submit." If the request is successful, you will be redirected to the login page and you will see a message that says "Your password has been reset."

If the reset token does not match the one in the database, you will be redirected to the home page.

Possible errors:

- "Passwords must match.": The `Password` and `Verify password` fields are different. Make sure there are no typos.

### /register/link-social

