from wwwhisper_auth.tests import HttpTestCase

import wwwhisper_service.urls

class LocationTest(HttpTestCase):

   def test_add_location(self):
      response = self.json_put('/admin/api/location/', {'path' : '/foo/bar'})
      self.assertEqual(200, response.status_code)
      self.assertEqual('/foo/bar', response.content)

   def test_add_location_invalid_arg_name(self):
      response = self.json_put('/admin/api/location/', {'prath' : '/foo/bar'})
      self.assertEqual(400, response.status_code)
      self.assertRegexpMatches(response.content, 'Invalid request arguments')

   def test_add_location_invalid_path(self):
      response = self.json_put('/admin/api/location/', {'path' : '/foo/../bar'})
      self.assertEqual(400, response.status_code)
      self.assertRegexpMatches(response.content, 'Invalid path')

   def test_add_existing_location(self):
      response = self.json_put('/admin/api/location/', {'path' : '/foo/bar'})
      self.assertEqual(200, response.status_code)
      response = self.json_put('/admin/api/location/', {'path' : '/foo/bar'})
      self.assertEqual(400, response.status_code)
      self.assertRegexpMatches(response.content, 'Location already exists')

   def test_delete_location(self):
      response = self.json_put('/admin/api/location/', {'path' : '/foo/bar'})
      self.assertEqual(200, response.status_code)
      response = self.json_delete('/admin/api/location/', {'path' : '/foo/bar'})
      self.assertEqual(200, response.status_code)

