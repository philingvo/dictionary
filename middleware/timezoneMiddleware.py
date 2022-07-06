import pytz
from django.utils import timezone
from django.shortcuts import redirect, render
from dictionaries.models import User


class TimezoneMiddleware:
	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		tzname = request.session.get('django_timezone')
		if not tzname:
			tzname = User.get_user_timezone()
		if tzname:
			timezone.activate(pytz.timezone(tzname))
		else:
			timezone.deactivate()
		return self.get_response(request)