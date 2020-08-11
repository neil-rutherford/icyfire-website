# Application Programming Interface (API)

## Purpose

There are three parts to the IcyFire queuing system -- the database, the user interface, and the worker servers. The database is where users' social media posts live. The user interface is the client-facing webpage that is used to collect data and store it in the database. When it is time to post, the worker server gets the post and publishes it to social media.

The IcyFire API allows the worker server to talk to the database in a secure way. Using the API, the worker server can get all of the information that it needs in an easily-parsable, machine-friendly format.

## Authentication Tokens

The IcyFire API uses authentication tokens for security purposes. To compartmentalize any breach, at least two tokens are required and each endpoint requires a different combination. There are four authentication tokens:

1. READ token
2. CRED token
3. DELETE token
4. SECURITY token

## Credential Encryption

Even with the authentication token system, we recognize that API calls between the database and the worker servers may be insecure. To add another layer of security, we encrypt social media credentials before we store them in our database. Even if an attacker intercepts the response from the database, they still will be unable to compromise the clients' social media accounts.

## Endpoints

### /api/_r/<timeslot_id>/auth={read_token}&{cred_token}&{server_id}

This endpoint is used to get the platform, the credentials, and the post sub-components. The `timeslot_id` variable is expected to be an integer, and the `read_token` and `cred_token` variables are both expected to be strings.

Example usage: `/api/_r/314/auth=RrEeAaDd&CcRrEeDd/1` returns the post associated with time slot #314. It provides two authentication tokens, "RrEeAaDd" as the READ token and "CcRrEeDd" as the CRED token. It also shows that the request is coming from Server #1.

If the request is successful, a JSON object will be returned with a `200` status code. The first part of the response is `platform`, which indicates what social media platform the post is meant for (i.e. `facebook`, `twitter`, `tumblr`, or `reddit`). The second part of the response is the credentials needed for that platform. Twitter, for example, would have four variables: `consumer_key`, `consumer_secret`, `access_key`, and `access_secret`. The final part of the response includes the post subcomponents, such as the body and links to multimedia. Sentry will record this as a `200`.

Possible errors:

- "ERROR: Malformed request; timeslot not found" (status code 400): The database queried the `timeslot_id` provided and could not find anything. This could be because that server hasn't been set up yet or because there was a typo. Sentry will record this as a `400`.
- "ERROR: Queue is empty" (status code 404): The time slot is set up correctly, but there is no post lined up to publish. This may be because the team is not adding enough content to keep up with the posting schedule. Sentry will record this as a `404`.
- "ERROR: Timeslot is empty" (status code 218): An internal response saying that while the request was properly formed, no domain has claimed the time slot and there is nothing to post. Sentry will record this as a `218`.
- "ERROR: Authentication token(s) incorrect" (status code 403): The API call cannot be completed because the READ token and/or CRED token is incorrect. Sentry will record this as a `403`.

### /api/_d/{timeslot_id}/auth={read_token}&{delete_token}&{server_id}

This endpoint is used to delete a particular post after it has been published. The `timeslot_id` variable is expected to be an integer, and the `read_token` and `delete_token` variables are both expected to be strings.

Example usage: `/api/_d/123/auth=rReEaAdD&DdEeLlEeTtEe&1` deletes the post associated with time slot #123. It provides two authentication tokens, "rReEaAdD" as the READ token and "DdEeLlEeTtEe" as the DELETE token. It also shows that the request is coming from Server #1.

If the request is successful, a short JSON response will be returned with a `204` status code. In the `error_details` variable, you will see: `SUCCESS: Post deleted.`. Sentry will record this as a `204`.

Possible errors:

- "ERROR: Malformed request; timeslot not found" (status code 400): The database queried the `timeslot_id` provided and could not find anything. This could be because that server hasn't been set up yet or because there was a typo. Sentry will record this as a `400`.
- "ERROR: Queue is empty" (status code 404): The time slot is set up correctly, but there is no post lined up to delete. This may be because the team is not adding enough content to keep up with the posting schedule. Sentry will record this as a `404`.
- "ERROR: Timeslot is empty" (status code 218): An internal response saying that while the request was properly formed, no domain has claimed the time slot and there is nothing to delete. Sentry will record this as a `218`.
- "ERROR: Authentication token(s) incorrect" (status code 403): The API call cannot be completed because the READ token and/or DELETE token is incorrect. Sentry will record this as a `403`.

### /api/_rs/auth={read_token}&{security_token}/query={argument}:{data}

This endpoint is used to access Sentry logs. The `timeslot_id` variable is expected to be an integer. The `read_token` and `security_token` variables are both expected to be strings. The `argument` variable is expected to be a string. The `data` variable can be a string or an integer, depending on the argument type.

Here are example use cases for each accepted argument:

- `sentry_id`: Sorts by ID and returns one incident. Data is expected as an integer.
    - Example usage: `/api/_rs/auth=ReAd&SeCuRiTy/query=sentry_id:23` returns Sentry incident #23.
- `timestamp`: Returns all incidents that occurred in the past x number of days. Data is expected as an integer.
    - Example usage: `/api/_rs/auth=ReAd&SeCuRiTy/query=timestamp:2` returns all incidents from the last 2 days.
- `ip_address`: Returns all incidents associated with a given IP address. Data is expected as a string.
    - Example usage: `/api/_rs/auth=ReAd&SeCuRiTy/query=ip_address:163.56.178.92` returns all incidents associated with IP address "163.56.178.92".
- `user_id`: Returns all incidents associated with a given user ID. Data is expected as an integer.
    - Example usage: `/api/_rs/auth=ReAd&SeCuRiTy/query=user_id:45` returns all incidents associated with user #45.
- `domain_id`: Returns all incidents associated with a given domain ID. Data is expected as an integer.
    - Example usage: `/api/_rs/auth=ReAd&SeCuRiTy/query=domain_id:163` returns all incidents associated with domain #163.
- `endpoint`: Returns all incidents associated with a specific endpoint. The naming convention follows the {blueprint.function_name} format. Data is expected as a string.
    - Example usage: `/api/_rs/auth=ReAd&SeCuRiTy/query=endpoint:auth.login` returns all incidents relating to user logins.
- `endpoint_prefix`: Returns all incidents associated with a specific portal. The naming convention follows the {blueprint} format. Data is expected as a string.
    - Example usage: `/api/_rs/auth=ReAd&SeCuRiTy/query=endpoint_prefix:auth` returns all incidents relating to the authentication portal.
- `status_code`: Returns all incidents that have a specific status code. Data is expected as an integer.
    - Example usage: `/api/_rs/auth=ReAd&SeCuRiTy/query=status_code:403` returns all unauthorized access across all monitored endpoints.
- `flag`: Returns all incidents with a specific flag value. Data is expected as a string.
    - Example usage: `/api/_rs/auth=ReAd&SeCuRiTy/query=flag:True` returns all incidents where the flag variable is set to True.

If the request is successful, a JSON response for each incident will be returned with a `200` status code. It will be recorded in Sentry as a `200`. Each incident will contain the following information:

```
{'id': result.id, 
'timestamp': result.timestamp, 
'ip_address': result.ip_address, 
'user_id': result.user_id, 
'domain_id': result.domain_id, 
'endpoint': result.endpoint, 
'status_code': result.status_code, 
'status_message': result.status_message, 
'flag': result.flag}
```

Possible errors:

- "ERROR: No results found" (status code 404): The database queried the `data` variable provided and could not find anything. Incidents may have been removed or there may have been a typo. Sentry will record this as a `404`.
- "ERROR: Malformed request; argument not found" (status code 400): The argument was not accepted or understood. There may have been a misspelling, or you are trying to query a term that is not yet supported. Sentry will record this as a `400`.
- ERROR: Authentication token(s) incorrect" (status code 403): The API call cannot be completed because the READ token and/or SECURITY token is incorrect. Sentry will record this as a `403`.