# Domain Administrator Portal

## Purpose

This portal is built for domain administrators and has three main purposes.

1. It serves as an interface for admins to grant and revoke their team members' CRUD permissions.
2. It serves as a way for admins to monitor what is happening on their domains. This includes successful actions (200s) and attempted actions (403s).
3. If an admin sees something out of the ordinary, this allows them the ability to flag the problem and escalate it to IcyFire's security team.

We designed it this way so that domain admins could have more control over their own security. Additionally, we have more people monitoring for unusual activity, which is great for security.

## Endpoints

### /admin/dashboard

The Admin Dashboard is the entrypoint into the Admin console. It provides a list of users that are registered with your domain, as well as providing the opportunity to grant/revoke your users' CRUD permissions. Below the user list, there is a directory where administrators can monitor activity on their domain.

If the user is not an administrator, they will be redirected to the main user dashboard and the event will be recorded as a `403` in Sentry.

### /admin/{user_id}/+{permission}

This endpoint is used to grant a user a specific permission. The `user_id` variable is expected to be an integer, and the `permission` variable is expected to be one lower-case letter ("c" for "Create", "r" for "Read", "u" for "Update", and "d" for "Delete"). If everything goes smoothly, the permission will change and the user will be redirected to the Admin Console. Sentry will record it as a `200`.

Example usage: `/admin/1/+c` gives "create" permission to the user with `user_id = 1`.

Possible errors:

- "ERROR: Can't find that user": The database queried the `user_id` provided and could not find anything. The user may have been deleted or there may have been a typo. Sentry will record it as `404`.
- "ERROR: You don't have permission to do that": You are not an administrator and therefore do not have permission to access admin tools. Sentry will record it as a `403`.
- "ERROR: That user isn't part of your domain": The database queried the `user_id` provided and found a user, but your `domain_id` and their `domain_id` don't match. This has triggered a security warning (Sentry `403`) for the user's domain administrator.
- "ERROR: Not a valid permission": The `permission` variable was not in an expected format. Make sure the letter is lower-case and is a valid permission. Sentry will record this as a `400`.

### /admin/{user_id}/-{permission}

This endpoint is used to revoke a specific permission from a user. The `user_id` variable is expected to be an integer, and the `permission` variable is expected to be either one lower-case letter ("c" for "Create", "r" for "Read", "u" for "Update", and "d" for "Delete") or "kill" (to delete the user). If everything goes smoothly, the permission will change and the user will be redirected to the Admin Console. Sentry will record it as a `200`.

If you use the `-kill` method on yourself, it will do exactly what you expect it to. Your user account will be deleted and you will likely have to contact IcyFire to get a new domain admin account set up. TL;DR - Don't *EVER* use the `-kill` method on your own account.

Example usage: `/admin/1/-c` revokes "create" permission from the user with `user_id = 1`.

Possible errors:

- "ERROR: Can't find that user": The database queried the `user_id` provided and could not find anything. The user may have been deleted or there may have been a typo. Sentry will record it as `404`.
- "ERROR: You don't have permission to do that": You are not an administrator and therefore do not have permission to access admin tools. Sentry will record it as a `403`.
- "ERROR: That user isn't part of your domain": The database queried the `user_id` provided and found a user, but your `domain_id` and their `domain_id` don't match. This has triggered a security warning (Sentry `403`) for the user's domain administrator.
- "ERROR: Not a valid permission": The `permission` variable was not in an expected format. Make sure the letter is lower-case and is a valid permission. Sentry will record this as a `400`.

### /admin/sentry/escalate-ciso/{post_id}

This endpoint is used to call to the IcyFire security team for help. Anyone can use this method, not just domain admins. The `post_id` variable is expected to be an integer. If everything goes smoothly, the incident will be flagged and the user will be redirected to the Admin Dashboard. Sentry does not record this.

Example usage: `admin/sentry/escalate-ciso/23` looks up the incident with `Sentry.id = 23` and sets the flag variable to `True`.

Possible errors:

- "ERROR: Can't find that incident": The database queried the `post_id` provided and could not find anything. The incident may have been deleted or there may have been a typo.

### /admin/sentry/user/{user_id}

This endpoint is used to get basic information about a user's domain, email address, and post count. It also shows what they have been doing over the past 14 days so that domain admins can monitor for attacks or malicious attempts on their domains. If everything goes smoothly, the user will be redirected to a page titled "Get User Info" with the requested information. The page does not show all of the user's activity, just what s/he has done in the admin's domain. (If the user attempted to hack into Domain X, then the Domain X admin could see that. If the user was just going about their day on Domain Y, the Domain X admin would not be able to see that activity.) Sentry will record it as a `200`.

Example usage: `admin/sentry/user/253` shows information and activity about the user with `id = 253`.

Possible errors:

- "ERROR: You don't have permission to do that": You are not an administrator and therefore do not have permission to access admin tools. Sentry will record it as a `403`.
- "ERROR: Can't find that user": The database queried the `user_id` provided and could not find anything. The user may have been deleted or there may have been a typo. Sentry will record it as `404`.

### /admin/sentry/create/success

This endpoint is used to list all incidents where users successfully created posts over the past 14 days. If all goes smoothly, the user will be redirected to a page called "Successful Creations" that contains the requested information. Sentry will record this as a `200`.

If there is activity on this page, it means that users are successfully creating posts on behalf of your domain. It is normal to recognize the users on this page. If you recognize the users but the posts look suspicious, it may mean that an account is compromised (i.e. someone gained access to a bonafide user's account). To prevent further damage, you can go to your Admin Dashboard and remove the compromised user. If you don't recognize the user, it means that there has been a successful malicious attack on your domain. Unrecognized activity on this page constitutes a high-impact security incident; escalate the incident to the IcyFire security team immediately.

Possible errors:

- "ERROR: You don't have permission to do that": You are not an administrator and therefore do not have permission to access admin tools. Sentry will record it as a `403`.

### /admin/sentry/create/fail

This endpoint is used to list all incidents where users attempted to (but failed to) create posts over the past 14 days. If all goes smoothly, the user will be redirected to a page called "Attempted Creations" that contains the requested information. Sentry will record this as a `200`.

If there is activity on this page, it means that users tried to create posts but lacked sufficient permissions. If you recognize the users who are attempting this action, grant them "create" permission or talk to them about why they feel they should be able to create new posts. If you don't recognize the users attempting the action, it may indicate the early stages of a malicious attack. Unrecognized activity on this page constitutes a low-impact security incident; please monitor this activity but do not escalate unless it continues.

Possible errors:

- "ERROR: You don't have permission to do that": You are not an administrator and therefore do not have permission to access admin tools. Sentry will record it as a `403`.

### /admin/sentry/read/success

This endpoint is used to list all incidents where users successfully accessed their dashboards over the past 14 days. If all goes smoothly, the user will be redirected to a page called "Successful Reads" that contains the requested information. Sentry will record this as a `200`.

If there is activity on this page, it means that users are successfully accessing their dashboards and are seeing all of your domain's posts. It is normal to recognize the users on this page. If you don't recognize the user, it means that third parties have the ability to see your posts. Unrecognized activity on this page constitutes a medium-impact security incident; please escalate the incident to the IcyFire security team at your earliest convenience.

Possible errors:

- "ERROR: You don't have permission to do that": You are not an administrator and therefore do not have permission to access admin tools. Sentry will record it as a `403`.

### /admin/sentry/read/fail

This endpoint is used to list all incidents where users attempted to (but failed to) access their dashboards over the past 14 days. If all goes smoothly, the user will be redirected to a page called "Attempted Reads" that contains the requested information. Sentry will record this as a `200`.

If there is activity on this page, it means that users tried to access their dashboards but lacked sufficient permissions. All new users have no CRUD permissions by default, and when a new user registers, they are automatically redirected to their dashboard. Therefore, it is not unusual to see a lot of activity on this page, particularly if you have just created your domain and many users are registering. If you recognize the users who are attempting this action, grant them "read" permission (unless you don't want them to be able to access their dashboard). If you don't recognize the users attempting the action, it may indicate the early stages of a malicious attack. Unrecognized activity on this page constitutes a low-impact security incident; please monitor this activity but do not escalate unless it continues.

Possible errors:

- "ERROR: You don't have permission to do that": You are not an administrator and therefore do not have permission to access admin tools. Sentry will record it as a `403`.

### /admin/sentry/update/success

This endpoint is used to list all incidents where users successfully updated/edited posts over the past 14 days. If all goes smoothly, the user will be redirected to a page called "Successful Updates" that contains the requested information. Sentry will record this as a `200`.

If there is activity on this page, it means that users are successfully updating posts on behalf of your domain. It is normal to recognize the users on this page. If you recognize the users but the updated posts look suspicious, it may mean that an account is compromised (i.e. someone gained access to a bonafide user's account). To prevent further damage, you can go to your Admin Dashboard and remove the compromised user. If you don't recognize the user, it means that there has been a successful malicious attack on your domain. Unrecognized activity on this page constitutes a high-impact security incident; escalate the incident to the IcyFire security team immediately.

Possible errors:

- "ERROR: You don't have permission to do that": You are not an administrator and therefore do not have permission to access admin tools. Sentry will record it as a `403`.

### /admin/sentry/update/fail

This endpoint is used to list all incidents where users attempted to (but failed to) update posts on behalf of your domain over the past 14 days. If all goes smoothly, the user will be redirected to a page called "Attempted Updates" that contains the requested information. Sentry will record this as a `200`.

If there is activity on this page, it means that users tried to update posts but lacked sufficient permissions. If you recognize the users who are attempting this action, grant them "update" permission or talk to them about why they feel they should be able to update posts. If you don't recognize the users attempting the action, it may indicate the early stages of a malicious attack. Unrecognized activity on this page constitutes a low-impact security incident; please monitor this activity but do not escalate unless it continues.

Possible errors:

- "ERROR: You don't have permission to do that": You are not an administrator and therefore do not have permission to access admin tools. Sentry will record it as a `403`.

### /admin/sentry/delete/success

This endpoint is used to list all incidents where users successfully deleted posts over the past 14 days. If all goes smoothly, the user will be redirected to a page called "Successful Deletes" that contains the requested information. Sentry will record this as a `200`.

If there is activity on this page, it means that users are successfully deleting posts on behalf of your domain. It is normal to recognize the users on this page. If you recognize the users but the deleted posts look suspicious, it may mean that an account is compromised (i.e. someone gained access to a bonafide user's account). To prevent further damage, you can go to your Admin Dashboard and remove the compromised user. If you don't recognize the user, it means that there has been a successful malicious attack on your domain. There is unfortunately no way to retrieve deleted posts. Unrecognized activity on this page constitutes a high-impact security incident; escalate the incident to the IcyFire security team immediately. 

Possible errors:

- "ERROR: You don't have permission to do that": You are not an administrator and therefore do not have permission to access admin tools. Sentry will record it as a `403`.

### /admin/sentry/delete/fail

This endpoint is used to list all incidents where users attempted to (but failed to) delete posts on behalf of your domain over the past 14 days. If all goes smoothly, the user will be redirected to a page called "Attempted Deletes" that contains the requested information. Sentry will record this as a `200`.

If there is activity on this page, it means that users tried to delete posts but lacked sufficient permissions. If you recognize the users who are attempting this action, grant them "delete" permission or talk to them about why they feel they should be able to delete posts. If you don't recognize the users attempting the action, it may indicate the early stages of a malicious attack. Unrecognized activity on this page constitutes a low-impact security incident; please monitor this activity but do not escalate unless it continues.

Possible errors:

- "ERROR: You don't have permission to do that": You are not an administrator and therefore do not have permission to access admin tools. Sentry will record it as a `403`.

### /admin/sentry/permission/success

This endpoint is used to list all incidents where a user's permission was successfully changed in the past 14 days. If all goes smoothly, the user will be redirected to a page called "Successful Permission Changes" that contains the requested information. Sentry will record this as a `200`.

If there is activity on this page, it means that users are successfully changing permissions. In cybersecurity, this action is known as a privilege escalation attack and, unless otherwise stated, can be prosecuted under the Computer Fraud and Abuse Act. As domain admin, you should be the only user listed on this page. If you see something that you don't remember doing, it may mean that your account is compromised (i.e. someone has gained access to your account). If you don't recognize the user, it means that there has been a successful malicious attack on your domain. A compromised domain admin account and unrecognized activity on this page both constitute high-impact security incidents; escalate the incident to the IcyFire security team immediately.

Possible errors:

- "ERROR: You don't have permission to do that": You are not an administrator and therefore do not have permission to access admin tools. Sentry will record it as a `403`.

### /admin/sentry/permission/fail

This endpoint is used to list all incidents where someone attempted to (and failed to) change a user's permission in the past 14 days. If all goes smoothly, the user will be redirected to a page called "Attempted Permission Changes" that contains the requested information. Sentry will record this as a `200`.

If there is activity on this page, it means that a user tried to change another user's permissions but lacked sufficient permissions. In cybersecurity, this action is known as a privilege escalation attack and, unless otherwise stated, can be prosecuted under the Computer Fraud and Abuse Act. This page should be empty. Any activity on this page constitutes a medium-impact security incident; please escalate the incident to the IcyFire security team.

Possible errors:

- "ERROR: You don't have permission to do that": You are not an administrator and therefore do not have permission to access admin tools. Sentry will record it as a `403`.

### /admin/sentry/admin/success

This endpoint is used to list all incidents where a user successfully accessed the Admin Dashboard and all of its related tools in the past 14 days. If all goes smoothly, the user will be redirected to a page called "Successful Admin Console Access" that contains the requested information. Sentry will record this as a `200`.

If there is activity on this page, it means that people are accessing the admin console and all of its related tools (i.e. all of the tools listed on this page). As domain admin, you should be the only user listed on this page. If you see something that you don't remember doing, it may mean that your account is compromised (i.e. someone has gained access to your account). If you don't recognize the user, it means that there has been a successful malicious attack on your domain. A compromised domain admin account and unrecognized activity on this page both constitute high-impact security incidents; escalate the incident to the IcyFire security team immediately.

Possible errors:

- "ERROR: You don't have permission to do that": You are not an administrator and therefore do not have permission to access admin tools. Sentry will record it as a `403`.

### /admin/sentry/admin/fail

This endpoint is used to list all incidents where a user attempted to (and failed to) access the Admin Dashboard and all of its related tools in the past 14 days. If all goes smoothly, the user will be redirected to a page called "Attempted Admin Console Access" that contains the requested information. Sentry will record this as a `200`.

If there is activity on this page, it means that a user tried to access the admin console and all of its related tools (i.e. all of the tools listed on this page), but lacked sufficient permissions. This page should be empty. Any activity on this page constitutes a medium-impact security incident; please escalate the incident to the IcyFire security team.

Possible errors:

- "ERROR: You don't have permission to do that": You are not an administrator and therefore do not have permission to access admin tools. Sentry will record it as a `403`.

### /admin/sentry/creds/success

This endpoint is used to list all incidents where a user successfully made changes to the domain's social media credentials in the past 14 days. If all goes smoothly, the user will be redirected to a page called "Successful Credentials Access" that contains the requested information. Sentry will record this as a `200`.

If there is activity on this page, it means that a user successfully updated the domain's social media credentials. Due to the way we encode things, IcyFire prevents the editing of the credentials themselves, so this is likely changing the time slots. As domain admin, you should be the only user listed on this page. If you see something that you don't remember doing, it may mean that your account is compromised (i.e. someone has gained access to your account). If you don't recognize the user, it means that there has been a successful malicious attack on your domain. A compromised domain admin account and unrecognized activity on this page both constitute high-impact security incidents; escalate the incident to the IcyFire security team immediately.

Possible errors:

- "ERROR: You don't have permission to do that": You are not an administrator and therefore do not have permission to access admin tools. Sentry will record it as a `403`.

### /admin/sentry/creds/fail

This endpoint is used to list all incidents where a user attempted to (and failed to) make changes to the domain's social media credentials in the past 14 days. If all goes smoothly, the user will be redirected to a page called "Attempted Credentials Access" that contains the requested information. Sentry will record this as a `200`.

If there is activity on this page, it means that a user attempted to update the domain's social media credentials. Due to the way we encode things, IcyFire prevents the editing of the credentials themselves, so this is likely trying to changing the time slots. This page should be empty. Any activity on this page constitutes a medium-impact security incident; please escalate the incident to the IcyFire security team.

Possible errors:

- "ERROR: You don't have permission to do that": You are not an administrator and therefore do not have permission to access admin tools. Sentry will record it as a `403`.