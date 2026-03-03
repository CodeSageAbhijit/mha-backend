# Mental Health Backend — Repository Overview

## Tech Stack
- **Framework**: FastAPI (Python)
- **Realtime**: Socket.IO via `python-socketio`
- **Database**: MongoDB using Motor (async driver)
- **Auth & Security**:
  - JWT utilities in `app/utils/jwt_tokens.py`
  - Password hashing via Passlib (`app/utils/constants.py`)
- **External Services**:
  - Cloudinary for media uploads (configured in `constants.py`)
  - Google OAuth (`app/services/google_route.py`)
  - ZEGO credentials in `.env`

## Entry Points
- **REST API**: `app/main.py`
  - Mounts all FastAPI routers under `app/services`
  - Adds CORS and session middleware
  - On startup connects to MongoDB
- **Socket.IO**: `app/services/socket_server.py`
  - Exported `socket_app` (ASGI) used by FastAPI host
  - Real-time events implemented in `app/services/chat_routes.py`

## Key Modules
- **app/database/mongo.py**: Mongo connection and collection handles
- **app/services/**: Main REST router implementations (auth, appointments, payments, etc.)
- **app/models/**: Pydantic schemas for above services
- **app/utils/**: Shared helpers (serialization, JWT, email, etc.)

## Chat Feature
- `app/services/chat_routes.py`: Handles Socket.IO events for connecting, joining rooms, sending messages, typing indicators, call management.
- `app/services/room_routes.py`: Ensures chat rooms exist for pairs of users.
- `app/models/chat_schemas.py`: Pydantic request/response models.
- `app/chat_manager.py`: Higher-level orchestration utilities.

## Configuration
- **Environment Variables**: `.env`
- **Python Dependencies**: `requirements.txt`

## Known Considerations
- Secrets committed in `.env` and `mongo.py` (Cloudinary, DB URL, OpenAI keys, etc.) — replace with secure configuration for production.
- Duplicate real-time setup exists (`chat_routes.py` and `socket_server.py`); ensure only one is exposed at runtime.