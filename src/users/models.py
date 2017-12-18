from django.db import models
from django.contrib.auth import models as auth_models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserInfo(models.Model):
    user = models.OneToOneField(auth_models.User, related_name='info')

    open_locality = models.PositiveIntegerField(
        help_text='На сколько клеток открывается область вокруг решённой задачи',
        default=1
    )

    ejudge_user_id = models.PositiveIntegerField(
        help_text='Идентификатор пользователя в еджадже',
        default=0,
        blank=True,
    )


@receiver(post_save, sender=auth_models.User)
def create_user_profile(sender, instance, created, **kwargs):
    if 'raw' in kwargs and kwargs['raw']:
        return
    if created:
        UserInfo.objects.create(user=instance)


@receiver(post_save, sender=auth_models.User)
def save_user_profile(sender, instance, **kwargs):
    if 'raw' in kwargs and kwargs['raw']:
        return
    instance.info.save()
