# app/config/default_pricing.py
"""
Default pricing configuration for professional roles.
These are salary-based professionals with no commission.
Only admins and superadmins can modify these rates.
"""

DEFAULT_PRICING = {
    "psychiatrist": {
        "voiceCallRate": 100,  # ₹/min
        "videoCallRate": 150,  # ₹/min
        "inPerson15Min": 750,
        "inPerson30Min": 1500,
        "inPerson60Min": 2500,
        "isSalaryBased": True,
        "commission": 0,  # NO commission - salary-based
        "role": "psychiatrist",
        "roleDescription": "Licensed Psychiatrist - Can prescribe medicine"
    },
    "mentor": {
        "voiceCallRate": 50,  # ₹/min
        "videoCallRate": 75,  # ₹/min
        "inPerson15Min": 300,
        "inPerson30Min": 600,
        "inPerson60Min": 1000,
        "isSalaryBased": True,
        "commission": 0,  # NO commission - salary-based
        "role": "mentor",
        "roleDescription": "Mentor - Support and guidance"
    },
    "counselor": {
        "voiceCallRate": 50,  # ₹/min
        "videoCallRate": 75,  # ₹/min
        "inPerson15Min": 300,
        "inPerson30Min": 600,
        "inPerson60Min": 1000,
        "isSalaryBased": True,
        "commission": 0,  # NO commission - salary-based
        "role": "counselor",
        "roleDescription": "Counselor - Emotional support"
    },
    "business_coach": {
        "voiceCallRate": 75,  # ₹/min
        "videoCallRate": 100,  # ₹/min
        "inPerson15Min": 450,
        "inPerson30Min": 900,
        "inPerson60Min": 1500,
        "isSalaryBased": True,
        "commission": 0,  # NO commission - salary-based
        "role": "business_coach",
        "roleDescription": "Business Coach - Business guidance and mentoring"
    },
    "buddy": {
        "voiceCallRate": 30,  # ₹/min
        "videoCallRate": 50,  # ₹/min
        "inPerson15Min": 150,
        "inPerson30Min": 300,
        "inPerson60Min": 500,
        "isSalaryBased": True,
        "commission": 0,  # NO commission - salary-based
        "role": "buddy",
        "roleDescription": "Buddy - Peer support"
    }
}

def get_default_pricing(role: str) -> dict:
    """Get default pricing for a role."""
    return DEFAULT_PRICING.get(role.lower(), None)

def get_all_professional_roles() -> list:
    """Get list of all professional roles."""
    return list(DEFAULT_PRICING.keys())
