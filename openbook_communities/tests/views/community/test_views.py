import json

from django.conf import settings
from django.core.files import File
from django.urls import reverse
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase

from openbook_common.tests.helpers import make_user, make_authentication_headers_for_user, \
    make_community_name, make_community, \
    make_community_title, make_community_rules, make_community_description, make_community_user_adjective, \
    make_community_users_adjective, make_community_avatar, make_community_cover, make_category

fake = Faker()


class CommunityAPITests(APITestCase):
    """
    CommunityAPITests
    """

    def test_can_retrieve_public_community(self):
        """
        should be able to retrieve a public community and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='P')
        community_name = community.name

        url = self._get_url(community_name=community_name)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        parsed_response = json.loads(response.content)

        self.assertIn('name', parsed_response)
        response_name = parsed_response['name']
        self.assertEqual(response_name, community_name)

    def test_can_retrieve_private_community(self):
        """
        should be able to retrieve a private community and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user, type='T')
        community_name = community.name

        url = self._get_url(community_name=community_name)

        response = self.client.get(url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        parsed_response = json.loads(response.content)

        self.assertIn('name', parsed_response)
        response_name = parsed_response['name']
        self.assertEqual(response_name, community_name)

    def test_non_member_cannot_update_community(self):
        """
        a non member of a community should not be able to update a community
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user)

        new_community_name = make_community_name()

        data = {
            'name': new_community_name
        }

        url = self._get_url(community_name=community.name)

        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        community.refresh_from_db()

        self.assertNotEqual(community.name, new_community_name)

    def test_member_cannot_update_community(self):
        """
        a community member should not be able to update a community
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user)

        user.join_community_with_name(community_name=community.name)

        new_community_name = make_community_name()

        data = {
            'name': new_community_name
        }

        url = self._get_url(community_name=community.name)

        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        community.refresh_from_db()

        self.assertNotEqual(community.name, new_community_name)

    def test_moderator_cannot_update_community(self):
        """
        a community moderator should not be able to update a community
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user)

        user.join_community_with_name(community_name=community.name)

        other_user.add_moderator_with_username_to_community_with_name(username=user.username,
                                                                      community_name=community.name)

        new_community_name = make_community_name()

        data = {
            'name': new_community_name
        }

        url = self._get_url(community_name=community.name)

        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        community.refresh_from_db()

        self.assertNotEqual(community.name, new_community_name)

    def test_can_update_administrated_community_name(self):
        """
        should be able to update an administrated community name
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community(creator=user)
        new_community_name = make_community_name()

        data = {
            'name': new_community_name
        }

        url = self._get_url(community_name=community.name)

        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        community.refresh_from_db()

        self.assertEqual(community.name, new_community_name)

    def test_cannot_update_administrated_community_name_to_taken_name(self):
        """
        should not be able to update an administrated community name to an existing one and return 400
        """
        user = make_user()
        other_user = make_user()

        other_community = make_community(creator=other_user)
        community = make_community(creator=user)

        data = {
            'name': other_community.name
        }

        headers = make_authentication_headers_for_user(user)

        url = self._get_url(community_name=community.name)

        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        community.refresh_from_db()

        self.assertNotEqual(community.name, other_community.name)

    def test_can_update_administrated_community_type(self):
        """
        should be able to update an administrated community type
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community(creator=user, type='P')
        new_community_type = 'T'

        data = {
            'type': new_community_type
        }

        url = self._get_url(community_name=community.name)

        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        community.refresh_from_db()

        self.assertEqual(community.type, new_community_type)

    def test_can_update_administrated_community_title(self):
        """
        should be able to update an administrated community title
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community(creator=user)
        new_community_title = make_community_title()

        data = {
            'title': new_community_title
        }

        url = self._get_url(community_name=community.name)

        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        community.refresh_from_db()

        self.assertEqual(community.title, new_community_title)

    def test_can_update_administrated_community_users_adjective(self):
        """
        should be able to update an administrated community users_adjective
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community(creator=user)
        new_community_users_adjective = make_community_users_adjective()

        data = {
            'users_adjective': new_community_users_adjective
        }

        url = self._get_url(community_name=community.name)

        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        community.refresh_from_db()

        self.assertEqual(community.users_adjective, new_community_users_adjective)

    def test_can_update_administrated_community_members_can_invite_members(self):
        """
        should be able to update an administrated community members_can_invite_members
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community(creator=user)
        community.members_can_invite_members = fake.boolean()
        community.save()

        new_community_users_adjective = not community.members_can_invite_members

        data = {
            'members_can_invite_members': new_community_users_adjective
        }

        url = self._get_url(community_name=community.name)

        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        community.refresh_from_db()

        self.assertEqual(community.members_can_invite_members, new_community_users_adjective)

    def test_can_update_administrated_community_user_adjective(self):
        """
        should be able to update an administrated community user_adjective
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community(creator=user)
        new_community_user_adjective = make_community_user_adjective()

        data = {
            'user_adjective': new_community_user_adjective
        }

        url = self._get_url(community_name=community.name)

        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        community.refresh_from_db()

        self.assertEqual(community.user_adjective, new_community_user_adjective)

    def test_can_update_administrated_community_color(self):
        """
        should be able to update an administrated community color
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community(creator=user)
        new_community_color = fake.hex_color()

        data = {
            'color': new_community_color
        }

        url = self._get_url(community_name=community.name)

        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        community.refresh_from_db()

        self.assertEqual(community.color, new_community_color)

    def test_can_update_administrated_community_description(self):
        """
        should be able to update an administrated community description
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community(creator=user)
        new_community_description = make_community_description()

        data = {
            'description': new_community_description
        }

        url = self._get_url(community_name=community.name)

        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        community.refresh_from_db()

        self.assertEqual(community.description, new_community_description)

    def test_can_update_administrated_community_rules(self):
        """
        should be able to update an administrated community rules
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community(creator=user)
        new_community_rules = make_community_rules()

        data = {
            'rules': new_community_rules
        }

        url = self._get_url(community_name=community.name)

        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        community.refresh_from_db()

        self.assertEqual(community.rules, new_community_rules)

    def test_can_delete_administrated_community_description(self):
        """
        should be able to delete the administrated community description and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community(creator=user)

        data = {
            'description': ''
        }

        url = self._get_url(community_name=community.name)

        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        community.refresh_from_db()

        self.assertTrue(not community.description)

    def test_can_delete_administrated_community_rules(self):
        """
        should be able to delete the administrated community rules and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community(creator=user)

        data = {
            'rules': ''
        }

        url = self._get_url(community_name=community.name)

        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        community.refresh_from_db()

        self.assertTrue(not community.rules)

    def test_can_delete_administrated_community_user_adjective(self):
        """
        should be able to delete the administrated community user_adjective and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community(creator=user)

        data = {
            'user_adjective': ''
        }

        url = self._get_url(community_name=community.name)

        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        community.refresh_from_db()

        self.assertTrue(not community.user_adjective)

    def test_can_delete_administrated_community_users_adjective(self):
        """
        should be able to delete the administrated community users_adjective and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community(creator=user)

        data = {
            'users_adjective': ''
        }

        url = self._get_url(community_name=community.name)

        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        community.refresh_from_db()

        self.assertTrue(not community.users_adjective)

    def test_can_update_administrated_community_categories(self):
        """
        should be able to update the administrated community categories and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community(creator=user)
        new_categories = []

        for i in range(settings.COMMUNITY_CATEGORIES_MIN_AMOUNT, settings.COMMUNITY_CATEGORIES_MAX_AMOUNT):
            category = make_category()
            new_categories.append(category)

        data = {
            'categories': ','.join(map(str, [category.name for category in new_categories]))
        }

        url = self._get_url(community_name=community.name)

        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        community.refresh_from_db()

        categories = community.categories.all()
        categories_ids = [category.pk for category in categories]

        self.assertEqual(len(categories), len(new_categories))

        for new_category in new_categories:
            self.assertIn(new_category.pk, categories_ids)

    def test_cannot_delete_administrated_community_categories(self):
        """
        should not be able to update the administrated community categories and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community(creator=user)

        data = {
            'categories': ''
        }

        url = self._get_url(community_name=community.name)

        response = self.client.patch(url, data, **headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        community.refresh_from_db()

        self.assertTrue(community.categories.exists())

    def _get_url(self, community_name):
        return reverse('community', kwargs={
            'community_name': community_name
        })


class CommunityAvatarAPITests(APITestCase):
    """
    CommunityAvatarAPITests
    """

    def test_can_update_administrated_community_avatar(self):
        """
        should be able to update the avatar of an administrated community and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community(creator=user)
        community.avatar = None
        community.save()

        new_avatar = make_community_avatar()

        data = {
            'avatar': new_avatar
        }

        url = self._get_url(community_name=community.name)

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()

        self.assertIsNotNone(community.avatar)

    def test_can_delete_administrated_community_avatar(self):
        """
        should be able to delete the avatar of an administrated community and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community(creator=user)
        community.avatar.save('avatar.jpg', File(make_community_avatar()))

        url = self._get_url(community_name=community.name)

        response = self.client.delete(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        community.refresh_from_db()

        self.assertTrue(not community.avatar)

    def _get_url(self, community_name):
        return reverse('community-avatar', kwargs={
            'community_name': community_name
        })


class CommunityCoverAPITests(APITestCase):
    """
    CommunityCoverAPITests
    """

    def test_can_update_administrated_community_cover(self):
        """
        should be able to update the cover of an administrated community and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community(creator=user)
        community.cover = None
        community.save()

        new_cover = make_community_cover()

        data = {
            'cover': new_cover
        }

        url = self._get_url(community_name=community.name)

        response = self.client.put(url, data, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()

        self.assertIsNotNone(community.cover)

    def test_can_delete_administrated_community_cover(self):
        """
        should be able to delete the cover of an administrated community and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        community = make_community(creator=user)
        community.cover.save('cover.jpg', File(make_community_cover()))

        url = self._get_url(community_name=community.name)

        response = self.client.delete(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        community.refresh_from_db()

        self.assertTrue(not community.cover)

    def _get_url(self, community_name):
        return reverse('community-cover', kwargs={
            'community_name': community_name
        })


class FavoriteCommunityAPITests(APITestCase):
    """
    FavoriteCommunityAPITests
    """

    def test_cant_favorite_not_joined_community(self):
        """
        should not be able to favorite a community not joined
        :return:
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user)

        url = self._get_url(community_name=community.name)

        response = self.client.put(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(user.has_favorite_community_with_name(community.name))

    def test_can_favorite_joined_community(self):
        """
        should be able to favorite a joined community and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user)

        user.join_community_with_name(community.name)

        url = self._get_url(community_name=community.name)

        response = self.client.put(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(user.has_favorite_community_with_name(community.name))

    def test_cant_favorite_already_favorite_community(self):
        """
        should not be be able to favorite an already favorite community and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user)

        user.join_community_with_name(community.name)
        user.favorite_community_with_name(community.name)

        url = self._get_url(community_name=community.name)

        response = self.client.put(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue(user.has_favorite_community_with_name(community.name))

    def test_can_unfavorite_favorite_community(self):
        """
        should be able to unfavorite a favorite community and return 200
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user)

        user.join_community_with_name(community.name)
        user.favorite_community_with_name(community.name)

        url = self._get_url(community_name=community.name)

        response = self.client.delete(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(user.has_favorite_community_with_name(community.name))

    def test_cant_unfavorite_not_favorite_community(self):
        """
        should not be able to unfavorite a non favorite community and return 400
        """
        user = make_user()
        headers = make_authentication_headers_for_user(user)

        other_user = make_user()
        community = make_community(creator=other_user)

        user.join_community_with_name(community.name)

        url = self._get_url(community_name=community.name)

        response = self.client.delete(url, **headers, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertFalse(user.has_favorite_community_with_name(community.name))

    def _get_url(self, community_name):
        return reverse('favorite-community', kwargs={
            'community_name': community_name
        })
