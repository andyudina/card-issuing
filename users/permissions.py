from rest_framework import permissions


class IsAccountOwner(permissions.BasePermission):
    '''
    Account permission to only allow owner ow account to see it state
    '''

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


