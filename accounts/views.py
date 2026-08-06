from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import Permission
from django.forms import ModelForm, CheckboxSelectMultiple, ModelMultipleChoiceField
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from accounts.models import Role, User
from accounts.permissions import require_admin
from core.modal import modal_form, modal_success


class UserForm(ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'tag', 'roles', 'is_active']
        widgets = {'roles': CheckboxSelectMultiple}


class RoleForm(ModelForm):
    permissions = ModelMultipleChoiceField(
        queryset=Permission.objects.select_related('content_type').order_by('content_type__app_label', 'codename'),
        widget=CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = Role
        fields = ['name', 'description', 'is_admin', 'permissions']


class StaffUserCreateForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'tag')


@require_http_methods(['GET', 'POST'])
def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    form = AuthenticationForm(request, data=request.POST or None)
    for field in form.fields.values():
        field.widget.attrs.setdefault('class', 'form-control')
    if request.method == 'POST' and form.is_valid():
        auth_login(request, form.get_user())
        return redirect(request.GET.get('next') or 'core:dashboard')
    return render(request, 'accounts/login.html', {'form': form})


@require_POST
def logout_view(request):
    auth_logout(request)
    return redirect('accounts:login')


@require_admin
def user_list(request):
    return render(request, 'accounts/user_list.html', {'users': User.objects.prefetch_related('roles').all()})


@require_admin
@require_http_methods(['GET', 'POST'])
def user_create(request):
    form = StaffUserCreateForm(request.POST or None)
    for field in form.fields.values():
        field.widget.attrs.setdefault('class', 'form-control')
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        roles = request.POST.getlist('roles')
        if roles:
            user.roles.set(roles)
        tag = request.POST.get('tag', '')
        if tag:
            user.tag = tag
            user.save(update_fields=['tag'])
        messages.success(request, 'Usuario creado.')
        return modal_success(request, reverse('accounts:user_list'))
    return modal_form(
        request,
        title='Crear usuario',
        form=form,
        action_url=reverse('accounts:user_create'),
        extra={
            'cancel_url': reverse('accounts:user_list'),
            'roles': Role.objects.all(),
            'form_body_template': 'accounts/user_create_body.html',
        },
    )


@require_admin
@require_http_methods(['GET', 'POST'])
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    form = UserForm(request.POST or None, instance=user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        new_password = request.POST.get('new_password', '').strip()
        if new_password:
            user.set_password(new_password)
            user.save(update_fields=['password'])
            messages.success(request, 'Usuario y contraseña actualizados.')
        else:
            messages.success(request, 'Usuario actualizado.')
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'Editar usuario', 'edit_user': user})


@require_admin
@require_POST
def user_toggle(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, 'No puedes desactivarte a ti mismo.')
    else:
        user.is_active = not user.is_active
        user.save(update_fields=['is_active'])
        messages.success(request, 'Estado de usuario actualizado.')
    return redirect('accounts:user_list')


@require_admin
def role_list(request):
    return render(request, 'accounts/role_list.html', {'roles': Role.objects.prefetch_related('permissions').all()})


@require_admin
@require_http_methods(['GET', 'POST'])
def role_create(request):
    form = RoleForm(request.POST or None)
    for name, field in form.fields.items():
        if name != 'permissions' and hasattr(field.widget, 'attrs'):
            field.widget.attrs.setdefault('class', 'form-control')
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Rol creado.')
        return modal_success(request, reverse('accounts:role_list'))
    return modal_form(
        request,
        title='Crear rol',
        form=form,
        action_url=reverse('accounts:role_create'),
        extra={'cancel_url': reverse('accounts:role_list')},
    )


@require_admin
@require_http_methods(['GET', 'POST'])
def role_edit(request, pk):
    role = get_object_or_404(Role, pk=pk)
    form = RoleForm(request.POST or None, instance=role)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Rol actualizado.')
        return redirect('accounts:role_list')
    return render(request, 'accounts/role_form.html', {'form': form, 'title': 'Editar rol'})


@require_admin
@require_POST
def role_delete(request, pk):
    role = get_object_or_404(Role, pk=pk)
    if role.name == 'admin':
        messages.error(request, 'No se puede eliminar el rol admin.')
    else:
        role.delete()
        messages.success(request, 'Rol eliminado.')
    return redirect('accounts:role_list')
