import copy
import plistlib

BASE_PROFILE = {
    "PayloadContent": {
        "URL": "https://example.invalid/retrieve/",
        "DeviceAttributes": ["UDID", "PRODUCT", "VERSION", "SERIAL"],
    },
    "PayloadOrganization": "nythepegasus",
    "PayloadDisplayName": "nythepegasus Paid Signing",
    "PayloadVersion": 1,
    "PayloadUUID": "E4079F18-490E-4B23-8F81-3907C92933A4",
    "PayloadIdentifier": "ny.udid.register",
    "PayloadDescription": "Helps you get your device details!",
    "PayloadType": "Profile Service",
}

def make_profile(callback_url: str) -> bytes:
    profile = copy.deepcopy(BASE_PROFILE)
    profile["PayloadContent"]["URL"] = callback_url
    return plistlib.dumps(profile)

def extract_plist_from_pkcs7(body: bytes) -> dict:
    start = body.find(b"<?xml")
    end = body.find(b"</plist>")
    if start == -1 or end == -1:
        raise ValueError("No XML plist found in payload.")
    end += len(b"</plist>")
    return plistlib.loads(body[start:end])
