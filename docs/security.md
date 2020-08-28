# Security Portal

## Purpose

This portal is built for site administrators and the IcyFire security team. It is intended to assess security incidents as they occur in real-time, as well as allow team members to see flagged events. The Security Portal does not have a dashboard.

## Endpoints

### /security/flags

This endpoint is used to look at flagged incidents. If everything goes smoothly, the page will display all Sentry events where `flag=True`. Sentry will record this as a `200`.

Possible errors:

- "ERROR: You don't have permission to do that.": You are not part of the security team and are not authorized to view this page. Sentry will record this as a `403`.

### /security/sort-by/user/{user_id}

This endpoint is used to view a certain user's activity. The `user_id` variable is expected to be an integer. If everything goes smoothly, the page will display all Sentry events where `Sentry.user_id=user_id`. Sentry will record this as a `200`.

Example usage: `/security/sort-by/4` displays all Sentry records associated with User #4.

Possible errors:

- "ERROR: You don't have permission to do that.": You are not part of the security team and are not authorized to view this page. Sentry will record this as a `403`.

### /security/sort-by/domain/{domain_id}

This endpoint is used to see activity within a certain domain. The `domain_id` variable is expected to be an integer. If everything goes smoothly, the page will display all Sentry events where `Sentry.domain_id=domain_id`. Sentry will record this as a `200`.

Example usage: `/security/sort-by/domain/1` would show all activity within Domain #1.

Possible errors:

- "ERROR: You don't have permission to do that.": You are not part of the security team and are not authorized to view this page. Sentry will record this as a `403`.

### /security/sort-by/ip-address/{ip_address}

This endpoint is used to view a certain IP address's activity. The `ip_address` variable is expected to be a string in the form `xxx.xxx.xxx.xxx`. If everything goes smoothly, the page will display all Sentry events where `Sentry.ip_address=ip_address`. Sentry will record this as a `200`.

Example usage: `/security/sort-by/ip-address/36.217.231.123` would show all activity associated with the IP address 36.217.231.123.

Possible errors:

- "ERROR: You don't have permission to do that.": You are not part of the security team and are not authorized to view this page. Sentry will record this as a `403`.

### /security/sort-by/status-code/{status_code}

This endpoint is used to categorize security events by status code. The `status_code` variable is expected to be an integer. If everything goes smoothly, the page will display all Sentry events were `Sentry.status_code=status_code`. Sentry will record this as a `200`.

Example usage: `/security/sort-by/status-code/401` would display all failed logins.

Possible errors:

- "ERROR: You don't have permission to do that.": You are not part of the security team and are not authorized to view this page. Sentry will record this as a `403`.

### /security/view/{blueprint_name}

This endpoint is used to categorize events by blueprint. The `blueprint_name` variable is expected to be one of the following lowercase strings:

- "admin"
- "api"
- "auth"
- "legal"
- "main"
- "sales"
- "security"

If everything goes smoothly, the page will display all Sentry events for that endpoint prefix. Sentry will record this as a `200`.

Example usage: `/security/view/security` would display all Sentry events within the Security Portal.

Possible errors:

- "ERROR: You don't have permission to do that.": You are not part of the security team and are not authorized to view this page. Sentry will record this as a `403`.
- "ERROR: That blueprint is not supported.": The `blueprint_name` variable was not one of the seven accepted strings.