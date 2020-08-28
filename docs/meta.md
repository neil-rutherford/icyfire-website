# Meta Administrator Portal

## Purpose

This portal is built for site maintenance and has two main purposes.

1. It allows site administrators to see what is happening on the site on a broad scale.
2. It allows site administrators to interact directly with the database outside of the user experience. This allows administrators to manually override certain things by creating, reading, updating, and deleting.

The Meta Portal is explicitly off-limits to regular users. If a user who is not the site administrator attempts to use Meta functionality (with the exception of "System Status"), their account will be deleted. Sentry does not record incidents in the Meta Portal.

## Endpoints

### /meta/dashboard

The Meta Dashboard is the entrypoint into the Meta Portal. It provides options for creating new objects, seeing existing objects, as well as system maintenance options, such as bringing servers online and checking the status of the system.

### /meta/read/{model}

This endpoint is used to see all objects that exist within that model. The `model` variable is expected to be a lower-case string. The following strings are accepted models:

- "domain"
- "user"
- "country_lead"
- "region_lead"
- "team_lead"
- "agent"
- "sale"
- "lead"
- "timeslot"

If everything goes smoothly, you will see a list of all objects in that model.

Example usage: `/meta/read/user` returns a list of all users on the IcyFire site.

Possible errors:

- If you are redirected to the astronaut meme, your account has been deleted. This is because the Meta Portal is off-limits to anyone without specific permission.
- "Couldn't understand that model.": The string was not one of the accepted models.

### /meta/create/domain

This endpoint is used to create domains outside of the normal user experience. Keep in mind that Meta forms don't have validators. If everything goes smoothly, the form will be accepted, a new domain object will be created, and "Success" will flash as you redirect to the Meta Dashboard.

Possible errors:

- If you are redirected to the astronaut meme, your account has been deleted. This is because the Meta Portal is off-limits to anyone without specific permission.

### /meta/create/user

This endpoint is used to create users outside of the normal user experience. Keep in mind that Meta forms don't have validators. If everything goes smoothly, the form will be accepted, a new user object will be created, and "Success" will flash as you redirect to the Meta Dashboard.

Possible errors:

- If you are redirected to the astronaut meme, your account has been deleted. This is because the Meta Portal is off-limits to anyone without specific permission.

### /meta/create/country-lead

This endpoint is used to create country leads outside of the normal user experience. Keep in mind that Meta forms don't have validators. If everything goes smoothly, the form will be accepted, a new country lead object will be created, and "Success" will flash as you redirect to the Meta Dashboard.

Possible errors:

- If you are redirected to the astronaut meme, your account has been deleted. This is because the Meta Portal is off-limits to anyone without specific permission.

### /meta/create/region-lead

This endpoint is used to create region leads outside of the normal user experience. Keep in mind that Meta forms don't have validators. If everything goes smoothly, the form will be accepted, a new region lead object will be created, and "Success" will flash as you redirect to the Meta Dashboard.

Possible errors:

- If you are redirected to the astronaut meme, your account has been deleted. This is because the Meta Portal is off-limits to anyone without specific permission.

### /meta/create/team-lead

This endpoint is used to create team leads outside of the normal user experience. Keep in mind that Meta forms don't have validators. If everything goes smoothly, the form will be accepted, a new team lead object will be created, and "Success" will flash as you redirect to the Meta Dashboard.

Possible errors:

- If you are redirected to the astronaut meme, your account has been deleted. This is because the Meta Portal is off-limits to anyone without specific permission.

### /meta/create/agent

This endpoint is used to create agents outside of the normal user experience. Keep in mind that Meta forms don't have validators. If everything goes smoothly, the form will be accepted, a new agent object will be created, and "Success" will flash as you redirect to the Meta Dashboard.

Possible errors:

- If you are redirected to the astronaut meme, your account has been deleted. This is because the Meta Portal is off-limits to anyone without specific permission.

### /meta/create/sale

This endpoint is used to create sales outside of the normal user experience. Keep in mind that Meta forms don't have validators. If everything goes smoothly, the form will be accepted, a new sale object will be created, and "Success" will flash as you redirect to the Meta Dashboard.

Possible errors:

- If you are redirected to the astronaut meme, your account has been deleted. This is because the Meta Portal is off-limits to anyone without specific permission.

### /meta/create/lead

This endpoint is used to create leads outside of the normal user experience. Keep in mind that Meta forms don't have validators. If everything goes smoothly, the form will be accepted, a new lead object will be created, and "Success" will flash as you redirect to the Meta Dashboard.

Possible errors:

- If you are redirected to the astronaut meme, your account has been deleted. This is because the Meta Portal is off-limits to anyone without specific permission.

### /meta/create/server

This endpoint is used to create a week's worth of new timeslot objects, which in the eyes of the website, means that a server has been brought online. Of course, this is only one part of the equation, and an [IcyFire server] (https://github.com/neil-rutherford/icyfire-server) must be simultaneously brought online. If everything goes smoothly, the 10,080 timeslots will be created and "Successfully added Server x" will flash when you are redirected to the Meta Dashboard.

Possible errors:

- If you are redirected to the astronaut meme, your account has been deleted. This is because the Meta Portal is off-limits to anyone without specific permission.

### /meta/system-status

This endpoint is the only Meta resource that is open to all users. It uses Sentry logs to determine the status of the system, as well as provide useful data about the servers' actions. It divides the API calls into four groups:

- **Successful:** Successful calls include `200` and `404` status codes. In other words, the server is doing what it needs to do. `200` status codes indicate that the server successfully retrieved data from the API. `404` status codes mean that the server would have posted, but there was nothing in the queue (i.e. not IcyFire's fault).
- **Unallocated:** Unallocated calls include `218` status codes. In other words, the server is talking to the API, but no one has claimed that time slot. This indicates that IcyFire is losing money.
- **Failed:** Failed calls include `400` and `403` status codes. In other words, there is some problem between the API and the server. `400` status codes indicate that the requests are malformed and the API can't understand them. `403` status codes indicate that the authentication tokens are incorrect. (Note: Server-side, `403` status codes can also indicate that the Heroku dyno is restarting.)
- **Downtime:** Downtime is calculated as all recorded API calls minus the number of expected calls in a week. For example, if there were 9,576 total calls in a week, the downtime would be 5% (504 / 10,080). Note that if a server has been online for less than a week, downtime can be a misleading indicator of performance.

Possible errors:

- "Our system is not operational at this time": No timeslots exist on the website. See `/meta/create/server`.

### /meta/edit/domain/{domain_id}

This endpoint is used to edit domains outside of the normal user experience. The `domain_id` variable is expected to be an integer. Keep in mind that Meta forms don't have validators. If everything goes smoothly, the form will be accepted, the existing domain object will be updated, and "Success" will flash as you redirect to the Meta Dashboard.

Possible errors:

- If you are redirected to the astronaut meme, your account has been deleted. This is because the Meta Portal is off-limits to anyone without specific permission.

### /meta/edit/user/{user_id}

This endpoint is used to edit users outside of the normal user experience. The `user_id` variable is expected to be an integer. Keep in mind that Meta forms don't have validators. If everything goes smoothly, the form will be accepted, the existing user object will be updated, and "Success" will flash as you redirect to the Meta Dashboard.

Possible errors:

- If you are redirected to the astronaut meme, your account has been deleted. This is because the Meta Portal is off-limits to anyone without specific permission.

### /meta/edit/country-lead/{country_lead_id}

This endpoint is used to edit country leads outside of the normal user experience. The `country_lead_id` variable is expected to be an integer. Keep in mind that Meta forms don't have validators. If everything goes smoothly, the form will be accepted, the existing country lead object will be updated, and "Success" will flash as you redirect to the Meta Dashboard.

Possible errors:

- If you are redirected to the astronaut meme, your account has been deleted. This is because the Meta Portal is off-limits to anyone without specific permission.

### /meta/edit/region-lead/{region_lead_id}

This endpoint is used to edit region leads outside of the normal user experience. The `region_lead_id` variable is expected to be an integer. Keep in mind that Meta forms don't have validators. If everything goes smoothly, the form will be accepted, the existing region lead object will be updated, and "Success" will flash as you redirect to the Meta Dashboard.

Possible errors:

- If you are redirected to the astronaut meme, your account has been deleted. This is because the Meta Portal is off-limits to anyone without specific permission.

### /meta/edit/team-lead/{team_lead_id}

This endpoint is used to edit team leads outside of the normal user experience. The `team_lead_id` variable is expected to be an integer. Keep in mind that Meta forms don't have validators. If everything goes smoothly, the form will be accepted, the existing team lead object will be updated, and "Success" will flash as you redirect to the Meta Dashboard.

Possible errors:

- If you are redirected to the astronaut meme, your account has been deleted. This is because the Meta Portal is off-limits to anyone without specific permission.

### /meta/edit/agent/{agent_id}

This endpoint is used to edit agents outside of the normal user experience. The `agent_id` variable is expected to be an integer. Keep in mind that Meta forms don't have validators. If everything goes smoothly, the form will be accepted, the existing agent object will be updated, and "Success" will flash as you redirect to the Meta Dashboard.

Possible errors:

- If you are redirected to the astronaut meme, your account has been deleted. This is because the Meta Portal is off-limits to anyone without specific permission.

### /meta/edit/sale/{sale_id}

This endpoint is used to edit sales outside of the normal user experience. The `sale_id` variable is expected to be an integer. Keep in mind that Meta forms don't have validators. If everything goes smoothly, the form will be accepted, the existing sale object will be updated, and "Success" will flash as you redirect to the Meta Dashboard.

Possible errors:

- If you are redirected to the astronaut meme, your account has been deleted. This is because the Meta Portal is off-limits to anyone without specific permission.

### /meta/edit/lead/{lead_id}

This endpoint is used to edit leads outside of the normal user experience. The `lead_id` variable is expected to be an integer. Keep in mind that Meta forms don't have validators. If everything goes smoothly, the form will be accepted, the existing lead object will be updated, and "Success" will flash as you redirect to the Meta Dashboard.

Possible errors:

- If you are redirected to the astronaut meme, your account has been deleted. This is because the Meta Portal is off-limits to anyone without specific permission.

### /meta/delete/{model}/{id}

This endpoint is used to delete existing objects outside of the normal user experience. The `id` variable is expected to be an integer, and the `model` variable is expected to be one of the following lower-case strings:

- "domain"
- "user"
- "country_lead"
- "region_lead"
- "team_lead"
- "agent"
- "sale"
- "lead"

If everything goes smoothly, the existing object will be deleted, and "Success" will flash as you redirect to the Meta Dashboard.

Possible errors:

- "Couldn't understand that model": The model variable was not one of the accepted strings.