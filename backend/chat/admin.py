from django.contrib import admin

from .models import Membership, Message, Room

admin.site.register(Room)
admin.site.register(Membership)
admin.site.register(Message)
