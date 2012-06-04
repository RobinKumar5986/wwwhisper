from wwwhisper_auth.tests.utils import HttpTestCase
from wwwhisper_auth.models import SITE_URL

import wwwhisper_admin.views
import json

FAKE_UUID = '41be0192-0fcc-4a9c-935d-69243b75533c'
TEST_USER_EMAIL = 'foo@bar.org'
TEST_LOCATION = '/pub/kika/'

def uid_regexp():
   return '[0-9a-z-]{36}'

def extract_uuid(urn):
   return urn.replace('urn:uuid:', '')

class AdminViewTestCase(HttpTestCase):

   def add_user(self, user_name=TEST_USER_EMAIL):
      response = self.post('/admin/api/users/', {'email' : user_name})
      self.assertEqual(201, response.status_code)
      return json.loads(response.content)

   def add_location(self):
      response = self.post('/admin/api/locations/', {'path' : TEST_LOCATION})
      self.assertEqual(201, response.status_code)
      return json.loads(response.content)

class UserTest(AdminViewTestCase):

   def test_add_user(self):
      response = self.post('/admin/api/users/', {'email' : TEST_USER_EMAIL})
      self.assertEqual(201, response.status_code)

      parsed_response_body = json.loads(response.content)
      user_uuid = extract_uuid(parsed_response_body['id'])

      self.assertRegexpMatches(parsed_response_body['id'],
                               '^urn:uuid:%s$' % uid_regexp())
      self.assertEqual(TEST_USER_EMAIL, parsed_response_body['email'])
      self_url = '%s/admin/api/users/%s/' % (SITE_URL, user_uuid)
      self.assertEqual(self_url, parsed_response_body['self'])
      self.assertEqual(self_url, response['Location'])
      self.assertEqual(self_url, response['Content-Location'])

   def test_get_user(self):
      parsed_add_user_response_body = self.add_user()
      get_response = self.get(parsed_add_user_response_body['self'])
      self.assertEqual(200, get_response.status_code)
      parsed_get_response_body = json.loads(get_response.content)
      self.assertEqual(parsed_add_user_response_body, parsed_get_response_body)

   def test_delete_user(self):
      user_url = self.add_user()['self']
      self.assertEqual(204, self.delete(user_url).status_code)
      self.assertEqual(404, self.get(user_url).status_code)

   def test_get_users_list(self):
      self.assertEqual(201, self.post('/admin/api/users/',
                                      {'email' : 'foo@bar.org'}).status_code)
      self.assertEqual(201, self.post('/admin/api/users/',
                                      {'email' : 'baz@bar.org'}).status_code)
      self.assertEqual(201, self.post('/admin/api/users/',
                                      {'email' : 'boo@bar.org'}).status_code)
      response = self.get('/admin/api/users/')
      self.assertEqual(200, response.status_code)
      parsed_response_body = json.loads(response.content)
      self.assertEqual('%s/admin/api/users/' % SITE_URL,
                       parsed_response_body['self'])

      users = parsed_response_body['users']
      self.assertEqual(3, len(users))
      self.assertItemsEqual(['foo@bar.org', 'baz@bar.org', 'boo@bar.org'],
                            [item['email'] for item in users])

   def test_get_not_existing_user(self):
      response = self.get('/admin/api/users/%s/' % FAKE_UUID)
      self.assertEqual(404, response.status_code)
      self.assertRegexpMatches(response.content, 'User not found')

   def test_add_user_invalid_email(self):
      response = self.post('/admin/api/users/', {'email' : 'foo.bar'})
      self.assertEqual(400, response.status_code)
      self.assertRegexpMatches(response.content, 'Invalid email format')

   def test_add_existing_user(self):
      self.add_user()
      response = self.post('/admin/api/users/', {'email' : TEST_USER_EMAIL})
      self.assertEqual(400, response.status_code)
      self.assertRegexpMatches(response.content, 'User already exists')

   def test_delete_user_twice(self):
      user_url = self.add_user()['self']
      response = self.delete(user_url)
      self.assertEqual(204, response.status_code)

      response = self.delete(user_url)
      self.assertEqual(404, response.status_code)
      self.assertRegexpMatches(response.content, 'User not found')


class LocationTest(AdminViewTestCase):

   def test_add_location(self):
      response = self.post('/admin/api/locations/', {'path' : TEST_LOCATION})
      self.assertEqual(201, response.status_code)

      parsed_response_body = json.loads(response.content)
      location_uuid = extract_uuid(parsed_response_body['id'])

      self.assertRegexpMatches(parsed_response_body['id'],
                               '^urn:uuid:%s$' % uid_regexp())
      self.assertEqual(TEST_LOCATION, parsed_response_body['path'])
      self_url = '%s/admin/api/locations/%s/' % (SITE_URL, location_uuid)
      self.assertEqual(self_url, parsed_response_body['self'])
      self.assertEqual(self_url, response['Location'])
      self.assertEqual(self_url, response['Content-Location'])

   def test_get_location(self):
      parsed_add_location_response_body = self.add_location()
      get_response = self.get(parsed_add_location_response_body['self'])
      self.assertEqual(200, get_response.status_code)
      parsed_get_response_body = json.loads(get_response.content)
      self.assertEqual(parsed_add_location_response_body,
                       parsed_get_response_body)

   def test_delete_location(self):
      location_url = self.add_location()['self']
      self.assertEqual(204, self.delete(location_url).status_code)
      self.assertEqual(404, self.get(location_url).status_code)

   def test_get_locations_list(self):
      self.assertEqual(201, self.post('/admin/api/locations/',
                                      {'path' : '/foo/bar'}).status_code)
      self.assertEqual(201, self.post('/admin/api/locations/',
                                      {'path' : '/baz/bar'}).status_code)
      self.assertEqual(201, self.post('/admin/api/locations/',
                                      {'path' : '/boo/bar/'}).status_code)
      response = self.get('/admin/api/locations/')
      self.assertEqual(200, response.status_code)
      parsed_response_body = json.loads(response.content)
      self.assertEquals('%s/admin/api/locations/' % SITE_URL,
                        parsed_response_body['self'])

      locations = parsed_response_body['locations']
      self.assertEqual(3, len(locations))
      self.assertItemsEqual(['/foo/bar', '/baz/bar', '/boo/bar/'],
                            [item['path'] for item in locations])

   def test_get_not_existing_location(self):
      response = self.get('/admin/api/locations/%s/' % FAKE_UUID)
      self.assertEqual(404, response.status_code)
      self.assertRegexpMatches(response.content, 'Location not found')

   def test_add_location_invalid_path(self):
      response = self.post('/admin/api/locations/', {'path' : '/foo/../bar'})
      self.assertEqual(400, response.status_code)
      self.assertRegexpMatches(response.content,
                               'Path should be normalized')

   def test_add_existing_location(self):
      self.add_location()
      response = self.post('/admin/api/locations/', {'path' : TEST_LOCATION})
      self.assertEqual(400, response.status_code)
      self.assertRegexpMatches(response.content, 'Location already exists')

   def test_delete_location_twice(self):
      location_url = self.add_location()['self']
      response = self.delete(location_url)
      self.assertEqual(204, response.status_code)

      response = self.delete(location_url)
      self.assertEqual(404, response.status_code)
      self.assertRegexpMatches(response.content, 'Location not found')


class AccessControlTest(AdminViewTestCase):

   def can_access(self, location_url, user_uuid):
      response = self.get(location_url + 'allowed-users/' + user_uuid + '/')
      self.assertTrue(response.status_code == 200
                      or response.status_code == 404)
      return response.status_code == 200

   def test_grant_access(self):
      location_url = self.add_location()['self']

      response = self.add_user()
      user_url = response['self']
      user_urn = response['id']
      user_uuid = extract_uuid(user_urn)

      response = self.put(location_url + 'allowed-users/' + user_uuid + '/')
      self.assertEqual(201, response.status_code)

      parsed_response_body = json.loads(response.content)
      resource_url = location_url + 'allowed-users/' + user_uuid + '/'
      self.assertEqual(resource_url, response['Location'])
      self.assertFalse(response.has_header('Content-Location'))
      self.assertEqual(resource_url, parsed_response_body['self'])
      self.assertEqual(user_url, parsed_response_body['user']['self'])
      self.assertEqual(user_urn, parsed_response_body['user']['id'])
      self.assertEqual(TEST_USER_EMAIL, parsed_response_body['user']['email'])

   def test_grant_access_creates_allowed_user_resource(self):
      location_url = self.add_location()['self']

      response = self.add_user()
      user_url = response['self']
      user_uuid = extract_uuid(response['id'])

      self.assertFalse(self.can_access(location_url, user_uuid))
      self.put(location_url + 'allowed-users/' + user_uuid + "/")
      self.assertTrue(self.can_access(location_url, user_uuid))


   def test_revoke_access(self):
      location_url = self.add_location()['self']

      response = self.add_user()
      user_url = response['self']
      user_uuid = extract_uuid(response['id'])

      # Allow access.
      self.put(location_url + 'allowed-users/' + user_uuid + "/")
      self.assertTrue(self.can_access(location_url, user_uuid))

      # Revoke access.
      response = self.delete(location_url + 'allowed-users/' + user_uuid + "/")
      self.assertEqual(204, response.status_code)
      self.assertFalse(self.can_access(location_url, user_uuid))

   def test_location_lists_allowed_users(self):
      location_url = self.add_location()['self']

      # Create two users.
      user1_urn = self.add_user('user1@acme.com')['id']
      user1_uuid = extract_uuid(user1_urn)

      user2_urn = self.add_user('user2@acme.com')['id']
      user2_uuid = extract_uuid(user2_urn)

      self.put(location_url + 'allowed-users/' + user1_uuid + "/")
      self.put(location_url + 'allowed-users/' + user2_uuid + "/")

      response = self.get(location_url)
      parsed_response_body = json.loads(response.content)
      allowed_users = parsed_response_body['allowedUsers']
      self.assertEqual(2, len(allowed_users))
      self.assertItemsEqual(['user1@acme.com', 'user2@acme.com'],
                            [item['email'] for item in allowed_users])
      self.assertItemsEqual([user1_urn, user2_urn],
                            [item['id'] for item in allowed_users])

   def test_grant_access_to_not_existing_location(self):
      location_url = '/admin/api/locations/%s/' % FAKE_UUID
      user_uuid = extract_uuid(self.add_user()['id'])

      response = self.put(location_url + 'allowed-users/' + user_uuid + '/')
      self.assertEqual(404, response.status_code)
      self.assertRegexpMatches(response.content, 'Location not found')

   def test_grant_access_for_not_existing_user(self):
      location_url = self.add_location()['self']
      user_uuid =  FAKE_UUID

      response = self.put(location_url + 'allowed-users/' + user_uuid + '/')
      self.assertEqual(404, response.status_code)
      self.assertRegexpMatches(response.content, 'User not found')


   # PUT should be indempontent, granting access for the second time
   # should not return an error.
   def test_grant_access_twice(self):
      location_url = self.add_location()['self']

      response = self.add_user()
      user_url = response['self']
      user_uuid = extract_uuid(response['id'])

      response1 = self.put(location_url + 'allowed-users/' + user_uuid + "/")
      self.assertEqual(201, response1.status_code)
      self.assertTrue(response1.has_header('Location'))

      response2 = self.put(location_url + 'allowed-users/' + user_uuid + "/")
      self.assertEqual(200, response2.status_code)
      self.assertFalse(response2.has_header('Location'))

      self.assertEqual(response1.content, response2.content)

   def test_revoke_access_twice(self):
      location_url = self.add_location()['self']

      response = self.add_user()
      user_url = response['self']
      user_uuid = extract_uuid(response['id'])

      # Allow access.
      self.put(location_url + 'allowed-users/' + user_uuid + "/")
      self.assertTrue(self.can_access(location_url, user_uuid))

      # Revoke access.
      response = self.delete(location_url + 'allowed-users/' + user_uuid + "/")
      self.assertEqual(204, response.status_code)

      response = self.delete(location_url + 'allowed-users/' + user_uuid + "/")
      self.assertEqual(404, response.status_code)
      self.assertRegexpMatches(response.content,
                               'User can not access location.')

      self.assertFalse(self.can_access(location_url, user_uuid))
