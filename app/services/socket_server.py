import socketio



sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25,
    namespace="/"
)

socket_app = socketio.ASGIApp(
    sio,
    static_files={},
    on_startup=lambda: print("✅ Socket.IO server started"),
    on_shutdown=lambda: print("❌ Socket.IO server shutdown")
)

ROLE_COLLECTIONS = {
    "user": ("patients", "patientId"),
    "doctor": ("doctor", "doctorId"),
    "counselor": ("counselors", "counselorId"),
}

COLLECTION_ROLE = {
    "patients": "user",
    "doctor": "doctor",
    "counselors": "counselor",
}


typing_users: dict[str, dict] = {}  
USER_SIDS: dict[str, set[str]] = {}
