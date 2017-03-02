'''Permissions for user accounts'''

from rest_framework import permissions


class IsAccountOwner(permissions.BasePermission):

    '''
    Account permissions.
    Allow only owner of account to see its state
    '''

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
