BlogClient Backend API Documentation
API Structure and Endpoints
BlogClient Backend API uses a RESTful structure. All API endpoints are accessible under the /api/ path.
Accounts

POST /api/accounts/register/: Register a new user
POST /api/accounts/login/: Log in a user
POST /api/accounts/logout/: Log out a user
GET /api/accounts/current-user/: Get current user details
PATCH /api/accounts/update-email/: Update user email
POST /api/accounts/delete-account/: Delete user account

Profiles

GET /api/profiles/: List all profiles
GET /api/profiles/<int:user_id>/: Get a specific profile
PATCH /api/profiles/<int:user_id>/: Update a profile

Posts

GET /api/posts/: List all posts
POST /api/posts/: Create a new post
GET /api/posts/<int:pk>/: Get a specific post
PATCH /api/posts/<int:pk>/: Update a post
DELETE /api/posts/<int:pk>/: Delete a post

Comments

GET /api/posts/<int:post_id>/comments/: List comments for a post
POST /api/posts/<int:post_id>/comments/: Create a comment on a post
PATCH /api/comments/<int:pk>/: Update a comment
DELETE /api/comments/<int:pk>/: Delete a comment

Ratings

POST /api/rate/: Create or update a rating for a post

Tags

POST /api/tags/create/: Create a new tag

Followers

POST /api/followers/follow/: Follow a user
DELETE /api/followers/follow/: Unfollow a user

Notifications

GET /api/notifications/: List notifications for the current user
PATCH /api/notifications/<int:pk>/mark-read/: Mark a notification as read
PATCH /api/notifications/mark-all-read/: Mark all notifications as read
DELETE /api/notifications/<int:pk>/delete/: Delete a notification

Authentication
The API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header of your requests:
Authorization: Bearer <your_token_here>
Rate Limiting
The API implements rate limiting to prevent abuse. Current limits are:

Anonymous users: 100 requests per day
Authenticated users: 1000 requests per day
Authentication attempts: 5 per minute

Pagination
List endpoints use pagination with a default page size of 10. You can specify a different page size using the page_size query parameter, up to a maximum of 100.
Filtering and Ordering
Many list endpoints support filtering and ordering. Check individual endpoint documentation for supported parameters.
Error Handling
The API returns appropriate HTTP status codes along with error messages in the response body for easier debugging.
Testing
Our API is extensively tested with 96% coverage. The test suite includes:

Unit tests for models, serializers, and views
Integration tests for API endpoints
Tests for authentication and permissions
Tests for complex logic (e.g., popularity calculations)

To run the test suite:
python manage.py test

For a detailed coverage report:
coverage run --source='.' manage.py test
coverage report

Versioning
Currently, the API does not use explicit versioning. Any significant changes will be communicated to API consumers well in advance.

Support
For any questions or issues, please open an issue in the GitHub repository.

Last updated: [2024-10-17]