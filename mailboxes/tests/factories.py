import factory

from mailboxes.models import MailboxConfig, MailReadStatus


class MailboxConfigFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MailboxConfig

    username = factory.Faker("email")


class MailReadStatusFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MailReadStatus
