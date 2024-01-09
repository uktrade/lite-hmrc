from core import celery_tasks
from rest_framework.test import APITestCase

class FlagsUpdateTest(APITestCase):
    def test_debug_add(self):
        res = celery_tasks.debug_add(1, 2)
        assert res == 3

    def test_debug_exception(self):
        self.assertRaises(Exception, celery_tasks.debug_exception)