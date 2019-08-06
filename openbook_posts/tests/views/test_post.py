# Create your tests here.
import json
import tempfile
from os import access, F_OK

from PIL import Image
from django.urls import reverse
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase
from django.core.files.images import ImageFile
from django.core.files import File
from unittest import mock

import logging

from openbook_common.tests.helpers import make_authentication_headers_for_user, make_fake_post_text, \
    make_fake_post_comment_text, make_user, make_circle, make_community, make_list, make_moderation_category, \
    get_test_usernames
from openbook_common.utils.model_loaders import get_language_model
from openbook_communities.models import Community
from openbook_notifications.models import PostUserMentionNotification, Notification
from openbook_posts.models import Post, PostUserMention

logger = logging.getLogger(__name__)
fake = Faker()


def get_language_for_text_mock(text):
    return text


class PostItemAPITests(APITestCase):
    """
    PostItemAPI
    """

    fixtures = [
        'openbook_circles/fixtures/circles.json',
        'openbook_common/fixtures/languages.json'
    ]

    def test_can_retrieve_own_post(self):
        """
        should be able to retrieve own post and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_post = json.loads(response.content)

        self.assertEqual(response_post['id'], post.pk)

    def test_can_retrieve_foreign_user_public_post(self):
        """
        should be able to retrieve a foreign user public post and return 200
        """
        user = make_user()
        foreign_user = make_user()

        headers = make_authentication_headers_for_user(user)
        post = foreign_user.create_public_post(text=make_fake_post_text())

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_post = json.loads(response.content)

        self.assertEqual(response_post['id'], post.pk)

    def test_can_retrieve_connected_user_encircled_post(self):
        """
        should be able to retrieve a connected user encircled post and return 200
        """
        user = make_user()
        foreign_user = make_user()

        headers = make_authentication_headers_for_user(user)

        circle = make_circle(creator=foreign_user)
        post = foreign_user.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        user.connect_with_user_with_id(foreign_user.pk)
        foreign_user.confirm_connection_with_user_with_id(user.pk, circles_ids=[circle.pk])

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_post = json.loads(response.content)

        self.assertEqual(response_post['id'], post.pk)

    def test_can_retrieve_public_community_not_member_of_post(self):
        """
        should be able to retrieve a public community not member of post and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_owner = make_user()
        community = make_community(creator=community_owner)

        post = community_owner.create_community_post(text=make_fake_post_text(), community_name=community.name)

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        response_post = json.loads(response.content)

        self.assertEqual(response_post['id'], post.pk)

    def test_can_retrieve_public_community_member_of_post(self):
        """
        should be able to retrieve a public community member of post and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_owner = make_user()
        community = make_community(creator=community_owner)

        post = community_owner.create_community_post(text=make_fake_post_text(), community_name=community.name)

        user.join_community_with_name(community_name=community.name)

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_post = json.loads(response.content)

        self.assertEqual(response_post['id'], post.pk)

    def test_cant_retrieve_community_banned_from_post(self):
        """
        should not be able to retrieve a community banned from post and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_owner = make_user()
        community = make_community(creator=community_owner)

        post = community_owner.create_community_post(text=make_fake_post_text(), community_name=community.name)

        user.join_community_with_name(community_name=community.name)
        user.comment_post(post, text=make_fake_post_comment_text())

        community_owner.ban_user_with_username_from_community_with_name(username=user.username,
                                                                        community_name=community.name)

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cant_retrieve_private_community_not_member_of_post(self):
        """
        should not be able to retrieve a private community not member of post and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_owner = make_user()
        community = make_community(creator=community_owner, type=Community.COMMUNITY_TYPE_PRIVATE)

        post = community_owner.create_community_post(text=make_fake_post_text(), community_name=community.name)

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_retrieve_private_community_member_of_post(self):
        """
        should be able to retrieve a private community member of post and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_owner = make_user()
        community = make_community(creator=community_owner, type=Community.COMMUNITY_TYPE_PRIVATE)

        post = community_owner.create_community_post(text=make_fake_post_text(), community_name=community.name)

        community_owner.invite_user_with_username_to_community_with_name(username=user.username,
                                                                         community_name=community.name)
        user.join_community_with_name(community_name=community.name)

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_post = json.loads(response.content)

        self.assertEqual(response_post['id'], post.pk)

    def test_cant_retrieve_user_encircled_post(self):
        """
        should not be able to retrieve a user encircled post and return 400
        """
        user = make_user()
        foreign_user = make_user()

        headers = make_authentication_headers_for_user(user)

        circle = make_circle(creator=foreign_user)
        post = foreign_user.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cant_retrieve_blocked_user_post(self):
        """
        should not be able to retrieve a post from a blocked user and return 400
        """
        user = make_user()
        user_to_block = make_user()

        headers = make_authentication_headers_for_user(user)

        post = user_to_block.create_public_post(text=make_fake_post_text())

        user.block_user_with_id(user_id=user_to_block.pk)

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_cant_retrieve_blocking_user_post(self):
        """
        should not be able to retrieve a post from a blocking user and return 400
        """
        user = make_user()
        user_to_block = make_user()

        headers = make_authentication_headers_for_user(user)

        post = user_to_block.create_public_post(text=make_fake_post_text())

        user_to_block.block_user_with_id(user_id=user.pk)

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_cant_retrieve_blocked_user_community_post(self):
        """
        should not be able to retrieve a community post from a blocked user and return 400
        """
        user = make_user()

        community_owner = make_user()
        community = make_community(creator=community_owner)

        user_to_block = make_user()

        headers = make_authentication_headers_for_user(user)

        user_to_block.join_community_with_name(community_name=community.name)

        post = user_to_block.create_community_post(text=make_fake_post_text(), community_name=community.name)

        user.block_user_with_id(user_id=user_to_block.pk)

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_cant_retrieve_blocking_user_community_post(self):
        """
        should not be able to retrieve a community post from a blocking user and return 400
        """
        user = make_user()

        community_owner = make_user()
        community = make_community(creator=community_owner)

        user_to_block = make_user()

        headers = make_authentication_headers_for_user(user)

        user_to_block.join_community_with_name(community_name=community.name)

        post = user_to_block.create_community_post(text=make_fake_post_text(), community_name=community.name)

        user_to_block.block_user_with_id(user_id=user.pk)

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_can_retrieve_blocked_community_staff_post(self):
        """
        should be able to retrieve a the post of a blocked community staff member and return 200
        """
        user = make_user()
        community_owner = make_user()
        community = make_community(creator=community_owner)

        headers = make_authentication_headers_for_user(user)

        post = community_owner.create_community_post(text=make_fake_post_text(), community_name=community.name)

        user.block_user_with_id(user_id=community_owner.pk)

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        response_post = json.loads(response.content)
        self.assertEqual(response_post['id'], post.pk)

    def test_can_retrieve_blocking_community_staff_post(self):
        """
        should be able to retrieve a the post of a blocking community staff member and return 200
        """
        user = make_user()
        community_owner = make_user()
        community = make_community(creator=community_owner)

        headers = make_authentication_headers_for_user(user)

        post = community_owner.create_community_post(text=make_fake_post_text(), community_name=community.name)

        community_owner.block_user_with_id(user_id=user.pk)

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        response_post = json.loads(response.content)
        self.assertEqual(response_post['id'], post.pk)

    def test_can_delete_own_post(self):
        """
        should be able to delete own post and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        url = self._get_url(post)

        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Post.objects.filter(pk=post.pk).count() == 0)

    def test_delete_image_post(self):
        """
        should be able to delete image post and file return True
        """
        user = make_user()

        image = Image.new('RGB', (100, 100))
        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(tmp_file)
        tmp_file.seek(0)
        image = ImageFile(tmp_file)

        post = user.create_public_post(text=make_fake_post_text(), image=image)
        file = post.image.image.file

        user.delete_post_with_id(post.id)

        self.assertFalse(access(file.name, F_OK))

    def test_delete_video_post(self):
        """
        should be able to delete video post and file return True
        """
        user = make_user()

        video = b"video_file_content"
        tmp_file = tempfile.NamedTemporaryFile(suffix='.mp4')
        tmp_file.write(video)
        tmp_file.seek(0)
        video = File(tmp_file)

        post = user.create_public_post(text=make_fake_post_text(), video=video)
        file = post.video.video.file

        user.delete_post_with_id(post.id)

        self.assertFalse(access(file.name, F_OK))

    def test_can_delete_post_of_community_if_mod(self):
        """
        should be able to delete a community post if moderator and return 200
        """
        user = make_user()

        community_creator = make_user()
        community = make_community(creator=community_creator)

        user.join_community_with_name(community_name=community.name)
        community_creator.add_moderator_with_username_to_community_with_name(username=user.username,
                                                                             community_name=community.name)

        community_post_creator = make_user()
        community_post_creator.join_community_with_name(community_name=community.name)

        post = user.create_community_post(text=make_fake_post_text(), community_name=community.name)

        url = self._get_url(post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Post.objects.filter(pk=post.pk).count() == 0)

    def test_can_delete_post_of_community_if_admin(self):
        """
        should be able to delete a community post if administrator and return 200
        """
        user = make_user()

        community_creator = make_user()
        community = make_community(creator=community_creator)

        user.join_community_with_name(community_name=community.name)
        community_creator.add_administrator_with_username_to_community_with_name(username=user.username,
                                                                                 community_name=community.name)

        community_post_creator = make_user()
        community_post_creator.join_community_with_name(community_name=community.name)

        post = community_post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)

        url = self._get_url(post)

        headers = make_authentication_headers_for_user(user)
        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Post.objects.filter(pk=post.pk).count() == 0)

    def test_logs_community_post_deleted_by_non_creator(self):
        """
        should create a log when a community post was deleted by an admin/moderator
        """
        user = make_user()

        community_creator = make_user()
        community = make_community(creator=community_creator)

        user.join_community_with_name(community_name=community.name)
        community_creator.add_administrator_with_username_to_community_with_name(username=user.username,
                                                                                 community_name=community.name)

        community_post_creator = make_user()
        community_post_creator.join_community_with_name(community_name=community.name)

        post = community_post_creator.create_community_post(text=make_fake_post_text(), community_name=community.name)

        url = self._get_url(post)

        headers = make_authentication_headers_for_user(user)
        self.client.delete(url, **headers)

        self.assertTrue(community.logs.filter(action_type='RP',
                                              source_user=user,
                                              target_user=community_post_creator).exists())

    def test_cannot_delete_foreign_post(self):
        """
        should not be able to delete a foreign post and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        foreign_user = make_user()
        post = foreign_user.create_public_post(text=make_fake_post_text())

        url = self._get_url(post)

        response = self.client.delete(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Post.objects.filter(pk=post.pk).count() == 1)

    def test_can_edit_own_post(self):
        """
        should be able to edit own  post and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        url = self._get_url(post)
        edited_text = make_fake_post_text()
        data = {
            'text': edited_text
        }

        response = self.client.patch(url, data, **headers)

        self.assertTrue(response.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        self.assertEqual(post.text, edited_text)
        self.assertTrue(post.is_edited)

    @mock.patch('openbook_posts.models.get_language_for_text')
    def test_editing_own_post_updates_language(self, get_language_for_text_call):
        """
        should update language when editing own  post and return 200
        """
        Language = get_language_model()
        get_language_for_text_call.return_value = Language.objects.get(pk=1)
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())
        post.refresh_from_db()
        self.assertTrue(post.language is not None)

        url = self._get_url(post)
        edited_text = make_fake_post_text()
        data = {
            'text': edited_text
        }
        self.client.patch(url, data, **headers)
        get_language_for_text_call.assert_called_with(edited_text)

    def test_editing_own_post_updates_mentions(self):
        """
        should update mentions when updating text
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        mentioned_user = make_user()
        post_text = 'Hello @' + mentioned_user.username

        post = user.create_public_post(text=post_text)

        post_user_mention = PostUserMention.objects.get(user_id=mentioned_user.pk, post_id=post.pk)

        newly_mentioned_user = make_user()

        post_text = 'Hello @' + newly_mentioned_user.username

        data = {
            'text': post_text
        }

        url = self._get_url(post)

        response = self.client.patch(url, data, **headers, format='multipart')

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        post = Post.objects.get(text=post_text, creator_id=user.pk)
        new_post_user_mention = PostUserMention.objects.get(user_id=newly_mentioned_user.pk, post_id=post.pk)

        self.assertFalse(PostUserMention.objects.filter(user_id=mentioned_user.pk, post_id=post.pk).exists())
        self.assertEqual(PostUserMention.objects.filter(user_id=newly_mentioned_user.pk, post_id=post.pk).count(), 1)

        self.assertFalse(PostUserMentionNotification.objects.filter(post_user_mention_id=post_user_mention.pk,
                                                                    notification__owner_id=mentioned_user.pk,
                                                                    notification__notification_type=Notification.POST_USER_MENTION).exists())

        self.assertTrue(PostUserMentionNotification.objects.filter(post_user_mention_id=new_post_user_mention.pk,
                                                                   notification__owner_id=newly_mentioned_user.pk,
                                                                   notification__notification_type=Notification.POST_USER_MENTION).exists())

    def test_editing_text_post_ignores_non_existing_mentioned_usernames(self):
        """
        should ignore non existing mentioned usernames when editing a post
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        post = user.create_public_post(text=make_fake_post_text())

        fake_username = 'nonexistinguser'
        post_text = 'Hello @' + fake_username

        data = {
            'text': post_text
        }
        url = self._get_url(post=post)

        response = self.client.patch(url, data, **headers, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        post = Post.objects.get(text=post_text, creator_id=user.pk)

        self.assertEqual(PostUserMention.objects.filter(post_id=post.pk).count(), 0)

    def test_editing_own_post_does_not_create_double_mentions(self):
        """
        should not create double mentions when editing our own post
        """
        user = make_user()

        headers = make_authentication_headers_for_user(user=user)

        mentioned_user = make_user()
        post_text = 'Hello @' + mentioned_user.username

        post = user.create_public_post(text=post_text)

        post_user_mention = PostUserMention.objects.get(user_id=mentioned_user.pk, post_id=post.pk)

        data = {
            'text': post_text
        }

        url = self._get_url(post)

        response = self.client.patch(url, data, **headers, format='multipart')

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        post = Post.objects.get(text=post_text, creator_id=user.pk)

        self.assertEqual(PostUserMention.objects.filter(user_id=mentioned_user.pk, post_id=post.pk).count(), 1)
        new_post_user_mention = PostUserMention.objects.get(user_id=mentioned_user.pk, post_id=post.pk,
                                                            id=post_user_mention.pk)
        self.assertEqual(new_post_user_mention.pk, post_user_mention.pk)

    def test_canot_edit_to_remove_text_from_own_text_only_post(self):
        """
        should not be able to edit to remove the text of an own post and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        initial_text = make_fake_post_text()
        post = user.create_public_post(text=initial_text)

        url = self._get_url(post)
        data = {
            'text': ''
        }

        response = self.client.patch(url, data, **headers)

        self.assertTrue(response.status_code, status.HTTP_400_BAD_REQUEST)
        post.refresh_from_db()
        self.assertEqual(post.text, initial_text)
        self.assertFalse(post.is_edited)

    def test_can_edit_own_community_post(self):
        """
        should be able to edit own community post and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_creator = make_user()
        community = make_community(creator=community_creator)

        user.join_community_with_name(community_name=community.name)
        community_post = user.create_community_post(text=make_fake_post_text(), community_name=community.name)

        url = self._get_url(community_post)
        edited_text = make_fake_post_text()
        data = {
            'text': edited_text
        }

        response = self.client.patch(url, data, **headers)

        self.assertTrue(response.status_code, status.HTTP_200_OK)
        community_post.refresh_from_db()
        self.assertEqual(community_post.text, edited_text)
        self.assertTrue(community_post.is_edited)

    def test_cannot_edit_own_community_post_which_is_closed(self):
        """
        should NOT be able to edit own closed community post and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community_creator = make_user()
        community = make_community(creator=community_creator)

        user.join_community_with_name(community_name=community.name)
        original_text = make_fake_post_text()
        community_post = user.create_community_post(text=original_text, community_name=community.name)
        community_post.is_closed = True
        community_post.save()

        url = self._get_url(community_post)
        edited_text = make_fake_post_text()
        data = {
            'text': edited_text
        }

        response = self.client.patch(url, data, **headers)

        self.assertTrue(response.status_code, status.HTTP_400_BAD_REQUEST)
        community_post.refresh_from_db()
        self.assertEqual(community_post.text, original_text)
        self.assertFalse(community_post.is_edited)

    def test_cannot_edit_foreign_post(self):
        """
        should not be able to edit foreign post
        """
        user = make_user()
        foreign_user = make_user()
        headers = make_authentication_headers_for_user(user)
        original_text = make_fake_post_text()
        post = foreign_user.create_public_post(text=original_text)

        url = self._get_url(post)
        edited_text = make_fake_post_text()
        data = {
            'text': edited_text
        }

        response = self.client.patch(url, data, **headers)

        self.assertTrue(response.status_code, status.HTTP_400_BAD_REQUEST)
        post.refresh_from_db()
        self.assertEqual(post.text, original_text)
        self.assertFalse(post.is_edited)

    def test_cant_retrieve_soft_deleted_community_post(self):
        """
        should not be able to retrieve soft deleted community post
        """
        user = make_user()

        community_creator = make_user()

        community = make_community(creator=community_creator)

        post_creator = make_user()

        user.join_community_with_name(community_name=community.name)
        post_creator.join_community_with_name(community_name=community.name)

        post = post_creator.create_community_post(community_name=community.name, text=make_fake_post_text())
        post.soft_delete()

        url = self._get_url(post=post)
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cant_retrieve_soft_deleted_following_user_post(self):
        """
        should not be able to retrieve soft deleted following user post
        """
        user = make_user()

        following_user = make_user()
        user.follow_user_with_id(user_id=following_user.pk)

        following_user_post = following_user.create_public_post(text=make_fake_post_text())
        following_user_post.soft_delete()

        url = self._get_url(post=following_user_post)
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cant_retrieve_soft_deleted_connected_user_post(self):
        """
        should not be able to retrieve soft deleted connected user post
        """
        user = make_user()

        connected_user = make_user()
        user.connect_with_user_with_id(user_id=connected_user.pk)
        connected_user_post_circle = make_circle(creator=connected_user)
        connected_user.confirm_connection_with_user_with_id(user_id=user.pk,
                                                            circles_ids=[connected_user_post_circle.pk])
        connected_user_post = connected_user.create_encircled_post(text=make_fake_post_text(),
                                                                   circles_ids=[connected_user_post_circle.pk])
        connected_user_post.soft_delete()
        connected_user_post.save()

        url = self._get_url(post=connected_user_post)
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cant_retrieve_reported_community_post(self):
        """
        should not be able to retrieve reported community post
        """
        user = make_user()

        community_creator = make_user()

        community = make_community(creator=community_creator)

        post_creator = make_user()

        user.join_community_with_name(community_name=community.name)
        post_creator.join_community_with_name(community_name=community.name)

        post = post_creator.create_community_post(community_name=community.name, text=make_fake_post_text())
        user.report_post(post=post, category_id=make_moderation_category().pk)

        url = self._get_url(post=post)
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cant_retrieve_reported_following_user_post(self):
        """
        should not be able to retrieve reported following user post
        """
        user = make_user()

        following_user = make_user()
        user.follow_user_with_id(user_id=following_user.pk)

        following_user_post = following_user.create_public_post(text=make_fake_post_text())
        user.report_post(post=following_user_post, category_id=make_moderation_category().pk)

        url = self._get_url(post=following_user_post)
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cant_retrieve_reported_connected_user_post(self):
        """
        should not be able to retrieve reported connected user post
        """
        user = make_user()

        connected_user = make_user()
        user.connect_with_user_with_id(user_id=connected_user.pk)
        connected_user_post_circle = make_circle(creator=connected_user)
        connected_user.confirm_connection_with_user_with_id(user_id=user.pk,
                                                            circles_ids=[connected_user_post_circle.pk])
        connected_user_post = connected_user.create_encircled_post(text=make_fake_post_text(),
                                                                   circles_ids=[connected_user_post_circle.pk])
        user.report_post(post=connected_user_post, category_id=make_moderation_category().pk)

        url = self._get_url(post=connected_user_post)
        headers = make_authentication_headers_for_user(user)
        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def _get_url(self, post):
        return reverse('post', kwargs={
            'post_uuid': post.uuid
        })


class MutePostAPITests(APITestCase):
    """
    MutePostAPI
    """

    fixtures = [
        'openbook_circles/fixtures/circles.json'
    ]

    def test_can_mute_own_post(self):
        """
        should be able to mute own post and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        url = self._get_url(post)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(user.has_muted_post_with_id(post.pk))

    def test_cant_mute_own_post_if_already_muted(self):
        """
        should not be able to mute own post if already muted and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        url = self._get_url(post)

        user.mute_post_with_id(post.pk)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(user.has_muted_post_with_id(post.pk))

    def test_can_mute_foreign_post_if_public_post(self):
        user = make_user()
        foreign_user = make_user()

        headers = make_authentication_headers_for_user(user)
        post = foreign_user.create_public_post(text=make_fake_post_text())

        url = self._get_url(post)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(user.has_muted_post_with_id(post.pk))

    def test_cannot_mute_foreign_post_if_encircled_post(self):
        user = make_user()
        foreign_user = make_user()

        headers = make_authentication_headers_for_user(user)

        circle = make_circle(creator=foreign_user)

        post = foreign_user.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        url = self._get_url(post)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(user.has_muted_post_with_id(post.pk))

    def test_can_mute_foreign_post_if_part_of_encircled_post(self):
        user = make_user()
        foreign_user = make_user()

        headers = make_authentication_headers_for_user(user)

        circle = make_circle(creator=foreign_user)

        post = foreign_user.create_encircled_post(text=make_fake_post_text(), circles_ids=[circle.pk])

        foreign_user.connect_with_user_with_id(user_id=user.pk, circles_ids=[circle.pk])
        user.confirm_connection_with_user_with_id(user_id=foreign_user.pk)

        url = self._get_url(post)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(user.has_muted_post_with_id(post.pk))

    def test_can_mute_community_post_if_public(self):
        user = make_user()

        foreign_user = make_user()
        community = make_community(creator=foreign_user)

        headers = make_authentication_headers_for_user(user)
        post = foreign_user.create_community_post(text=make_fake_post_text(), community_name=community.name)

        url = self._get_url(post)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(user.has_muted_post_with_id(post.pk))

    def test_cannot_mute_closed_community_post(self):
        """
        should not be able to mute closed post if not admin/mod or post creator in community
        """
        user = make_user()

        foreign_user = make_user()
        community = make_community(creator=foreign_user)
        user.join_community_with_name(community_name=community.name)

        headers = make_authentication_headers_for_user(user)
        post = foreign_user.create_community_post(text=make_fake_post_text(), community_name=community.name)
        post.is_closed = True
        post.save()

        url = self._get_url(post)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(user.has_muted_post_with_id(post.pk))

    def test_can_mute_closed_community_post_if_creator(self):
        """
        should be able to mute closed post if post creator in community
        """
        user = make_user()

        foreign_user = make_user()
        community = make_community(creator=foreign_user)
        user.join_community_with_name(community_name=community.name)

        headers = make_authentication_headers_for_user(user)
        post = user.create_community_post(text=make_fake_post_text(), community_name=community.name)
        post.is_closed = True
        post.save()

        url = self._get_url(post)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(user.has_muted_post_with_id(post.pk))

    def test_can_mute_closed_community_post_administrator(self):
        """
        should be able to mute closed post if administrator in community
        """
        user = make_user()

        admin = make_user()
        community = make_community(creator=admin)
        user.join_community_with_name(community_name=community.name)

        headers = make_authentication_headers_for_user(admin)
        post = user.create_community_post(text=make_fake_post_text(), community_name=community.name)
        post.is_closed = True
        post.save()

        url = self._get_url(post)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(admin.has_muted_post_with_id(post.pk))

    def test_can_mute_closed_community_post_if_moderator(self):
        """
        should be able to mute closed post if moderator in community
        """
        user = make_user()

        admin = make_user()
        moderator = make_user()
        community = make_community(creator=admin)
        user.join_community_with_name(community_name=community.name)
        moderator.join_community_with_name(community_name=community.name)
        admin.add_moderator_with_username_to_community_with_name(username=moderator.username,
                                                                 community_name=community.name)

        headers = make_authentication_headers_for_user(moderator)
        post = user.create_community_post(text=make_fake_post_text(), community_name=community.name)
        post.is_closed = True
        post.save()

        url = self._get_url(post)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(moderator.has_muted_post_with_id(post.pk))

    def test_cant_mute_community_post_if_private_and_not_member(self):
        user = make_user()

        foreign_user = make_user()
        community = make_community(creator=foreign_user, type='T')

        headers = make_authentication_headers_for_user(user)
        post = foreign_user.create_community_post(text=make_fake_post_text(), community_name=community.name)

        url = self._get_url(post)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(user.has_muted_post_with_id(post.pk))

    def test_can_mute_community_post_if_private_and_member(self):
        user = make_user()

        foreign_user = make_user()
        community = make_community(creator=foreign_user, type='T')

        headers = make_authentication_headers_for_user(user)
        post = foreign_user.create_community_post(text=make_fake_post_text(), community_name=community.name)

        foreign_user.invite_user_with_username_to_community_with_name(username=user.username,
                                                                      community_name=community.name)

        user.join_community_with_name(community_name=community.name)

        url = self._get_url(post)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(user.has_muted_post_with_id(post.pk))

    def _get_url(self, post):
        return reverse('mute-post', kwargs={
            'post_uuid': post.uuid
        })


class UnmutePostAPITests(APITestCase):
    """
    UnmutePostAPI
    """

    fixtures = [
        'openbook_circles/fixtures/circles.json'
    ]

    def test_can_unmute_own_post(self):
        """
        should be able to unmute own post and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        user.mute_post_with_id(post.pk)

        url = self._get_url(post)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(user.has_muted_post_with_id(post.pk))

    def test_cant_unmute_own_post_if_already_unmuted(self):
        """
        should not be able to unmute own post if already unmuted and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())

        url = self._get_url(post)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(user.has_muted_post_with_id(post.pk))

    def test_cannot_unmute_closed_community_post(self):
        """
        should not be able to unmute closed post if not admin/mod or post creator in community
        """
        user = make_user()

        foreign_user = make_user()
        community = make_community(creator=foreign_user)
        user.join_community_with_name(community_name=community.name)

        headers = make_authentication_headers_for_user(user)
        post = foreign_user.create_community_post(text=make_fake_post_text(), community_name=community.name)
        user.mute_post_with_id(post.pk)
        post.is_closed = True
        post.save()

        url = self._get_url(post)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(user.has_muted_post_with_id(post.pk))

    def test_can_unmute_closed_community_post_if_creator(self):
        """
        should be able to unmute closed post if post creator in community
        """
        user = make_user()

        foreign_user = make_user()
        community = make_community(creator=foreign_user)
        user.join_community_with_name(community_name=community.name)

        headers = make_authentication_headers_for_user(user)
        post = user.create_community_post(text=make_fake_post_text(), community_name=community.name)
        user.mute_post_with_id(post.pk)
        post.is_closed = True
        post.save()

        url = self._get_url(post)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(user.has_muted_post_with_id(post.pk))

    def test_can_unmute_closed_community_post_administrator(self):
        """
        should be able to unmute closed post if administrator in community
        """
        user = make_user()

        admin = make_user()
        community = make_community(creator=admin)
        user.join_community_with_name(community_name=community.name)

        headers = make_authentication_headers_for_user(admin)
        post = user.create_community_post(text=make_fake_post_text(), community_name=community.name)
        admin.mute_post_with_id(post.pk)
        post.is_closed = True
        post.save()

        url = self._get_url(post)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(admin.has_muted_post_with_id(post.pk))

    def test_can_unmute_closed_community_post_if_moderator(self):
        """
        should be able to unmute closed post if moderator in community
        """
        user = make_user()

        admin = make_user()
        moderator = make_user()
        community = make_community(creator=admin)
        user.join_community_with_name(community_name=community.name)
        moderator.join_community_with_name(community_name=community.name)
        admin.add_moderator_with_username_to_community_with_name(username=moderator.username,
                                                                 community_name=community.name)

        headers = make_authentication_headers_for_user(moderator)
        post = user.create_community_post(text=make_fake_post_text(), community_name=community.name)
        moderator.mute_post_with_id(post.pk)
        post.is_closed = True
        post.save()

        url = self._get_url(post)

        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(moderator.has_muted_post_with_id(post.pk))

    def _get_url(self, post):
        return reverse('unmute-post', kwargs={
            'post_uuid': post.uuid
        })


class PostCloseAPITests(APITestCase):
    """
    PostCloseAPITests APITests
    """

    def test_can_close_post_if_administrator_of_community(self):
        """
         should be able to close post if administrator of a community
        """
        user = make_user()
        admin = make_user()
        community = make_community(admin)

        user.join_community_with_name(community_name=community.name)
        post = user.create_community_post(community.name, text=make_fake_post_text())

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(admin)
        response = self.client.post(url, **headers)

        parsed_response = json.loads(response.content)

        self.assertTrue(response.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        self.assertTrue(post.is_closed)
        self.assertTrue(parsed_response['is_closed'])

    def test_can_close_post_if_moderator_of_community(self):
        """
         should be able to close post if moderator of a community
        """
        user = make_user()
        admin = make_user()
        moderator = make_user()
        community = make_community(admin)

        user.join_community_with_name(community_name=community.name)
        moderator.join_community_with_name(community_name=community.name)
        admin.add_moderator_with_username_to_community_with_name(username=moderator.username,
                                                                 community_name=community.name)
        post = user.create_community_post(community.name, text=make_fake_post_text())

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(moderator)
        response = self.client.post(url, **headers)

        parsed_response = json.loads(response.content)

        self.assertTrue(response.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        self.assertTrue(post.is_closed)
        self.assertTrue(parsed_response['is_closed'])

    def test_cannot_close_post_if_not_administrator_or_moderator_of_community(self):
        """
         should not be able to close post if not moderator/administrator of a community
        """
        user = make_user()
        admin = make_user()
        community = make_community(admin)

        user.join_community_with_name(community_name=community.name)
        post = user.create_community_post(community.name, text=make_fake_post_text())

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(user)
        response = self.client.post(url, **headers)

        self.assertTrue(response.status_code, status.HTTP_400_BAD_REQUEST)
        post.refresh_from_db()
        self.assertFalse(post.is_closed)

    def test_logs_close_post_by_administrator_of_community(self):
        """
         should log close post by administrator of a community
        """
        community_post_creator = make_user()
        admin = make_user()
        community = make_community(admin)

        community_post_creator.join_community_with_name(community_name=community.name)
        post = community_post_creator.create_community_post(community.name, text=make_fake_post_text())

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(admin)
        self.client.post(url, **headers)

        self.assertTrue(community.logs.filter(action_type='CP',
                                              post=post,
                                              source_user=admin,
                                              target_user=community_post_creator).exists())

    def _get_url(self, post):
        return reverse('close-post', kwargs={
            'post_uuid': post.uuid
        })


class PostOpenAPITests(APITestCase):
    """
    PostOpenAPITests APITests
    """

    def test_can_open_post_if_administrator_of_community(self):
        """
         should be able to open post if administrator of a community
        """
        user = make_user()
        admin = make_user()
        community = make_community(admin)

        user.join_community_with_name(community_name=community.name)
        post = user.create_community_post(community.name, text=make_fake_post_text())
        post.is_closed = True
        post.save()

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(admin)
        response = self.client.post(url, **headers)

        parsed_response = json.loads(response.content)

        self.assertTrue(response.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        self.assertFalse(post.is_closed)
        self.assertFalse(parsed_response['is_closed'])

    def test_can_open_post_if_moderator_of_community(self):
        """
         should be able to open post if moderator of a community
        """
        user = make_user()
        admin = make_user()
        moderator = make_user()
        community = make_community(admin)

        user.join_community_with_name(community_name=community.name)
        moderator.join_community_with_name(community_name=community.name)
        admin.add_moderator_with_username_to_community_with_name(username=moderator.username,
                                                                 community_name=community.name)
        post = user.create_community_post(community.name, text=make_fake_post_text())
        post.is_closed = True
        post.save()

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(moderator)
        response = self.client.post(url, **headers)

        parsed_response = json.loads(response.content)

        self.assertTrue(response.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        self.assertFalse(post.is_closed)
        self.assertFalse(parsed_response['is_closed'])

    def test_cannot_open_post_if_not_administrator_or_moderator_of_community(self):
        """
         should not be able to open post if not moderator/administrator of a community
        """
        user = make_user()
        admin = make_user()
        community = make_community(admin)

        user.join_community_with_name(community_name=community.name)
        post = user.create_community_post(community.name, text=make_fake_post_text())
        post.is_closed = True
        post.save()

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(user)
        response = self.client.post(url, **headers)

        self.assertTrue(response.status_code, status.HTTP_400_BAD_REQUEST)
        post.refresh_from_db()
        self.assertTrue(post.is_closed)

    def test_logs_open_post_by_administrator_of_community(self):
        """
         should log open post by administrator of a community
        """
        community_post_creator = make_user()
        admin = make_user()
        community = make_community(admin)

        community_post_creator.join_community_with_name(community_name=community.name)
        post = community_post_creator.create_community_post(community.name, text=make_fake_post_text())

        url = self._get_url(post)
        headers = make_authentication_headers_for_user(admin)
        self.client.post(url, **headers)

        self.assertTrue(community.logs.filter(action_type='OP',
                                              post=post,
                                              source_user=admin,
                                              target_user=community_post_creator).exists())

    def _get_url(self, post):
        return reverse('open-post', kwargs={
            'post_uuid': post.uuid
        })


class TranslatePostAPITests(APITestCase):
    """
    TranslatePostAPI
    """

    fixtures = [
        'openbook_common/fixtures/languages.json'
    ]

    def test_translate_post_text(self):
        """
        should translate post text and return 200
        """
        user = make_user()
        Language = get_language_model()
        user.translation_language = Language.objects.get(code='en')
        user.save()
        text = 'Ik ben en man 😀. Jij bent en vrouw.'
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=text)

        url = self._get_url(post=post)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_post = json.loads(response.content)
        self.assertEqual(response_post['translated_text'], 'I am a man 😀. You\'re a woman.')

    def test_cannot_translate_post_text_without_user_language(self):
        """
        should not translate post text and return 400 if user language is not set
        """
        user = make_user()
        text = 'Ik ben en man 😀. Jij bent en vrouw.'
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=text)

        url = self._get_url(post=post)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_translate_post_text_without_post_comment_language(self):
        """
        should not translate post text and return 400 if post language is not set
        """
        user = make_user()
        text = 'Ik ben en man 😀. Jij bent en vrouw.'
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=text)
        post.language = None
        post.save()

        url = self._get_url(post=post)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_return_error_between_unsupported_translate_pairs(self):
        """
        should return error when translating post between unsupported pairs (Norwegian to arabic) and return 400
        """
        user = make_user()
        Language = get_language_model()
        user.translation_language = Language.objects.get(code='ar')
        user.save()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=fake.text(max_nb_chars=30))
        post.language = Language.objects.get(code='no')
        post.save()

        url = self._get_url(post=post)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_return_error_when_text_length_exceeds_max_setting(self):
        """
        should return appropriate error when length of text is more than maximum in settings.py return 400
        """
        user = make_user()
        Language = get_language_model()
        user.translation_language = Language.objects.get(code='ar')
        user.save()
        headers = make_authentication_headers_for_user(user)
        post = user.create_public_post(text=make_fake_post_text())
        post.language = Language.objects.get(code='no')
        post.save()

        url = self._get_url(post=post)
        response = self.client.post(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def _get_url(self, post):
        return reverse('translate-post', kwargs={
            'post_uuid': post.uuid
        })


class SearchPostParticipantsAPITests(APITestCase):
    """
    SearchPostParticipantsAPI
    """

    fixtures = [
        'openbook_circles/fixtures/circles.json',
    ]

    def test_retrieves_post_creator_by_username(self):
        """
        should retrieve the post creator by username and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()
        post = post_creator.create_public_post(text=make_fake_post_text())

        url = self._get_url(post)

        search_query = post_creator.username[:int(len(post_creator.username) / 2)]

        response = self.client.post(url, {
            'query': search_query
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_participants = json.loads(response.content)

        self.assertEqual(response_participants[0]['id'], post_creator.pk)

    def test_retrieves_post_creator_by_name(self):
        """
        should retrieve the post creator by name and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()
        post = post_creator.create_public_post(text=make_fake_post_text())

        url = self._get_url(post)

        search_query = post_creator.profile.name[:int(len(post_creator.profile.name) / 2)]

        response = self.client.post(url, {
            'query': search_query
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_participants = json.loads(response.content)

        self.assertEqual(response_participants[0]['id'], post_creator.pk)

    def test_retrieves_post_commentator_by_username(self):
        """
        should retrieve a post commentator by username and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()
        post = post_creator.create_public_post(text=make_fake_post_text())

        post_commentator = make_user()
        post_commentator.comment_post(post=post, text=make_fake_post_comment_text())

        url = self._get_url(post)

        search_query = post_commentator.username[:int(len(post_commentator.username) / 2)]

        response = self.client.post(url, {
            'query': search_query
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_participants = json.loads(response.content)

        found = False

        for response_participant in response_participants:
            if response_participant['id'] == post_commentator.pk:
                found = True
                break

        self.assertTrue(found)

    def test_retrieves_post_commentator_by_name(self):
        """
        should retrieve a post commentator by name and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()
        post = post_creator.create_public_post(text=make_fake_post_text())

        post_commentator = make_user()
        post_commentator.comment_post(post=post, text=make_fake_post_comment_text())

        url = self._get_url(post)

        search_query = post_commentator.profile.name[:int(len(post_commentator.profile.name) / 2)]

        response = self.client.post(url, {
            'query': search_query
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_participants = json.loads(response.content)

        found = False

        for response_participant in response_participants:
            if response_participant['id'] == post_commentator.pk:
                found = True
                break

        self.assertTrue(found)

    def test_retrieves_post_community_member_by_username(self):
        """
        should retrieve a post community member by username and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community()

        post_creator = make_user()
        post_creator.join_community_with_name(community_name=community.name)
        post = post_creator.create_community_post(community_name=community, text=make_fake_post_text())

        post_community_member = make_user()
        post_community_member.join_community_with_name(community_name=community.name)

        url = self._get_url(post)

        search_query = post_community_member.username[:int(len(post_community_member.username) / 2)]

        response = self.client.post(url, {
            'query': search_query
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_participants = json.loads(response.content)

        found = False

        for response_participant in response_participants:
            if response_participant['id'] == post_community_member.pk:
                found = True
                break

        self.assertTrue(found)

    def test_retrieves_post_community_member_by_name(self):
        """
        should retrieve a post community member by name and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community()

        post_creator = make_user()
        post_creator.join_community_with_name(community_name=community.name)
        post = post_creator.create_community_post(community_name=community, text=make_fake_post_text())

        post_community_member = make_user()
        post_community_member.join_community_with_name(community_name=community.name)

        url = self._get_url(post)

        search_query = post_community_member.profile.name[:int(len(post_community_member.profile.name) / 2)]

        response = self.client.post(url, {
            'query': search_query
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_participants = json.loads(response.content)

        found = False

        for response_participant in response_participants:
            if response_participant['id'] == post_community_member.pk:
                found = True
                break

        self.assertTrue(found)

    def test_retrieves_follower_by_username(self):
        """
        should retrieve a follower by username and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()
        post = post_creator.create_public_post(text=make_fake_post_text())

        follower = make_user()
        follower.follow_user(user=user)

        url = self._get_url(post)

        search_query = follower.username[:int(len(follower.username) / 2)]

        response = self.client.post(url, {
            'query': search_query
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_participants = json.loads(response.content)

        found = False

        for response_participant in response_participants:
            if response_participant['id'] == follower.pk:
                found = True
                break

        self.assertTrue(found)

    def test_retrieves_follower_by_name(self):
        """
        should retrieve a follower by name and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()
        post = post_creator.create_public_post(text=make_fake_post_text())

        follower = make_user()
        follower.follow_user(user=user)

        url = self._get_url(post)

        search_query = follower.profile.name[:int(len(follower.profile.name) / 2)]

        response = self.client.post(url, {
            'query': search_query
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_participants = json.loads(response.content)

        found = False

        for response_participant in response_participants:
            if response_participant['id'] == follower.pk:
                found = True
                break

        self.assertTrue(found)

    def test_retrieves_connection_by_username(self):
        """
        should retrieve a connection by username and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()
        post = post_creator.create_public_post(text=make_fake_post_text())

        connection = make_user()
        connection.connect_with_user_with_id(user_id=user.pk)

        user.confirm_connection_with_user_with_id(user_id=connection.pk)

        url = self._get_url(post)

        search_query = connection.username[:int(len(connection.username) / 2)]

        response = self.client.post(url, {
            'query': search_query
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_participants = json.loads(response.content)

        found = False

        for response_participant in response_participants:
            if response_participant['id'] == connection.pk:
                found = True
                break

        self.assertTrue(found)

    def test_retrieves_connection_by_name(self):
        """
        should retrieve a connection by name and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()
        post = post_creator.create_public_post(text=make_fake_post_text())

        connection = make_user()
        connection.connect_with_user_with_id(user_id=user.pk)

        user.confirm_connection_with_user_with_id(user_id=connection.pk)

        url = self._get_url(post)

        search_query = connection.profile.name[:int(len(connection.profile.name) / 2)]

        response = self.client.post(url, {
            'query': search_query
        }, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_participants = json.loads(response.content)

        found = False

        for response_participant in response_participants:
            if response_participant['id'] == connection.pk:
                found = True
                break

        self.assertTrue(found)

    def _get_url(self, post):
        return reverse('search-post-participants', kwargs={
            'post_uuid': post.uuid
        })


class GetPostParticipantsAPITests(APITestCase):
    """
    SearchPostParticipantsAPI
    """

    fixtures = [
        'openbook_circles/fixtures/circles.json',
    ]

    def test_retrieves_post_creator(self):
        """
        should retrieve the post creator and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()
        post = post_creator.create_public_post(text=make_fake_post_text())

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_participants = json.loads(response.content)

        self.assertEqual(response_participants[0]['id'], post_creator.pk)

    def test_retrieves_post_commentator(self):
        """
        should retrieve a post commentator and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()
        post = post_creator.create_public_post(text=make_fake_post_text())

        post_commentator = make_user()
        post_commentator.comment_post(post=post, text=make_fake_post_comment_text())

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_participants = json.loads(response.content)

        found = False

        for response_participant in response_participants:
            if response_participant['id'] == post_commentator.pk:
                found = True
                break

        self.assertTrue(found)

    def test_retrieves_post_community_member(self):
        """
        should retrieve a post community member and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community()

        post_creator = make_user()
        post_creator.join_community_with_name(community_name=community.name)
        post = post_creator.create_community_post(community_name=community, text=make_fake_post_text())

        post_community_member = make_user()
        post_community_member.join_community_with_name(community_name=community.name)

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_participants = json.loads(response.content)

        found = False

        for response_participant in response_participants:
            if response_participant['id'] == post_community_member.pk:
                found = True
                break

        self.assertTrue(found)

    def test_retrieves_follower(self):
        """
        should retrieve a follower and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()
        post = post_creator.create_public_post(text=make_fake_post_text())

        follower = make_user()
        follower.follow_user(user=user)

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_participants = json.loads(response.content)

        found = False

        for response_participant in response_participants:
            if response_participant['id'] == follower.pk:
                found = True
                break

        self.assertTrue(found)

    def test_retrieves_connection(self):
        """
        should retrieve a connection and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        post_creator = make_user()
        post = post_creator.create_public_post(text=make_fake_post_text())

        connection = make_user()
        connection.connect_with_user_with_id(user_id=user.pk)

        user.confirm_connection_with_user_with_id(user_id=connection.pk)

        url = self._get_url(post)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_participants = json.loads(response.content)

        found = False

        for response_participant in response_participants:
            if response_participant['id'] == connection.pk:
                found = True
                break

        self.assertTrue(found)

    def _get_url(self, post):
        return reverse('get-post-participants', kwargs={
            'post_uuid': post.uuid
        })
