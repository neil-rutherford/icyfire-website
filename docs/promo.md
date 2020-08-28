# Promotional Portal

## Purpose

The Promotional Portal serves as the public-facing front of the IcyFire website. As well as advertising the product and providing information about IcyFire Technologies, it also collects analytic information about traffic.

## Endpoints

### /

This endpoint is the home page. It provides links to the product description, our "help others" page, our "what if" page, and our "do good" page. Sentry logs IP addresses of visitors with a `200`.

### /product

This endpoint is the product description. It advertises IcyFire Social and provides links to other pages. Sentry logs IP addresses of visitors with a `200`.

### /help-others

This endpoint discusses IcyFire's value, "Help Others", which is our unique value proposition to clients. Sentry logs IP addresses of visitors with a `200`.

### /what-if

This endpoint discusses IcyFire's value, "What If", which is how we question the status quo and develop new products. Sentry logs IP addresses of visitors with a `200`.

### /do-good

This endpoint discusses IcyFire's value, "Do Good", which is how we give back to the community. This page provides links to our "IcyFire People", "IcyFire Planet", and "IcyFire Profit" projects. Sentry logs IP addresses of visitors with a `200`.

### /contact-us

This endpoint provides contact information -- our physical address and email address. Sentry logs IP addresses of visitors with a `200`.

### /product/competition-weigh-in

This endpoint compares IcyFire Social to competitors' products and is part of our promotional strategy. Sentry logs IP addresses of visitors with a `200`.

### /careers

This endpoint renders a Denver agent job description. Sentry does not log these.

### /about

This endpoint tells more about IcyFire Technologies and our values. Sentry logs IP addresses of visitors with a `200`.

### /blog

This endpoint is a directory for all blog articles and is created dynamically by scanning the `templates/promo/articles` folder. Blog entries are organized by date, where the newest articles are at the top. Sentry logs IP addresses of visitors with a `200`.

### /blog/{article_path}&{article_title}

This endpoint renders a specific blog post. The `article_path` variable is expected to be a file name and extension, and the `article_title` variable is expected to be a string. 

Example usage: `blog/example.html&Example article` would load example.html and set the title as "Example article".

Possible errors:

- "Sorry, we couldn't find the article you were looking for.": Either the article has been removed or there was a typo.

### /landing/{audience}

This endpoint renders a specific landing page. The `audience` variable is expected to be a string. This functionality is not yet supported and is a planned addition for when we can collect customer stories.

Example usage: `/landing/plumbers` would load "promo/landing/plumbers.html".

Possible errors:

- If you are redirected to the home page, that landing page doesn't exist.

### /random-image/{image_type}

This endpoint displays a random promotional image. The `image_type` variable is expected to either be "scenic" or "people". 

Example usage: `/random-image/scenic` would render a random image from the "static/scenic_images" folder.

Possible errors:

- 404 error: The `image_type` variable was not one of the two accepted strings.

### /contact-sales

This endpoint allows interested customers to provide their contact information to the IcyFire sales team. On success, the user will be redirected to the home page with a message saying "Thanks for your interest."

### /product/make-suggestion

This endpoint redirects to a Google Form and allows users to make product suggestions.

### /product/demo

This endpoint allows visitors to log into a read-only account and see how IcyFire's own social queues work. On success, the user should be logged in and redirected to IcyFire's Main Dashboard.

Possible errors:

- "Sorry, the demo isn't available at this time.": The demo account has not been set up.

### /pricing

This endpoint provides information on how much the IcyFire Social product costs, as well as a link to the Service Agreement.

### /checkout

As of August 2020, this endpoint is incomplete. Normally, it would be the entrypoint into the online payment module, but that is still under construction. It currently redirects to the "contact sales" page and indicates an intent to buy to the agent.