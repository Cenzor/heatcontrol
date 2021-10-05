from rest_framework.permissions import BasePermission
from django.http.response import HttpResponseForbidden
from django.core.exceptions import PermissionDenied


class SystemAdminPermission(BasePermission):
    def has_permission(self, request, view):
        if not bool(request.user and request.user.is_authenticated):
            return False
        permissions = request.user.get_permissions()
        return permissions and permissions.status_admin_system


class CompanyAdminPermission(BasePermission):
    def has_permission(self, request, view):
        if not bool(request.user and request.user.is_authenticated):
            return False
        if request.method == 'GET':
            # на просмотр пусть будет все доступно
            return True
        permissions = request.user.get_permissions()
        return permissions and (permissions.status_admin_company or permissions.status_admin_system)


class CompanyObjectAdminPermission(BasePermission):
    def has_permission(self, request, view):
        if not bool(request.user and request.user.is_authenticated):
            return False
        if request.method == 'GET':
            # на просмотр пусть будет все доступно
            return True
        permissions = request.user.get_permissions()
        return permissions and (permissions.status_admin_company_object or permissions.status_admin_company or permissions.status_admin_system)


class ModemAdminPermission(BasePermission):
    def has_permission(self, request, view):
        if not bool(request.user and request.user.is_authenticated):
            return False
        if request.method == 'GET':
            # на просмотр пусть будет все доступно
            return True
        permissions = request.user.get_permissions()
        return permissions and (permissions.status_admin_modem or permissions.status_admin_company or permissions.status_admin_system)


class DeviceAdminPermission(BasePermission):
    def has_permission(self, request, view):
        if not bool(request.user and request.user.is_authenticated):
            return False
        if request.method == 'GET':
            # на просмотр пусть будет все доступно
            return True
        permissions = request.user.get_permissions()
        return permissions and (permissions.status_admin_device or permissions.status_admin_company or permissions.status_admin_system)


def check_user_permission(request_user, user, read_access = False):
    #свойства произвольного пользователя может просматривать либо системный админ - свойства любого пользователя, либо админ компании - свойства любого из работников компании. Остальные пользователи могут только просматривать, редактировать и удалять себя
    permissions = request_user.get_permissions()
    if not permissions:
        if not user.id == request_user.id:
            raise PermissionDenied("unsufficient permissions")
    elif not permissions.status_admin_system:
        if permissions.status_admin_company and read_access:
            if request_user.employer and user.employer and not request_user.employer.id == user.employer.id:
                raise PermissionDenied("unsufficient permissions")
        elif not user.id == request_user.id:
            raise PermissionDenied("unsufficient permissions")


def check_company_permission(request_user, company, read_access = False):
    #изменить или удалить компанию может только админ этой компании
    permissions = request_user.get_permissions()
    if not permissions:
        raise PermissionDenied("unsufficient permissions")
    elif not permissions.status_admin_system:
        if permissions.status_admin_company and request_user.employer or read_access:
            if not request_user.employer.id == company.id:
                raise PermissionDenied("unsufficient permissions")
        else:
            raise PermissionDenied("unsufficient permissions")


def check_company_object_permission(request_user, company, read_access = False):
    permissions = request_user.get_permissions()
    if not permissions:
        raise PermissionDenied("unsufficient permissions")
    elif not permissions.status_admin_system:
        if permissions.status_admin_company and request_user.employer or read_access:
            if not request_user.employer.id == company.id:
                raise PermissionDenied("unsufficient permissions")
        elif permissions.status_admin_company_object and request_user.employer:
            if not request_user.employer.id == company.id:
                raise PermissionDenied("unsufficient permissions")
        else:
            raise PermissionDenied("unsufficient permissions")
        
        
def check_device_permission(request_user, company, read_access = False):
    permissions = request_user.get_permissions()
    if not permissions:
        raise PermissionDenied("unsufficient permissions")
    elif not permissions.status_admin_system:
        if permissions.status_admin_company and request_user.employer or read_access:
            if not request_user.employer.id == company.id:
                raise PermissionDenied("unsufficient permissions")
        elif permissions.status_admin_device and request_user.employer:
            if not request_user.employer.id == company.id:
                raise PermissionDenied("unsufficient permissions")
        else:
            raise PermissionDenied("unsufficient permissions")


def check_modem_permission(request_user, company, read_access = False):
    permissions = request_user.get_permissions()
    if not permissions:
        raise PermissionDenied("unsufficient permissions")
    elif not permissions.status_admin_system:
        if permissions.status_admin_company and request_user.employer or read_access:
            if not request_user.employer.id == company.id:
                raise PermissionDenied("unsufficient permissions")
        elif permissions.status_admin_modem and request_user.employer:
            if not request_user.employer.id == company.id:
                raise PermissionDenied("unsufficient permissions")
        else:
            raise PermissionDenied("unsufficient permissions")
