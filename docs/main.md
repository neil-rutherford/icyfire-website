# Main Portal

## Purpose

This portal is built for users and has four main purposes.

1. It serves as a way for users to see all existing posts in all existing queues. (In order for a user to use this functionality, they must have `Read` permission.)
2. It serves as a way to create new posts and decide which queues they will be assigned to. (In order for a user to use this functionality, they must have `Create` permission.)
3. It serves as a way to update existing posts. (In order for a user to use this functionality, they must have `Update` permission.)
4. It serves as a way to delete existing posts. (In order for a user to use this functionality, they must have `Delete` permission.)

This is the main functionality behind IcyFire Social. Permissions are assigned by domain admins. All users have no permissions by default.

## Endpoints

### /dashboard

The Main Dashboard is the entrypoint into the Main portal. It provides a list of account aliases, post queues, and timeslot information. At the top of the dashboard, there are four buttons available to create posts. Sentry will record this as a `200`.

For aesthetic purposes, each post is truncated to 100 characters. If you would like to see the full post, you may click on the post text. To edit the post, click "Edit". To delete the post, click "Delete". As posts are published to social media, they are deleted from the queues.

If the user is an IcyFire contractor, they will be redirected to the sales dashboard. If IcyFire contractors would like to contribute to our internal social media, they may register with another email address and interact with the IcyFire platform as a user. Sentry will not record this redirection.

If you don't have `Read` permission, you will be redirected to a page titled "Insufficient permissions." Sentry will record this as a `403`. This is normal at the beginning and just means that your domain admin has not given you `Read` permission yet. When you are granted `Read` permission, you will be able to view the dashboard normally.

### /download-multimedia/{file_name}

This endpoint exists because the IcyFire website runs on Heroku. Heroku has an [ephemeral filesystem] (https://devcenter.heroku.com/articles/dynos#ephemeral-filesystem), which means that files written to disk may be erased when dynos are rebooted. We therefore use Dropbox for long-term file storage.

This background process downloads a file from Dropbox onto the Heroku filesystem so that it can be viewed in the browser. The `file_name` variable is expected to be a string with a file extension at the end. Sentry does not record this incident.

Example usage: `/download-multimedia/example.jpg` would download "example.jpg" from Dropbox to the `static/resources` file on Heroku. It would then display the image in the browser.

### /view/post/{platform}/{post_id}

This endpoint is used to view more details about any given post. The `post_id` variable is expected to be an integer, and the `platform` variable is expected to be one of the following lower-case strings:

- "facebook"
- "twitter"
- "tumblr"
- "reddit"

If everything goes smoothly, the post will be displayed. Sentry will record it as a `200`.

Example usage: `/view/post/facebook/45` would display the FacebookPost with `id=45`.

Possible errors:

- If you are redirected to the page titled "Insufficient permissions", you do not have `Read` permission. Talk to your domain admin.
- "ERROR: Post not found.": The database queried the `platform` and `post_id` provided and could not find anything. The post may have been deleted or there may have been a typo. Sentry will record it as a `404`.
- "ERROR: Malformed request; platform not found.": The `platform` variable was not one of the four accepted strings. There was probably a typo. Sentry will record this as a `400`.
- "ERROR: That post isn't part of your domain.": You are attempting to look at another domain's post and have been denied permission. Sentry will record this as a `403`.

### /pre/{post_type}/choose-queues

This endpoint helps users decide which queues to publish their post to. The `post_type` is expected to be one of the following lower-case strings:

- "short_text"
- "long_text"
- "image"
- "video"

If everything goes smoothly, the user will be redirected to the form page with "x queues on deck..." on top. (x correspnds to how many queues were selected.) Sentry does not record events on this page.

Example usage: `/pre/short_text/choose-queues` would prompt the user to choose queue(s) for their short text post.

Possible errors:

- "Talk to your domain about getting create permissions.": You don't have `Create` permission. Talk to your domain admin about changing this.
- "ERROR: Please select at least one queue.": In order to add a post to a social media queue, at least one queue needs to be selected.
- "ERROR: That post type doesn't exist.": The `post_type` variable was not one of the four accepted strings.

### /create/short-text/{queue_list}

Taking input from the "choose-queues" endpoint, this endpoint allows users to craft a short text post. The `queue_list` variable is expected to be a forward-slash-separated path object of cred ids that the post will be posted to. If everything goes smoothly, the user will be redirected to the Main Dashboard with a "Successfully queued!" message, and the post(s) will appear in the queue(s) indicated in the "choose-queues" stage. Sentry will record each queue addition as a `200`. (If one post was going to three queues, Sentry would generate three `200` logs.) The user's post count is incremented by one, regardless of how many queues the post is directed to.

Example usage: `/create/short-text/facebook_1/twitter_1/tumblr_2` would prepare to publish a short text post to FacebookCred #1, TwitterCred #1, and TumblrCred #2.

Possible errors:

- "Talk to your domain about getting create permissions.": You don't have `Create` permission. Talk to your domain admin about changing this.

### /create/long-text/{queue_list}

Taking input from the "choose-queues" endpoint, this endpoint allows users to craft a long text post. The `queue_list` variable is expected to be a forward-slash-separated path object of cred ids that the post will be posted to. If everything goes smoothly, the user will be redirected to the Main Dashboard with a "Successfully queued!" message, and the post(s) will appear in the queue(s) indicated in the "choose-queues" stage. Sentry will record each queue addition as a `200`. (If one post was going to three queues, Sentry would generate three `200` logs.) The user's post count is incremented by one, regardless of how many queues the post is directed to.

Example usage: `/create/long-text/facebook_1/tumblr_2` would prepare to publish a long text post to FacebookCred #1 and TumblrCred #2.

Possible errors:

- "Talk to your domain about getting create permissions.": You don't have `Create` permission. Talk to your domain admin about changing this.

### /create/image/{queue_list}

Taking input from the "choose-queues" endpoint, this endpoint allows users to craft an image post. The `queue_list` variable is expected to be a forward-slash-separated path object of cred ids that the post will be posted to. If everything goes smoothly, the user will be redirected to the Main Dashboard with a "Successfully queued!" message, and the post(s) will appear in the queue(s) indicated in the "choose-queues" stage. Sentry will record each queue addition as a `200`. (If one post was going to three queues, Sentry would generate three `200` logs.) The user's post count is incremented by one, regardless of how many queues the post is directed to.

Due to Heroku's ephemeral filesystem, image files are uploaded to Dropbox. They are transfered from the local `/static/resources` folder to the Dropbox `/multimedia/` folder for long-term storage. Because of this background process, multimedia posts take slightly longer than text posts.

Example usage: `/create/image/facebook_11/tumblr_22` would prepare to publish an image post to FacebookCred #11 and TumblrCred #22.

Possible errors:

- "Talk to your domain about getting create permissions.": You don't have `Create` permission. Talk to your domain admin about changing this.

### /create/video/{queue_list}

Taking input from the "choose-queues" endpoint, this endpoint allows users to craft a video post. The `queue_list` variable is expected to be a forward-slash-separated path object of cred ids that the post will be posted to. If everything goes smoothly, the user will be redirected to the Main Dashboard with a "Successfully queued!" message, and the post(s) will appear in the queue(s) indicated in the "choose-queues" stage. Sentry will record each queue addition as a `200`. (If one post was going to three queues, Sentry would generate three `200` logs.) The user's post count is incremented by one, regardless of how many queues the post is directed to.

Due to Heroku's ephemeral filesystem, video files are uploaded to Dropbox. They are transfered from the local `/static/resources` folder to the Dropbox `/multimedia/` folder for long-term storage. Because of this background process, multimedia posts take slightly longer than text posts.

Example usage: `/create/video/facebook_1` would prepare to publish an image post to FacebookCred #1.

Possible errors:

- "Talk to your domain about getting create permissions.": You don't have `Create` permission. Talk to your domain admin about changing this.

### /update/short-text/{platform}/{post_id}

This endpoint allows users to edit short text posts. The `post_id` variable is expected to be an integer, and the `platform` variable is expected to be one of the following lower-case strings:

- "facebook"
- "twitter"
- "tumblr"
- "reddit"

If all goes smoothly, the user will be redirected to the Main Dashboard and will see a message that says "Successfully updated!". Please note that editing a post will only change one post, so if a user posted in bulk, the other posts in that batch will be unaffected. Sentry will record this as a `200`.

Example usage: `/update/short-text/facebook/13` would allow the user to edit FacebookPost #13.

Possible errors:

- "Talk to your domain admin about getting update permissions.": You don't have `Update` permission. Talk to your domain admin about changing this.
- "ERROR: Post not found.": The database queried the `platform` and `post_id` provided and could not find anything. The post may have been deleted or there may have been a typo. Sentry will record it as a `404`.
- "ERROR: Malformed request.": The `platform` variable was not one of the four accepted strings. Sentry will record this as a `400`.
- "ERROR: That post isn't part of your domain.": You are attempting to look at another domain's post and have been denied permission. Sentry will record this as a `403`.

### /update/long-text/{platform}/{post_id}

This endpoint allows users to edit long text posts. The `post_id` variable is expected to be an integer, and the `platform` variable is expected to be one of the following lower-case strings:

- "facebook"
- "tumblr"
- "reddit"

If all goes smoothly, the user will be redirected to the Main Dashboard and will see a message that says "Successfully updated!". Please note that editing a post will only change one post, so if a user posted in bulk, the other posts in that batch will be unaffected. Sentry will record this as a `200`.

Example usage: `/update/long-text/facebook/135` would allow the user to edit FacebookPost #135.

Possible errors:

- "Talk to your domain admin about getting update permissions.": You don't have `Update` permission. Talk to your domain admin about changing this.
- "ERROR: Post not found.": The database queried the `platform` and `post_id` provided and could not find anything. The post may have been deleted or there may have been a typo. Sentry will record it as a `404`.
- "ERROR: Malformed request.": The `platform` variable was not one of the three accepted strings. Sentry will record this as a `400`.
- "ERROR: That post isn't part of your domain.": You are attempting to look at another domain's post and have been denied permission. Sentry will record this as a `403`.

### /update/image/{platform}/{post_id}

This endpoint allows users to edit image posts. The `post_id` variable is expected to be an integer, and the `platform` variable is expected to be one of the following lower-case strings:

- "facebook"
- "twitter"
- "tumblr"
- "reddit"

If all goes smoothly, the user will be redirected to the Main Dashboard and will see a message that says "Successfully updated!". Please note that editing a post will only change one post, so if a user posted in bulk, the other posts in that batch will be unaffected. Sentry will record this as a `200`. Also note that triggering an image edit deletes the image file from Dropbox, so if you edit an image post, please upload the image file again.

Example usage: `/update/image/twitter/135` would allow the user to edit TwitterPost #135.

Possible errors:

- "Talk to your domain admin about getting update permissions.": You don't have `Update` permission. Talk to your domain admin about changing this.
- "ERROR: Post not found.": The database queried the `platform` and `post_id` provided and could not find anything. The post may have been deleted or there may have been a typo. Sentry will record it as a `404`.
- "ERROR: Malformed request.": The `platform` variable was not one of the three accepted strings. Sentry will record this as a `400`.
- "ERROR: That post isn't part of your domain.": You are attempting to look at another domain's post and have been denied permission. Sentry will record this as a `403`.

### /update/video/{platform}/{post_id}

This endpoint allows users to edit video posts. The `post_id` variable is expected to be an integer, and the `platform` variable is expected to be one of the following lower-case strings:

- "facebook"
- "twitter"
- "tumblr"
- "reddit"

If all goes smoothly, the user will be redirected to the Main Dashboard and will see a message that says "Successfully updated!". Please note that editing a post will only change one post, so if a user posted in bulk, the other posts in that batch will be unaffected. Sentry will record this as a `200`. Also note that triggering a video edit deletes the video file from Dropbox, so if you edit a video post, please upload the video file again.

Example usage: `/update/image/twitter/135` would allow the user to edit TwitterPost #135.

Possible errors:

- "Talk to your domain admin about getting update permissions.": You don't have `Update` permission. Talk to your domain admin about changing this.
- "ERROR: Post not found.": The database queried the `platform` and `post_id` provided and could not find anything. The post may have been deleted or there may have been a typo. Sentry will record it as a `404`.
- "ERROR: Malformed request.": The `platform` variable was not one of the three accepted strings. Sentry will record this as a `400`.
- "ERROR: That post isn't part of your domain.": You are attempting to look at another domain's post and have been denied permission. Sentry will record this as a `403`.

### /delete/post/{platform}/{post_id}

This endpoint allows users to delete posts. The `post_id` variable is expected to be an integer, and the `platform` variable is expected to be one of the following lower-case strings:

- "facebook"
- "twitter"
- "tumblr"
- "reddit"

If all goes smoothly, the user will be redirected to the Main Dashboard and will see a message that says "Successfully deleted!". The offending post should also be gone from its queue. Please note that deleting a post will only affect one post, so if a user posted in bulk, the other posts in that batch will be unaffected. Sentry will record this as a `204`.

If the post is an image or video, the associated multimedia will be removed from Dropbox. Because IcyFire uploads a copy of the file for each queue, deletion of one post will not affect others.

Example usage: `/delete/post/tumblr/45` will delete TumblrPost #45, along with any associated multimedia (if any).

Possible errors:

- "Talk to your domain admin about getting delete permissions.": You don't have `Delete` permission. Talk to your domain admin about changing this.
- "ERROR: Malformed request.": The `platform` variable was not one of the three accepted strings. Sentry will record this as a `400`.
- "ERROR: That post isn't part of your domain.": You are attempting to look at another domain's post and have been denied permission. Sentry will record this as a `403`.

### /help

This endpoint directs the user to a list of help topics. Sentry does not record this page.

### /help/{topic}

This endpoint renders a specific help page. The `topic` variable is expected to be one of the following lower-case strings:

- "admin"
- "api"
- "auth"
- "errors"
- "legal"
- "main"
- "meta"
- "payment"
- "promo"
- "sales"
- "security"

Example usage: `/help/main` would load this page.

Possible errors:

- "Sorry, we couldn't find that help topic.": Either the `topic` variable was not one of the 11 accepted strings, or the help page does not exist. 