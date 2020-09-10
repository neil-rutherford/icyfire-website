# Payments Portal

## Purpose

This portal is built for new and existing customers and has x purposes:

1. It allows new customers to initiate subscriptions.
2. It allows existing customers to automatically renew subscriptions.
3. When automatic billing fails, it allows existing customers to add new billing information.

The payments portal currently only supports customers in the United States. In our next release, we plan to offer Mandarin language support so that audiences in Mainland China can use our services.

## Endpoints

### /pre/us/new/checkout

This endpoint is the entrypoint into the payments module for new customers. It is a landing page that is used to:

1. Determine state sales tax rate, if applicable
2. Create a Stripe `Customer` object
3. Create IcyFire `Sale` and `Domain` objects
4. Set IcyFire's `Domain.stripe_customer_id` equal to Stripe's `Customer.id`
5. Generate an activation code for the new domain
6. Populate a receipt/service agreement with relevant customer and activation information
7. Store the receipt file to Dropbox as `receipts/{UTC timestamp (YYYYMMDD format)}_{Company name}_sale_online.pdf`
8. Pass variables to the checkout page for Stripe payment processing

### /us/checkout?sigma={state}&filename={filename}&domain={domain_id}

This endpoint is used to load payment processing information for the Stripe checkout page. The `state` variable is expected to be a string. The `filename` variable is expected to be a string that corresponds with the receipt's file name. The `domain_id` variable is expected to be an integer that corresponds to the Domain object that was created on the landing page. If everything goes smoothly, a page with a functional "Buy now" button will appear.

Example usage #1: `/us/checkout?sigma=NA&filename=IcyFire Technologies, LLC_20200911_sale_online.pdf&domain=1` would load payment processing information for IcyFire Technologies, LLC. The sales tax would be 0% (Colorado doesn't levy taxes on SaaS, and this was determined at the entrypoint landing page), the receipt is stored at the filename location, and the domain ID helps link IcyFire and Stripe's tracking processes.

Example usage #2: `/us/checkout?sigma=New York&filename=WeWork, Inc._20201010_sale_online.pdf&domain=2` would load payment processing information for WeWork. The sales tax would be 4%, the receipt is stored at the filename location, and the domain ID helps link IcyFire and Stripe's tracking processes.

Clicking "Buy now" redirects to the Stripe checkout page, which is not part of the IcyFire domain. IcyFire partners with Stripe for payment processing, and they have a very straightforward interface on the checkout page. If you have any questions about the checkout page, please contact Stripe customer service.

Possible errors:

- "ERROR: State is required.": There is no information in the `state` variable, making it impossible to calculate the amount of sales tax to add.

### /success?filename={filename}&domain={domain_id}?session_id={checkout_session_id}

This endpoint is displayed when payments are successful. The `filename` variable is expected to be a string that corresponds with the receipt's file name. The `domain_id` is expected to be an integer that corresponds with the Domain object that was created in the first step. The `checkout_session_id` variable is expected to be a string provided by Stripe upon completion of payment processing. If everything goes smoothly, a page with a populated receipt will appear in the browser.

Example usage: `/success?filename=WeWork, Inc._20201010_sale_online.pdf&domain=2?session_id=Ch3cK0u7535510N1d` would mean that WeWork's payment was successful with the Session ID code Ch3cK0u7535510N1d. WeWork's receipt for $1,040 would be displayed in the browser.

Errors are caught on the Stripe checkout page. This page is only routed to if payment is successful.

### /stripe-webhook

This endpoint listens for webhooks, or automated messages, from Stripe. When payments are successful, Stripe sends a webhook to this address, which IcyFire then uses to update the domain's subscription information. This is used for all payment processing on IcyFire's end, and includes automatic billing. Since this is a webhook listener, it does not render a webpage and instead only prints to stdout. On success, it would look like this on the console:

```py
WEBHOOK CALLED
Added one year to Domain 2
```
Possible errors:

- "REQUEST TOO BIG": The size of the content is over 1 MB. The listener has aborted with a `400` HTTP status code.
- "INVALID PAYLOAD": There was an error with the message. The listener has returned a `400` HTTP status code.
- "INVALID SIGNATURE": This is not an authentic message from Stripe. The listener has returned a `400` HTTP status code.

### /us/renew?domain={domain_id}

This endpoint is used when customers need to manually renew their subscription. There can be many use cases for this, the most common of which being an expired card. The `domain_id` variable is expected to be an integer, corresponding to the existing domain's ID. If everything goes smoothly, a new `Sale` object will be created using the old sale information, a new receipt will be generated, and the user will be redirected to the checkout page.

Example usage: `/us/renew?domain=3` would prepare the payment process for Domain #3.