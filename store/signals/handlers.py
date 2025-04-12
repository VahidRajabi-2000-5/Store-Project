from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.conf import settings
from django.utils.text import slugify

from .. import models


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_customer_profile_for_newly_created_user(sender, instance, created, **kwargs):
    if created:
        models.Customer.objects.create(user=instance)


@receiver(pre_save, sender=models.Product)
def generate_slug_product(sender, instance: models.Product, **kwargs):
        base_slug = slugify(instance.name)
        unique_slug = base_slug
        counter = 1

        while models.Product.objects.filter(slug=unique_slug).exists():
            unique_slug = f"{base_slug}-{counter}"
            counter += 1
        instance.slug = unique_slug
