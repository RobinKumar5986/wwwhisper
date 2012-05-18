from wwwhisper_auth.tests import HttpTestCase

#import wwwhisper_service.urls
import wwwhisper_admin.views
import json

def site_url():
   return wwwhisper_admin.views.site_url()

def uid_regexp():
   return '[0-9a-z-]{36}'

class UserTest(HttpTestCase):

   def test_add_user(self):
      response = self.post('/admin/api/users/', {'email' : 'foo@bar.org'})
      self.assertEqual(201, response.status_code)

      parsed_response_body = json.loads(response.content)
      self.assertEqual('foo@bar.org', parsed_response_body['email'])
      self.assertRegexpMatches(parsed_response_body['id'],
                               '^urn:uuid:%s$' % uid_regexp())

      self_url_regexp = '^%s/admin/api/users/%s/$' % (site_url(), uid_regexp())
      self.assertRegexpMatches(parsed_response_body['self'], self_url_regexp)
      self.assertRegexpMatches(response['Location'], self_url_regexp)
      self.assertRegexpMatches(response['Content-Location'], self_url_regexp)

   def test_get_user(self):
      post_response = self.post('/admin/api/users/', {'email' : 'foo@bar.org'})
      self.assertEqual(201, post_response.status_code)
      parsed_post_response_body = json.loads(post_response.content)

      get_response = self.get(parsed_post_response_body['self'])
      self.assertEqual(200, get_response.status_code)
      parsed_get_response_body = json.loads(get_response.content)

      self.assertEqual(post_response.content, get_response.content)

   def test_delete_user(self):
      response = self.post('/admin/api/users/', {'email' : 'foo@bar.org'})
      self.assertEqual(201, response.status_code)

      parsed_response_body = json.loads(response.content)
      response = self.delete(parsed_response_body['self'])
      self.assertEqual(204, response.status_code)

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
      self.assertRegexpMatches(parsed_response_body['self'],
                               '^%s/admin/api/users/$' % site_url())

      users = parsed_response_body['users']
      self.assertEqual(3, len(users))
      self.assertItemsEqual(['foo@bar.org', 'baz@bar.org', 'boo@bar.org'],
                            [item['email'] for item in users])

   def test_get_not_existing_user(self):
      response = self.get(
         '/admin/api/users/41be0192-0fcc-4a9c-935d-69243b75533c/')
      self.assertEqual(404, response.status_code)
      self.assertRegexpMatches(response.content, 'User not found')

   # TODO: make this a generic test for the RestView.
   def test_add_user_invalid_arg_name(self):
      response = self.post('/admin/api/users/', {'eemail' : 'foo@bar.org'})
      self.assertEqual(400, response.status_code)
      self.assertRegexpMatches(response.content, 'Invalid request arguments')

   def test_add_user_invalid_email(self):
      response = self.post('/admin/api/users/', {'email' : 'foo.bar'})
      self.assertEqual(400, response.status_code)
      self.assertRegexpMatches(response.content, 'Invalid email format')

   def test_add_existing_user(self):
      response = self.post('/admin/api/users/', {'email' : 'foo@bar.org'})
      self.assertEqual(201, response.status_code)

      response = self.post('/admin/api/users/', {'email' : 'foo@bar.org'})
      self.assertEqual(400, response.status_code)
      self.assertRegexpMatches(response.content, 'User already exists')

   def test_delete_user_twice(self):
      response = self.post('/admin/api/users/', {'email' : 'foo@bar.org'})
      self.assertEqual(201, response.status_code)

      parsed_response_body = json.loads(response.content)
      response = self.delete(parsed_response_body['self'])
      self.assertEqual(204, response.status_code)

      response = self.delete(parsed_response_body['self'])
      self.assertEqual(404, response.status_code)
      self.assertRegexpMatches(response.content, 'User not found')


class LocationTest(HttpTestCase):

   def test_add_location(self):
      response = self.post('/admin/api/locations/', {'path' : '/foo/bar'})
      self.assertEqual(201, response.status_code)

      parsed_response_body = json.loads(response.content)
      self.assertEqual('/foo/bar', parsed_response_body['path'])
      self.assertRegexpMatches(parsed_response_body['id'],
                               '^urn:uuid:%s$' % uid_regexp())

      self_url_regexp = '^%s/admin/api/locations/%s/$' \
          % (site_url(), uid_regexp())
      self.assertRegexpMatches(parsed_response_body['self'], self_url_regexp)
      self.assertRegexpMatches(response['Location'], self_url_regexp)
      self.assertRegexpMatches(response['Content-Location'], self_url_regexp)

   def test_get_location(self):
      post_response = self.post('/admin/api/locations/', {'path' : '/foo/bar'})
      self.assertEqual(201, post_response.status_code)
      parsed_post_response_body = json.loads(post_response.content)

      get_response = self.get(parsed_post_response_body['self'])
      self.assertEqual(200, get_response.status_code)
      parsed_get_response_body = json.loads(get_response.content)

      self.assertEqual(post_response.content, get_response.content)

   # def test_delete_location(self):
   #    response = self.post('/admin/api/locations/', {'path' : '/foo/bar'})
   #    self.assertEqual(201, response.status_code)

   #    parsed_response_body = json.loads(response.content)
   #    response = self.delete(parsed_response_body['self'])
   #    self.assertEqual(204, response.status_code)

   # def test_get_locations_list(self):
   #    self.assertEqual(201, self.post('/admin/api/locations/',
   #                                    {'path' : '/foo/bar'}).status_code)
   #    self.assertEqual(201, self.post('/admin/api/locations/',
   #                                    {'path' : 'baz@bar.org'}).status_code)
   #    self.assertEqual(201, self.post('/admin/api/locations/',
   #                                    {'path' : 'boo@bar.org'}).status_code)
   #    response = self.get('/admin/api/locations/')
   #    self.assertEqual(200, response.status_code)
   #    parsed_response_body = json.loads(response.content)
   #    self.assertRegexpMatches(parsed_response_body['self'],
   #                             '^%s/admin/api/locations/$' % site_url())

   #    locations = parsed_response_body['locations']
   #    self.assertEqual(3, len(locations))
   #    self.assertItemsEqual(['/foo/bar', 'baz@bar.org', 'boo@bar.org'],
   #                          [item['path'] for item in locations])

   # def test_get_not_existing_location(self):
   #    response = self.get(
   #       '/admin/api/locations/41be0192-0fcc-4a9c-935d-69243b75533c/')
   #    self.assertEqual(404, response.status_code)
   #    self.assertRegexpMatches(response.content, 'Location not found')

   # # TODO: make this a generic test for the RestView.
   # def test_add_location_invalid_arg_name(self):
   #    response = self.post('/admin/api/locations/', {'epath' : '/foo/bar'})
   #    self.assertEqual(400, response.status_code)
   #    self.assertRegexpMatches(response.content, 'Invalid request arguments')

   # def test_add_location_invalid_path(self):
   #    response = self.post('/admin/api/locations/', {'path' : 'foo.bar'})
   #    self.assertEqual(400, response.status_code)
   #    self.assertRegexpMatches(response.content, 'Invalid path format')

   # def test_add_existing_location(self):
   #    response = self.post('/admin/api/locations/', {'path' : '/foo/bar'})
   #    self.assertEqual(201, response.status_code)

   #    response = self.post('/admin/api/locations/', {'path' : '/foo/bar'})
   #    self.assertEqual(400, response.status_code)
   #    self.assertRegexpMatches(response.content, 'Location already exists')

   # def test_delete_location_twice(self):
   #    response = self.post('/admin/api/locations/', {'path' : '/foo/bar'})
   #    self.assertEqual(201, response.status_code)

   #    parsed_response_body = json.loads(response.content)
   #    response = self.delete(parsed_response_body['self'])
   #    self.assertEqual(204, response.status_code)

   #    response = self.delete(parsed_response_body['self'])
   #    self.assertEqual(404, response.status_code)
   #    self.assertRegexpMatches(response.content, 'Location not found')

