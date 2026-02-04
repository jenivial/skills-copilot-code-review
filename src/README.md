# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities
- View active school announcements
- Manage announcements (teachers only)

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                                 | Description                                                         |
| ------ | ------------------------------------------------------------------------ | ------------------------------------------------------------------- |
| GET    | `/activities`                                                            | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu`        | Sign up for an activity                                             |
| POST   | `/activities/{activity_name}/unregister?email=student@mergington.edu`    | Remove a student from an activity                                   |
| POST   | `/auth/login?username=teacher&password=secret`                           | Authenticate a teacher                                              |
| GET    | `/auth/check-session?username=teacher`                                   | Validate a teacher session                                          |
| GET    | `/announcements`                                                        | List active announcements                                           |
| GET    | `/announcements/all?teacher_username=teacher`                            | List all announcements (teacher only)                               |
| POST   | `/announcements?teacher_username=teacher`                                | Create an announcement (teacher only)                               |
| PUT    | `/announcements/{announcement_id}?teacher_username=teacher`              | Update an announcement (teacher only)                               |
| DELETE | `/announcements/{announcement_id}?teacher_username=teacher`              | Delete an announcement (teacher only)                               |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Announcements** - Uses a generated identifier:
   - Message
   - Optional start date
   - Required expiration date
   - Tone (info, success, warning)

All data is stored in MongoDB, so records persist between server restarts.
