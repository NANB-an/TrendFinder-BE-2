from django.urls import path
from .views import test_root, protected_route, trending_posts, bookmark_post, generate_idea_route, get_bookmarks, delete_bookmark, update_bookmark

urlpatterns = [
    path('', test_root),
    path('protected/', protected_route),
    path('trending/', trending_posts),
    path('bookmark/', bookmark_post),
    path('generate_idea/',generate_idea_route),
    path('get_bookmarks/', get_bookmarks),
    path('bookmark/<str:bookmark_id>/',delete_bookmark, name='delete_bookmark'),
    path('bookmark/<uuid:bookmark_id>/update/',update_bookmark, name='update_bookmark'),


]
