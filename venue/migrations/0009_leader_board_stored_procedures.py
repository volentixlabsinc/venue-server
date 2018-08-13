from __future__ import unicode_literals

from django.db import migrations


def forum_stats_procedure():
    return """
    CREATE OR REPLACE FUNCTION forum_stats()
        RETURNS TABLE(
          site_name TEXT,
          total_posts BIGINT,
          total_users BIGINT
        ) AS $body$
        SELECT S.name::TEXT AS site_name,
               count(DISTINCT FPT.id) AS total_posts,
               count(DISTINCT FP.id) AS total_users
        FROM venue_forumsite S
               JOIN venue_forumprofile FP ON S.id = FP.forum_id
               JOIN venue_forumpost FPT ON FP.id = FPT.forum_profile_id
               JOIN venue_userprofile UP ON FP.user_profile_id = UP.id
               JOIN auth_user U ON UP.user_id = U.id
        WHERE U.is_active IS TRUE AND FP.active IS TRUE AND FP.verified IS TRUE
        GROUP BY name;
        $body$
        LANGUAGE SQL;
    """


def leader_board_procedure():
    return """
        CREATE OR REPLACE FUNCTION leader_board_data(P_TOTAL_POINTS NUMERIC, P_VTX_AVAILABLE INT, P_MAX_REFERRALS INT)
          RETURNS TABLE(
            username     TEXT,
            total_posts  BIGINT,
            total_points NUMERIC,
            total_tokens BIGINT,
            rank         INT
          ) AS $body$
        WITH POSTS AS (SELECT P.forum_profile_id,
                              coalesce(sum(P.total_points), 0.0) AS total_points,
                              coalesce(count(P.id), 0) AS total_count
                       FROM venue_forumpost P
                       WHERE credited = TRUE
                       GROUP BY P.forum_profile_id),
             REFERREALS AS (SELECT referrer_id, coalesce(bonus, 0) AS bonus
                            FROM (SELECT bonus, referrer_id,
                                         row_number() OVER (PARTITION BY referrer_id ORDER BY granted_at) AS rownum
                                  FROM venue_referral) tmp
                            WHERE ROWNUM <= P_MAX_REFERRALS),
             RANK AS (SELECT rank :: INT, user_profile_id
                      FROM (SELECT id, rank, timestamp, user_profile_id, row_number() OVER (
                        PARTITION BY user_profile_id ORDER BY timestamp DESC
                        ) AS row_number
                            FROM venue_ranking) AS tmp
                      WHERE row_number = 1)
        SELECT U.username :: TEXT,
               coalesce(sum(P.total_count), 0) :: BIGINT AS total_posts,
               coalesce(sum(P.total_points), 0.0) :: NUMERIC AS total_points,
               coalesce(coalesce(sum(P.total_points), 0) / P_TOTAL_POINTS * P_VTX_AVAILABLE + coalesce(sum(R.bonus), 0),
                        0) :: BIGINT AS total_tokens,
               RK.rank
        FROM venue_userprofile UP
               JOIN venue_forumprofile FP ON UP.id = FP.user_profile_id
               JOIN auth_user U ON UP.user_id = U.id
               LEFT JOIN POSTS AS P ON FP.id = P.forum_profile_id
               LEFT JOIN REFERREALS R ON UP.id = R.referrer_id
               LEFT JOIN RANK RK ON UP.id = RK.user_profile_id
        WHERE FP.active IS TRUE AND verified IS TRUE AND U.is_active IS TRUE AND UP.email_confirmed IS TRUE
        GROUP BY U.id, RK.RANK;
        $body$
        LANGUAGE SQL;
    """


class Migration(migrations.Migration):
    dependencies = [
        ('venue', '0008_referral'),
    ]

    operations = [
        migrations.RunSQL(leader_board_procedure()),
        migrations.RunSQL(forum_stats_procedure())
    ]
