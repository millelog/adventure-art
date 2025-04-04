Okay, here is a revised, self-contained design document for the Adventure Art SAAS, focusing on a simplified, cost-effective architecture leveraging Supabase and Railway, with AWS S3 for storage.

## Adventure Art SAAS - Simplified Design Document

**Version:** 2.0 (Self-Contained)
**Date:** 2023-10-27

**1. Introduction & Goals**

**1.1. Overview**
This document outlines the design for "Adventure Art SAAS," a web application enabling users (like Dungeon Masters) to generate visual art representing scenes from their tabletop roleplaying games or other narrative sessions in near real-time. The core functionality involves processing user-provided audio input through an AI pipeline (transcription, environment analysis, scene composition, image generation) and displaying the resulting image dynamically on a web interface. This document details a simplified architecture suitable for initial launch, prioritizing cost-effectiveness and ease of management.

**1.2. Core Functionality**
*   **User Accounts:** Secure user registration and login.
*   **Audio Input:** Capture audio chunks from the user's browser.
*   **AI Processing Pipeline:**
    *   Audio Transcription (via managed Whisper API).
    *   Environment Analysis & Update (via LLM like GPT-4o).
    *   Scene Composition (via LLM like GPT-4o, using transcript, environment, character data, style).
    *   Image Generation (via Google Imagen API).
*   **Real-time Updates:** Push newly generated images, scene descriptions, and environment updates to the user's interface without requiring page refreshes.
*   **Data Management:** Allow users to define and manage Characters (name, description), Environment state (description, lock status), and global visual Style preferences.
*   **Session History:** Store and allow users to review past sessions, including transcripts, generated prompts, and images.

**1.3. Design Goals**
*   **SAAS Model:** Build a multi-tenant application where users manage their own data securely.
*   **Cost-Effective Start:** Minimize initial infrastructure costs by leveraging integrated platforms and avoiding unnecessary services.
*   **Simplified Architecture:** Reduce the number of moving parts and complex integrations for easier development and maintenance initially.
*   **Leverage Supabase:** Utilize Supabase heavily for Authentication, Database, and Real-time features.
*   **Maintainable Backend:** Employ FastAPI (Python) for a performant and well-structured API.
*   **Standard Object Storage:** Use AWS S3 for reliable image storage.
*   **Clear Scalability Path:** Design components so they can be individually scaled or replaced as user load grows.

**2. Architecture Overview**

The system employs a decoupled architecture:

1.  **Frontend:** A Next.js application hosted on Vercel, providing the user interface.
2.  **Authentication:** Handled by Supabase Auth.
3.  **Database:** A Supabase PostgreSQL database storing all persistent application data, including a simple job queue table.
4.  **Backend API:** A FastAPI (Python) application deployed as a containerized service on **Railway**. It handles API requests from the frontend and enqueues processing tasks.
5.  **Worker Service:** A separate Python service/script, also deployed as a containerized service on **Railway**. It polls the database for tasks and executes the AI processing pipeline.
6.  **Object Storage:** An AWS S3 bucket for storing generated images.
7.  **Real-time Service:** Supabase Realtime, triggered by database changes, pushes updates to the frontend.
8.  **External AI Services:** APIs for Whisper (OpenAI), GPT-4o (OpenAI), and Imagen 3 (Google AI).

**Diagram:**

```mermaid
graph TD
    subgraph User Interaction
        User -->|Browser| Frontend[Next.js on Vercel];
    end

    subgraph Authentication [Supabase]
        Frontend -->|Login/Signup via Supabase SDK| SupabaseAuth[Supabase Auth];
        BackendAPI -->|Verify JWT| SupabaseAuth;
    end

    subgraph Data & Realtime [Supabase]
        Frontend -->|WebSockets via Supabase SDK| SupabaseRealtime[Supabase Realtime];
        BackendAPI -->|CRUD Ops, Job Insert| SupabaseDB[(Supabase PostgreSQL DB)];
        WorkerService -->|Poll Jobs, Update Status/Results| SupabaseDB;
        SupabaseDB -- DB Changes --> SupabaseRealtime;
    end

    subgraph Application Logic [Railway PaaS]
        Frontend -->|API Calls (HTTPS)| BackendAPI[FastAPI Backend Service];
        BackendAPI -->|Inserts Job| SupabaseDB;
        WorkerService[Worker Service (Python Script)];
    end

    subgraph Storage
        WorkerService -->|Upload Image| S3Storage[AWS S3 Bucket];
        BackendAPI -->|Write/Read Metadata (Optional)| S3Storage;
    end

    subgraph External AI Services
        WorkerService -->|Call API| WhisperAPI[Managed Whisper API];
        WorkerService -->|Call API| GPT_API[OpenAI GPT-4o API];
        WorkerService -->|Call API| ImagenAPI[Google Imagen API];
    end

```

**3. Technology Stack**

*   **Frontend Framework:** Next.js (Hosted on Vercel)
*   **Authentication:** Supabase Auth
*   **Database:** Supabase PostgreSQL
*   **Backend Framework:** FastAPI (Python)
*   **Backend/Worker Hosting:** Railway (Container Platform as a Service)
*   **Object Storage:** AWS S3
*   **Task Queue:** PostgreSQL Table (`jobs`) within Supabase DB (Worker polls this table)
*   **Real-time Communication:** Supabase Realtime (Triggered by DB changes)
*   **Transcription:** Managed Whisper API (e.g., OpenAI)
*   **LLMs:** OpenAI API (GPT-4o or similar)
*   **Image Generation:** Google AI API (Imagen 3 or similar)
*   **Infrastructure Libraries:** Supabase Python/JS SDKs, Boto3 (for S3), OpenAI Python library, Google AI Python library, SQLAlchemy/SQLModel (for DB interaction in Python).

**4. Component Breakdown**

*   **4.1. Frontend (Next.js on Vercel)**
    *   **Responsibilities:**
        *   Render user interface components (React).
        *   Handle user interactions (button clicks, form submissions).
        *   Integrate with Supabase Auth SDK for signup, login, session management.
        *   Use Web Audio API to capture microphone input, encode (e.g., WAV), and potentially chunk audio.
        *   Send authenticated HTTP requests (with Supabase JWT) to the Backend API for data management and audio upload.
        *   Establish WebSocket connection using Supabase JS SDK to listen for real-time database changes.
        *   Receive real-time events (new images, prompts, environment changes) and update the UI dynamically.
        *   Display session history fetched via API.
    *   **Key Logic:** UI rendering, state management, audio recording/formatting, API client logic, Supabase Auth/Realtime SDK integration.

*   **4.2. Backend API (FastAPI on Railway)**
    *   **Responsibilities:**
        *   Expose secure RESTful API endpoints (e.g., `/api/v1/...`).
        *   Use middleware to verify the Supabase JWT attached to incoming requests.
        *   Validate incoming request data (using Pydantic models).
        *   Handle requests for managing Characters, User Settings (Environment/Style), and Sessions (CRUD operations on Supabase DB). Ensure operations respect user ownership (using user ID from JWT).
        *   Handle audio chunk uploads: receive the audio file, potentially save temporarily within the container's ephemeral storage, retrieve necessary context (user settings, characters) from DB.
        *   Create a job record in the `jobs` table in the Supabase DB, including the audio reference and necessary context in a JSONB payload.
        *   Respond appropriately to the frontend (e.g., 200 OK for data retrieval, 201 Created for new data, 202 Accepted for audio upload/job creation).
    *   **Key Logic:** API routing, request/response validation, JWT verification, database interaction via ORM (e.g., SQLModel), job record insertion (SQL INSERT).

*   **4.3. Database (Supabase PostgreSQL)**
    *   **Responsibilities:**
        *   Provide persistent storage for all application data (users, settings, characters, sessions, events, jobs).
        *   Enforce data relationships and integrity.
        *   Utilize **Row Level Security (RLS)** policies to ensure users can only access and modify their own data.
        *   Serve as the backing store for Supabase Auth and Realtime.
    *   **Key Data:** See Section 5 (Data Models).

*   **4.4. Authentication (Supabase Auth)**
    *   **Responsibilities:** Managed service handling user registration, login (email/password, potentially social providers), password resets, issuing secure JWTs.
    *   **Key Logic:** Configuration in Supabase dashboard, integration via Supabase SDKs in frontend and JWT verification in backend.

*   **4.5. Object Storage (AWS S3)**
    *   **Responsibilities:** Durably store generated scene images. Provide publicly accessible URLs for these images (or securely signed URLs if privacy becomes a concern).
    *   **Key Logic:** Bucket creation and configuration (e.g., public read access for image files). Worker service uses AWS SDK (Boto3) with credentials (stored securely as environment variables on Railway) to upload images.

*   **4.6. Task Queue (PostgreSQL `jobs` Table)**
    *   **Responsibilities:** Hold records of pending audio processing tasks. Track the status of each task (`pending`, `processing`, `completed`, `failed`). Store necessary context for the worker.
    *   **Key Logic:** Simple table acting as a queue. Backend API inserts `pending` jobs. Worker polls for `pending` jobs, updates status during processing, and marks final status.

*   **4.7. Worker Service (Python on Railway)**
    *   **Responsibilities:**
        *   Run as a persistent background service (separate container/process from the API).
        *   Periodically poll the `jobs` table for records with `status = 'pending'`.
        *   Implement a locking mechanism (e.g., `SELECT ... FOR UPDATE SKIP LOCKED` or atomic `UPDATE ... RETURNING`) to claim a single pending job and prevent multiple workers processing the same task.
        *   Mark the claimed job as `processing` in the database.
        *   Execute the core AI processing pipeline using the job payload:
            1.  Retrieve/access audio data.
            2.  Call Whisper API -> Get `transcript`.
            3.  Call GPT-4o (Environment Analysis) using transcript and environment context from job payload.
            4.  If environment update needed & unlocked: Update the `user_settings` table in DB for that user. (This DB change can trigger Realtime).
            5.  Call GPT-4o (Scene Composition) using transcript, (potentially updated) environment, character context, style context -> Get `scene_prompt`.
            6.  Call Imagen API using `scene_prompt` -> Get image data.
            7.  Upload image data to AWS S3 bucket -> Get `image_url`.
            8.  Insert a new record into the `session_events` table containing the `transcript`, `scene_prompt`, `image_url`, and snapshots of environment/style used. (This DB change triggers Realtime).
            9.  Update the job record status to `completed` in the `jobs` table.
        *   Handle errors gracefully during the pipeline, log the error, and update the job status to `failed` with error details.
    *   **Key Logic:** Database polling loop, job locking query, sequential calls to external AI APIs (using their SDKs), S3 upload logic (Boto3), database updates (SQLAlchemy/SQLModel). Requires DB connection string, AI API keys, S3 credentials.

*   **4.8. Real-time Service (Supabase Realtime)**
    *   **Responsibilities:** Managed service that monitors PostgreSQL Write-Ahead Log (WAL) for database changes. Pushes notifications about specified changes over WebSockets to subscribed clients.
    *   **Key Logic:** Configure Realtime publications on relevant tables (e.g., `session_events`, `user_settings`) in the Supabase dashboard. Frontend uses Supabase JS SDK to subscribe to these publications, filtering for events relevant to the logged-in user.

**5. Data Models (Supabase PostgreSQL with RLS)**

*(RLS Policies should be defined for all tables to ensure users can only access their own data)*

*   **`users`** (Managed mostly by Supabase Auth, links to `auth.users`)
    *   `id`: UUID (Primary Key, references `auth.users.id`)
    *   *(Other profile fields managed via Supabase Auth or custom fields)*

*   **`user_settings`**
    *   `user_id`: UUID (Primary Key, Foreign Key -> users.id, On Delete Cascade)
    *   `current_environment_description`: TEXT
    *   `environment_locked`: BOOLEAN (Default: FALSE)
    *   `current_style_text`: TEXT
    *   `updated_at`: TIMESTAMP WITH TIME ZONE (Default: NOW())
    *   *(RLS: `user_id = auth.uid()`)*

*   **`characters`**
    *   `id`: UUID (Primary Key, Default: gen_random_uuid())
    *   `user_id`: UUID (Foreign Key -> users.id, Not Null, On Delete Cascade)
    *   `name`: VARCHAR (Not Null)
    *   `description`: TEXT
    *   `created_at`: TIMESTAMP WITH TIME ZONE (Default: NOW())
    *   `updated_at`: TIMESTAMP WITH TIME ZONE (Default: NOW())
    *   *(RLS: `user_id = auth.uid()`)*
    *   *Index on (user_id)*

*   **`sessions`**
    *   `id`: UUID (Primary Key, Default: gen_random_uuid())
    *   `user_id`: UUID (Foreign Key -> users.id, Not Null, On Delete Cascade)
    *   `start_time`: TIMESTAMP WITH TIME ZONE (Default: NOW())
    *   `name`: VARCHAR (Optional)
    *   `created_at`: TIMESTAMP WITH TIME ZONE (Default: NOW())
    *   *(RLS: `user_id = auth.uid()`)*
    *   *Index on (user_id, start_time DESC)*

*   **`session_events`**
    *   `id`: UUID (Primary Key, Default: gen_random_uuid())
    *   `session_id`: UUID (Foreign Key -> sessions.id, Not Null, On Delete Cascade)
    *   `user_id`: UUID (Foreign Key -> users.id, Not Null, On Delete Cascade)
    *   `timestamp`: TIMESTAMP WITH TIME ZONE (Default: NOW())
    *   `event_type`: VARCHAR (Default: 'scene')
    *   `transcript`: TEXT
    *   `scene_prompt`: TEXT
    *   `image_url`: VARCHAR (URL to image in S3)
    *   `environment_snapshot`: TEXT (Env description used for this event)
    *   `style_snapshot`: TEXT (Style text used for this event)
    *   `processing_duration_ms`: INTEGER (Optional)
    *   *(RLS: `user_id = auth.uid()`)*
    *   *Index on (session_id, timestamp)*

*   **`jobs`**
    *   `id`: BIGSERIAL (Primary Key)
    *   `user_id`: UUID (Foreign Key -> users.id, Not Null, On Delete Cascade)
    *   `session_id`: UUID (Foreign Key -> sessions.id, Not Null, On Delete Cascade)
    *   `payload`: JSONB (Job details: audio S3 ref/path, context snapshots)
    *   `status`: VARCHAR (Default: 'pending'; values: 'pending', 'processing', 'completed', 'failed')
    *   `created_at`: TIMESTAMP WITH TIME ZONE (Default: NOW())
    *   `updated_at`: TIMESTAMP WITH TIME ZONE (Default: NOW())
    *   `worker_id`: VARCHAR (Optional)
    *   `last_error`: TEXT (Optional)
    *   *(RLS: `user_id = auth.uid()` - Allows users potentially to see status of their own jobs if API exposes it)*
    *   *Index on (status, created_at)*

**6. Key Workflows**

*   **6.1. User Signup/Login:**
    1.  Frontend uses Supabase JS SDK UI components or methods.
    2.  Supabase Auth handles the flow, creates user record in `auth.users`.
    3.  Frontend receives JWT upon successful login/signup.
    4.  Subsequent API calls from Frontend include the JWT in the Authorization header.
    5.  Backend API uses Supabase Python library or JWT library to verify token and extract `user_id` (`auth.uid()`).

*   **6.2. Audio Upload and Processing:**
    1.  Frontend captures audio, sends `POST /api/v1/audio/upload` with audio file and JWT.
    2.  Backend API verifies JWT, gets `user_id`. Fetches current `user_settings` and `characters` for context. Determines current `session_id`. Creates `payload` JSONB. Inserts a new row into `jobs` table (`status='pending'`). Responds 202 Accepted.
    3.  Worker Service polls `jobs` table, finds and locks the pending job, updates status to `processing`.
    4.  Worker executes AI pipeline (Whisper -> GPT Env -> DB Env Update -> GPT Scene -> Imagen -> S3 Upload).
    5.  Worker inserts results into `session_events` table.
    6.  Worker updates job status to `completed` (or `failed`).
    7.  Supabase Realtime detects the INSERT on `session_events` (and potentially UPDATE on `user_settings`).
    8.  Supabase Realtime pushes the new event data over WebSocket to the specific user's subscribed Frontend instance.
    9.  Frontend receives the real-time message via Supabase SDK listener and updates the displayed image, scene prompt, and environment description.

*   **6.3. Data Management (Characters, Env, Style):**
    1.  Frontend user interacts with forms.
    2.  Frontend sends authenticated `GET/POST/PUT/DELETE` requests to Backend API endpoints (e.g., `/api/v1/characters`, `/api/v1/user/settings`).
    3.  Backend API verifies JWT, performs DB operation (respecting RLS via `user_id` from JWT).
    4.  Backend API responds.
    5.  If `user_settings` is updated, Supabase Realtime (if configured for that table/event) pushes the change to the Frontend for immediate UI sync.

*   **6.4. Viewing Session History:**
    1.  Frontend requests `/api/v1/sessions` or `/api/v1/sessions/{id}/events`.
    2.  Backend API queries Supabase DB (RLS automatically filters by logged-in user).
    3.  Backend API returns data.
    4.  Frontend displays the history.

**7. API Design Examples**

*   `POST /api/v1/audio/upload`: Accepts audio file (multipart/form-data). Requires Auth. Returns 202.
*   `GET /api/v1/characters`: Returns list of user's characters. Requires Auth.
*   `POST /api/v1/characters`: Creates character. Body: `{ "name": "...", "description": "..." }`. Requires Auth.
*   `PUT /api/v1/characters/{character_id}`: Updates character. Body: `{ "name": "...", "description": "..." }`. Requires Auth.
*   `DELETE /api/v1/characters/{character_id}`: Deletes character. Requires Auth.
*   `GET /api/v1/user/settings`: Returns user's env/style settings. Requires Auth.
*   `PUT /api/v1/user/settings`: Updates user settings. Body: `{ "current_environment_description": "...", "environment_locked": true/false, "current_style_text": "..." }`. Requires Auth.
*   `GET /api/v1/sessions`: Returns list of user's sessions. Requires Auth.
*   `GET /api/v1/sessions/{session_id}/events`: Returns events for a specific session. Requires Auth.

**8. Real-time Communication Strategy**

*   Primarily relies on **Supabase Realtime** triggered by database changes.
*   Frontend uses `supabase-js` SDK to connect and subscribe to relevant changes on `session_events` and `user_settings`, filtering by `user_id`.
*   Example Frontend Subscription:
    ```javascript
    const userId = supabase.auth.user()?.id;
    if (userId) {
      supabase
        .channel('db-changes')
        .on('postgres_changes', {
            event: 'INSERT',
            schema: 'public',
            table: 'session_events',
            filter: `user_id=eq.${userId}`
          },
          (payload) => {
            console.log('New session event:', payload.new);
            // Update UI with image_url, scene_prompt from payload.new
          }
        )
        .on('postgres_changes', {
            event: 'UPDATE',
            schema: 'public',
            table: 'user_settings',
            filter: `user_id=eq.${userId}`
          },
          (payload) => {
             console.log('User settings updated:', payload.new);
            // Update environment description UI from payload.new
          }
        )
        .subscribe();
    }
    ```
*   This approach minimizes explicit broadcasting logic in the backend/worker for the core data flow.

**9. Scalability Path**

*   **Initial Bottleneck:** The database polling by the worker and the `jobs` table itself will likely be the first performance limit.
*   **Step 1: Optimize Polling:** Ensure proper indexing on `jobs` (`status`, `created_at`). Adjust polling frequency.
*   **Step 2: Scale Workers:** Increase the number of Worker service instances running on Railway. The DB locking mechanism (`SELECT FOR UPDATE SKIP LOCKED`) ensures jobs aren't processed twice.
*   **Step 3: Scale API:** Increase the number of Backend API service instances on Railway if API response time degrades.
*   **Step 4: Upgrade Task Queue:** If DB polling becomes too inefficient or puts too much load on the database:
    *   Introduce a managed Redis service (e.g., Upstash, Redis Labs, AWS ElastiCache).
    *   Modify Backend API to enqueue jobs to Redis using a Python library like Celery, RQ, or Dramatiq.
    *   Modify Worker Service to consume jobs from Redis using the chosen library. This provides more robust queuing features.
*   **Step 5: Database Scaling:** Utilize Supabase's built-in scaling options (e.g., upgrading compute resources) if the database itself becomes a bottleneck.

**10. Security Considerations**

*   **Authentication:** Handled by Supabase Auth.
*   **Authorization:** Implement strict **Row Level Security (RLS)** policies in Supabase PostgreSQL for *all* tables containing user data. Backend API should still verify JWT ownership but relies on RLS for data access enforcement.
*   **Credentials:** Store Supabase keys, S3 keys, AI API keys securely as environment variables within the Railway service configurations. Never commit secrets to code.
*   **Input Validation:** Use Pydantic in FastAPI to validate all API inputs. Sanitize any user-generated content displayed in HTML if necessary (though most content here is structured or URLs).
*   **HTTPS:** Ensure Railway and Vercel enforce HTTPS.
*   **Rate Limiting:** Consider adding rate limiting to the Backend API (especially audio upload) using libraries like `slowapi` for FastAPI.
*   **S3 Security:** Configure S3 bucket policies correctly (e.g., public read for generated images, restricted write access only for the Worker's IAM credentials/keys).
*   **Dependencies:** Regularly update all software dependencies (OS, Python packages, Node modules).

**11. Deployment Strategy**

1.  **Supabase Setup:** Create Supabase project. Enable Auth, configure DB tables (with SQL schema definitions including RLS policies), enable Realtime on `session_events` and `user_settings`. Note Supabase URL and `anon` / `service_role` keys.
2.  **AWS S3 Setup:** Create an S3 bucket. Configure public read access if desired. Create IAM user/credentials with write access to the bucket for the Worker service.
3.  **Frontend (Next.js):** Connect project Git repository (e.g., GitHub) to Vercel. Configure Vercel environment variables for Supabase URL and `anon` key. Deploy automatically on Git push.
4.  **Backend API & Worker (FastAPI/Python):**
    *   Create `Dockerfile` for both the API application and the Worker script (can be separate Dockerfiles or a multi-stage build).
    *   Create services on Railway, linking the Git repository. Railway can detect the `Dockerfile` and build/deploy.
    *   Configure environment variables on Railway for each service: Supabase URL, Supabase `service_role` key (for backend/worker privileged access), S3 credentials (AWS Key ID, Secret Key, Bucket Name), OpenAI API Key, Google AI API Key.
    *   Ensure Worker service is configured to run persistently (e.g., as a long-running command in the Dockerfile's `CMD` or `ENTRYPOINT`).