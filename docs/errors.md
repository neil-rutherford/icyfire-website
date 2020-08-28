# Error Messages

## Generic

### Page not found

The resource you are looking for does not exist. This could be because it was deleted, or because there is a typo in your URL.

### Unexpected error

The page crashed due to a technical error. Site administrators have been notified and will begin fixing the problem as soon as possible. You may also [report this issue] (https://icy-fire.com/product/make-suggestion) to make sure we're aware of it. We apologize for the inconvenience.

## Status codes

### 218

218s are specific to API functionality and indicate that while everything was successful, no company has claimed that timeslot. IcyFire uses this internally to determine how our sales efforts are doing and when we need to bring new servers online.

### 303

303s are specific to login defense functionality and occur when a user is redirected away from the login page to the login defense page. We look at 303s and 401s to identify and protect against unauthorized logins.

### 400

400 errors occur when the program receives an input it is not expecting. (In real life, a 400 error is like asking a kid what his favorite color is and him saying "I like pasta".) Within the IcyFire application, examples of this include:

- **ADMIN:** "Not a valid permission"
    - The `permission` variable was not in an expected format. Make sure the letter is lower-case and is a valid permission.
- **API:** "Malformed request; timeslot not found"
    - The database queried the `timeslot_id` provided and could not find anything. This could be because that server hasn't been set up yet or because there was a typo.
- **API:** "Malformed request; argument not found"
    - The argument was not accepted or understood. There may have been a misspelling, or you are trying to query a term that is not yet supported.
- **AUTH:** "Malformed request; platform not found"
    - The `platform` variable was not one of the four accepted strings.
- **MAIN:** "Malformed request; platform not found"
    - The `platform` variable was not one of the four accepted strings.
- **SALES:** "Couldn't process that request"
    - The CRTA code associated with your user account cannot be parsed. Talk to your supervisor.

### 401

401 errors are specific to login functionality and mean that an incorrect login has occurred.

### 403

403 errors occur when someone tries to do something they don't have permission to do. (In real life, a 403 error is like forbidding a kid from eating cookies and then finding them with their hand in the cookie jar.) Within the IcyFire application, examples of this include:

- **ADMIN:** "You don't have permission to do that"
    - You are not an administrator and therefore do not have permission to access admin tools.
- **API:** "Authentication token(s) incorrect"
    - _READ:_ The API call cannot be completed because the READ token and/or CRED token is incorrect.
    - _DELETE:_ The API call cannot be completed because the READ token and/or DELETE token is incorrect.
    - _SECURITY:_ The API call cannot be completed because the READ token and/or SECURITY token is incorrect.
- **AUTH:** "You don't have permission to do that"
    - You are not a domain admin. Only domain admins are able to handle social accounts.
- **MAIN:** "That post isn't part of your domain"
    - You are attempting to access another domain's post and have been denied permission.
- **MAIN:** "Talk to your domain about getting X permissions"
    - You don't have X permission. Talk to your domain administrator.
- **SALES:** "You don't have permission to do that"
    - The user account you are using doesn't have a CRTA code, or...
    - The CRTA code associated with this lead doesn't match your CRTA code.
- **SALES:** "Only IcyFire agents are able to create sales."
    - The website is denying you the ability to create a sale because it detects you are not an IcyFire agent.
- **SECURITY:** "You don't have permission to do that."
    - You are not part of the security team and are not authorized to view this page.

### 404

404 errors occur when the thing that is being searched for doesn't exist. (In real life, a 404 error would be like a kid asking you where you parked your Lamborghini and you saying, "What Lamborghini?") Within the IcyFire application, examples of this include:

- **ADMIN:** "Can't find that user"
    - The database queried the `user_id` provided and could not find anything. The user may have been deleted or there may have been a typo.
- **ADMIN:** "Can't find that incident"
    - The database queried the `post_id` provided and could not find anything. The incident may have been deleted or there may have been a typo.
- **API:** "Queue is empty"
    - The time slot is set up correctly, but there is no post lined up to publish. This may be because the team is not adding enough content to keep up with the posting schedule.
- **API:** "No results found"
    - The database queried the `data` variable provided and could not find anything. Incidents may have been removed or there may have been a typo.
- **MAIN:** "Post not found"
    - The database queried the `platform` and `post_id` provided and could not find anything. The post may have been deleted or there may have been a typo.
- **PROMO:** The `image_type` variable was not one of the two accepted strings.