from jose import jwt, JWTError
import os

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

def verify_supabase_jwt(token):
    """
    Decodes and verifies a Supabase JWT.
    Returns the decoded payload if valid, raises JWTError otherwise.
    """
    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=['HS256'], # Supabase uses HS256 for JWTs
            audience="authenticated" 
        )
        return payload
    except JWTError as e:
        raise Exception(f"Invalid token: {str(e)}")
