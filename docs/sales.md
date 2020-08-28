# Sales Portal

## Purpose

This portal is built for IcyFire sales contractors and serves three main purposes.

1. It serves as a way for contractors to monitor their monthly sales progress.
2. It serves as a way for contractors to record sales and generate receipts.
3. It serves as a way for contractors to gain access to IcyFire's leads.

Access to this portal is restricted to users who have a CRTA code. CRTA stands for Country-Region-Team-Agent and is a unique identifier for IcyFire sales contractors.

## Endpoints

### /sales/dashboard

The Sales Dashboard is the entrypoint into the Sales console. For agents, it provides a list of leads that they have been assigned, if available. For other contractors, it provides contact information for their team members.

It also provides a list of completed sales within that contractor's jurisdiction, as well as insight into how close they are to meeting their monthly goals and their projected earnings. Successful access is logged by Sentry as a `200`.

Possible errors:

- "ERROR: You don't have permission to do that.": The user account you are using doesn't have a CRTA code. Sentry logs this as a `403`.
- "ERROR: Couldn't process that request.": The CRTA code associated with your user account cannot be parsed. Talk to your supervisor. Sentry logs this as a `400`.

### /sales/lead/{lead_id}

This endpoint allows an agent to see more information about a lead. The `lead_id` variable is expected to be an integer. On success, the page will display the lead's contact information and background information about their position and company. Sentry doesn't record this.

Example usage: `/sales/lead/34` would display contact information for Lead #34.

Possible errors:

- "ERROR: You don't have permission to do that.": The CRTA code associated with this lead doesn't match your CRTA code. Sentry doesn't log this.
- "An unexpected error has occurred.": There is no CRTA code associated with your user account.

### /sales/contacted-lead/{lead_id}

This endpoint allows an agent to indicate that they have contacted a lead. The `lead_id` variable is expected to be an integer. On success, the page will redirect to the Sales Dashboard and flash "Nice! Keep up the good work." Sentry doesn't record this.

Example usage: `/sales/contacted-lead/34` would change Lead #34's status from "uncontacted" to "contacted".

Possible errors:

- "ERROR: You don't have permission to do that.": The CRTA code associated with this lead doesn't match your CRTA code. Sentry doesn't log this.

### /create/sale

This endpoint allows an agent to record a sale and allow a client access to the service. On success:

1. The total amount due is calculated based on which state the client is in.
2. The sale and total amount due are recorded in the database.
3. An activation code is generated and is used to create a new domain.
4. Using the sales data and the activation code, a PDF receipt is generated and uploaded to Dropbox.
5. The receipt is displayed in the browser.

Possible errors:

- "ERROR: Only IcyFire agents are able to create sales.": Either your user account doesn't have a CRTA code, or your CRTA code does not indicate that you are an agent.