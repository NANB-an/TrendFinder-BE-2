from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .utils import verify_supabase_jwt
import os
import google.generativeai as genai
import praw
import requests

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT")
)

genai.configure(api_key=GEMINI_API_KEY)

@api_view(['GET'])
def test_root(request):
    return Response({"message": "TrendFinder API is live!"})


@api_view(['GET'])
def protected_route(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return Response({"error": "Missing Authorization header"}, status=status.HTTP_401_UNAUTHORIZED)
    try:
        token = auth_header.split(" ")[1]
        payload = verify_supabase_jwt(token)
        user_id = payload['sub']
        user_email = payload['email']
        return Response({
            "message": "Token is valid",
            "user_id": user_id,
            "email": user_email
        })
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)


def generate_idea(title):
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"Suggest a creative blog or social media content idea inspired by this Reddit post: \"{title}\""
    response = model.generate_content(prompt)
    return response.text


@api_view(['GET'])
def trending_posts(request):
    jwt_token = request.headers.get('Authorization', '').split('Bearer ')[-1]
    payload = verify_supabase_jwt(jwt_token)
    if not payload:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    user_id = payload['sub']

    subreddit_name = request.GET.get('subreddit', '').strip() or 'popular'
    subreddit = reddit.subreddit(subreddit_name)

    res = requests.get(
        f"{SUPABASE_URL}/rest/v1/bookmarks",
        headers={
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {jwt_token}",  # ✅ Pass user JWT here too
            "Content-Type": "application/json"
        },
        params={
            "user_id": f"eq.{user_id}",
            "select": "id,url"
        }
    )

    if res.status_code != 200:
        return Response(
            {"error": "Failed to fetch bookmarks", "details": res.text},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    bookmarks = res.json()
    bookmarked_urls = {row["url"]: row["id"] for row in bookmarks}

    posts = []
    for post in subreddit.hot(limit=5):
        posts.append({
            'title': post.title,
            'url': post.url,
            'subreddit': subreddit_name,
            'score': post.score,
            'idea': '',
            'isBookmarked': post.url in bookmarked_urls,
            'bookmark_id': bookmarked_urls.get(post.url)
        })

    return Response({'posts': posts})


@api_view(['POST'])
def generate_idea_route(request):
    jwt_token = request.headers.get('Authorization', '').split('Bearer ')[-1]
    payload = verify_supabase_jwt(jwt_token)
    if not payload:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    title = request.data.get('title')
    if not title:
        return Response({'error': 'Missing title'}, status=status.HTTP_400_BAD_REQUEST)

    idea = generate_idea(title)
    return Response({'idea': idea})


@api_view(['POST'])
def bookmark_post(request):
    jwt_token = request.headers.get('Authorization', '').split('Bearer ')[-1]
    payload = verify_supabase_jwt(jwt_token)
    if not payload:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    # user_id = payload['sub']  # ✅ NOT needed in payload, let DB set it

    title = request.data.get("title")
    subreddit = request.data.get("subreddit")
    url = request.data.get("url")
    idea = request.data.get("idea")

    if not title or not url:
        return Response({'error': 'Missing title or url'}, status=status.HTTP_400_BAD_REQUEST)

    insert_res = requests.post(
        f"{SUPABASE_URL}/rest/v1/bookmarks",
        headers={
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {jwt_token}",  # ✅ Use user's JWT for RLS & trigger!
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        },
        json={
            "title": title,
            "subreddit": subreddit,
            "url": url,
            "idea": idea,
            # ✅ Do NOT send user_id! DB sets it.
        }
    )

    if insert_res.status_code != 201:
        return Response({'error': 'Failed to insert', 'details': insert_res.text}, status=500)

    inserted = insert_res.json()[0]
    return Response({'message': 'Bookmark saved!', 'id': inserted['id']})


@api_view(['GET'])
def get_bookmarks(request):
    jwt_token = request.headers.get('Authorization', '').split('Bearer ')[-1]
    payload = verify_supabase_jwt(jwt_token)
    if not payload:
        return Response({'error': 'Unauthorized'}, status=401)

    user_id = payload['sub']

    res = requests.get(
        f"{SUPABASE_URL}/rest/v1/bookmarks",
        headers={
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json"
        },
        params={
            "user_id": f"eq.{user_id}"
        }
    )

    if res.status_code != 200:
        return Response({'error': 'Failed to fetch', 'details': res.text}, status=500)

    bookmarks = res.json()
    return Response({'bookmarks': bookmarks})


@api_view(['DELETE'])
def delete_bookmark(request, bookmark_id):
    jwt_token = request.headers.get('Authorization', '').split('Bearer ')[-1]
    payload = verify_supabase_jwt(jwt_token)
    if not payload:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    user_id = payload['sub']

    res = requests.delete(
        f"{SUPABASE_URL}/rest/v1/bookmarks?id=eq.{bookmark_id}&user_id=eq.{user_id}",
        headers={
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {jwt_token}",  # ✅ Use user JWT!
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
    )

    if res.status_code in [200, 204]:
        return Response({'message': 'Bookmark deleted.'})
    else:
        return Response({'error': 'Failed to delete.', 'details': res.text}, status=500)


@api_view(['PATCH'])
def update_bookmark(request, bookmark_id):
    jwt_token = request.headers.get('Authorization', '').split('Bearer ')[-1]
    payload = verify_supabase_jwt(jwt_token)
    if not payload:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    user_id = payload['sub']
    new_data = request.data

    res = requests.patch(
        f"{SUPABASE_URL}/rest/v1/bookmarks?id=eq.{bookmark_id}&user_id=eq.{user_id}",
        headers={
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {jwt_token}",  # ✅ Use user JWT!
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        },
        json=new_data
    )

    if res.status_code in [200, 204]:
        return Response({'message': 'Bookmark updated.'})
    else:
        return Response({'error': 'Failed to update.', 'details': res.text}, status=500)
