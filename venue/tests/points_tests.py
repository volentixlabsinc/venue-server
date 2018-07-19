from venue.models import UserProfile, ForumProfile, ForumPost, ForumSite
from django.test import TestCase
from django.utils import timezone
from constance import config
import unittest.mock as mock
from model_mommy import mommy
from model_mommy.recipe import Recipe


class PointsCreditTest(TestCase):

    def setUp(self):
        # Create a mock forum site
        self.forum_site = mommy.make(ForumSite)
        # Create a mock user profile
        self.user_profile = mommy.make(UserProfile)
        # Create a mock forum rank
        rank_recipe = Recipe(
            ForumUserRank,
            name='Sr. Member',
            bonus_percentage=5
        )
        self.forum_rank = rank_recipe.make()
        # Create a mock forum profile
        forum_profile_recipe = Recipe(
            ForumProfile,
            forum_rank=forum_rank,
            user_profile=user_profile,
            forum=forum_site,
            forum_user_id='172792'
        )
        self.forum_profile = forum_profile_recipe.make()
        # Create a dummpy scraped post result
        self.post = {
            'topic_id': '1239384',
            'message_id': '98372737',
            'content_length': 273,
            'timestamp': timezone.now()
        }

    @mock.patch.object(ForumPost, 'save')
    def test_forum_post_save(self, forum_post_save)
        # Create a forum post
        self.forum_post = ForumPost(
            user_profile=user_profile,
            forum_profile=forum_profile,
            forum_rank=forum_profile.forum_rank,
            topic_id=post['topic_id'],
            message_id=post['message_id'],
            unique_content_length=post['content_length'],
            timestamp=post['timestamp']
        )
        self.forum_post.save()
        # Test with asserts
        self.assetTrue(forum_post_save.save.called)
        self.assertEqual(forum_post, config.POST_POINTS_MULTIPLIER)
