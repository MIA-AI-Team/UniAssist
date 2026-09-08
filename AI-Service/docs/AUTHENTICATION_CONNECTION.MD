## 1. How authentication works

The backend uses **JWT Bearer authentication**.

```text
Register
   ↓
User created in database
   ↓
Login
   ↓
Backend verifies email/password
   ↓
JWT returned
   ↓
Frontend sends JWT with protected requests
   ↓
Backend verifies JWT + checks permissions
```

There are currently **no refresh tokens**.

---

## 2. Auth endpoints

| Endpoint                  | Purpose                 |
| ------------------------- | ----------------------- |
| `POST /api/auth/register` | Create an account       |
| `POST /api/auth/login`    | Login and receive a JWT |



## 3. Authentication smoke test

The authentication workflow can be tested independently using the **auth smoke test**.
```
uvicorn backend.auth_smoke_test:app --reload --host 127.0.0.1 --port 8000
```

The smoke test creates a small FastAPI application and mounts the authentication router:

```python
app.include_router(auth_router, prefix="/api", tags=["Authentication"])
```


The smoke test also includes protected routes to verify that JWT authentication and role authorization work correctly.

### Protected routes

```text
GET /users/me
GET /admin/dashboard
```

### `/users/me`

Requires a valid JWT but accepts **any authenticated user**.

```python
@app.get("/users/me")
async def get_my_profile(
    current_user: Annotated[User, Depends(get_current_user)]
):
```

It returns:

```json
{
  "id": 42,
  "name": "Alice Chen",
  "email": "alice@uni.edu",
  "role": "student"
}
```

### `/admin/dashboard`

Requires the user to have the `admin` role:

```python
@app.get("/admin/dashboard")
async def admin_dashboard(
    current_user: Annotated[User, Depends(require_roles(["admin"]))]
):
```

A non-admin user receives:

```text
403 Forbidden
```

---

## 4. Register

### `POST /api/auth/register`

Creates a user and their role-specific database record.

### Request

```json
{
  "name": "Alice Chen",
  "email": "alice@uni.edu",
  "password": "hunter22ab",
  "role": "student",
  "student_number": "S12345",
  "cohort_year": 2026,
  "major": "Computer Science"
}
```

### Roles

```text
admin
professor
teaching_assistant
student
```

Students require:

* `student_number`
* `cohort_year`
* `major`

Staff require:

* `staff_role`
* `department`

### Response

```json
{
  "id": 42,
  "name": "Alice Chen",
  "email": "alice@uni.edu",
  "role": "student",
  "message": "Account created successfully."
}
```

Registration does **not** return a JWT. The frontend should call `/api/auth/login` afterward.

### Errors

| Status | Meaning                                 |
| ------ | --------------------------------------- |
| `400`  | Email already registered                |
| `422`  | Invalid role or missing required fields |

---

## 5. Login

### `POST /api/auth/login`

Verifies the user's email and password and returns a JWT.

### Request

```json
{
  "email": "alice@uni.edu",
  "password": "hunter22ab"
}
```

### Response

```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "user_id": 42,
  "role": "student",
  "name": "Alice Chen"
}
```

### Errors

| Status | Meaning                   |
| ------ | ------------------------- |
| `401`  | Invalid email or password |

---

## 6. Using the JWT

Every protected endpoint should receive the token through the `Authorization` header:

```http
Authorization: Bearer <access_token>
```

### JavaScript example

```javascript
fetch("/users/me", {
  headers: {
    Authorization: `Bearer ${token}`
  }
});
```

The frontend should attach the token to every protected API request.

---

## 7. Authentication vs authorization

The backend handles both:

### Authentication

**"Who are you?"**

The JWT identifies the logged-in user.

```text
JWT → user ID → database → User
```

### Authorization

**"Are you allowed to do this?"**

Some endpoints require specific roles.

```python
require_roles(["professor", "teaching_assistant"])
```

A user with the wrong role receives:

```text
403 Forbidden
```

---

## 8. JWT contents

The JWT contains:

```json
{
  "sub": "42",
  "role": "student",
  "exp": 1234567890
}
```

| Field  | Meaning          |
| ------ | ---------------- |
| `sub`  | User ID          |
| `role` | User's role      |
| `exp`  | Token expiration |

The token does **not** contain passwords or other sensitive user information.

---

## 9. Token expiration

Tokens currently expire after **10 hours**.

This is configured in `.env.example`:

```env
ACCESS_TOKEN_EXPIRE_MINUTES=600
```

There is currently no refresh-token system.

Therefore:

```text
Token expires
     ↓
Frontend receives 401
     ↓
User logs in again
     ↓
New token
```

This is intentional for the MVP/hackathon.

---

## 10. SECRET_KEY

`SECRET_KEY` is used to sign and verify JWTs.

Generate one with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Then add it to `.env`:

```env
SECRET_KEY=your_generated_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=600
```

`.env.example` should contain a placeholder:

```env
SECRET_KEY=change-me
ACCESS_TOKEN_EXPIRE_MINUTES=600
```

**Do not commit the real `SECRET_KEY` to Git.**

---

## 11. Token storage

For the MVP/demo, the frontend can store the token in `localStorage`:

```javascript
localStorage.setItem("access_token", access_token);
```

Then retrieve it when making requests:

```javascript
const token = localStorage.getItem("access_token");
```

---

## 12. HTTP status codes

| Status | Meaning                           | Frontend action       |
| ------ | --------------------------------- | --------------------- |
| `400`  | Bad request                       | Show error            |
| `401`  | Not authenticated / invalid token | Redirect to login     |
| `403`  | Authenticated but not allowed     | Show permission error |
| `422`  | Invalid request data              | Show validation error |

---



## 13. Current limitations

The authentication system is intentionally simple for the MVP.

Currently there is:

* No refresh tokens
* No password reset
* No server-side logout/revocation
* No role-change endpoint
