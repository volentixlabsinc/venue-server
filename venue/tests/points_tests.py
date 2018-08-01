from venue.models import UserProfile, ForumProfile, ForumPost, \
    ForumSite, ForumUserRank
from django.test import TestCase
from django.utils import timezone
from constance import config
import unittest.mock as mock
from model_mommy import mommy
from model_mommy.recipe import Recipe


class PointsCreditingTest(TestCase):
    """ Tests the crediting of points that happens after a new forum
    post is saved """

    def setUp(self):
        # Create a mock forum site
        forum_site = mommy.make(ForumSite)
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
            forum_rank=self.forum_rank,
            user_profile=self.user_profile,
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

    def test_points_crediting(self):
        # Create a forum post
        forum_post = ForumPost(
            user_profile=self.user_profile,
            forum_profile=self.forum_profile,
            forum_rank=self.forum_profile.forum_rank,
            topic_id=self.post['topic_id'],
            message_id=self.post['message_id'],
            unique_content_length=self.post['content_length'],
            timestamp=self.post['timestamp']
        )
        forum_post.save()
        # Check credited base points
        self.assertEqual(forum_post.base_points, config.POST_POINTS_MULTIPLIER)
        # Check credited bonus percentage
        bonus_pct = self.forum_rank.bonus_percentage
        self.assertEqual(forum_post.influence_bonus_pts, bonus_pct)
        # Check credited bonus points
        expected_bonus = config.POST_POINTS_MULTIPLIER * (bonus_pct/100)
        self.assertEqual(forum_post.influence_bonus_pts, expected_bonus)
        # Check credited total points
        expected_total = config.POST_POINTS_MULTIPLIER + expected_bonus
        self.assertEqual(forum_post.total_points, expected_total)


class SignatureMinutesMonitoringTest(TestCase):
    """ Tests the monitoring and categorization of signature minutes that
    happen every time a forum post is saved """

    def setUp(self):
        pass

    def test_sig_minutes_monitoring(self):
        pass
