from rest_framework.viewsets import ViewSet
from django.db.models import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework import status
from backend.serializers.notification_group_serializer import NotificationGroupModelSerializer, \
    NotificationGroupModelDetailSerializer
from backend.usecases.control_notification import ControlNotificationUseCase
from backend.models import TenantModel, NotificationGroupModel
from backend.logger import NarukoLogging
from django.db import transaction


class NotificationGroupViewSet(ViewSet):

    def list(self, request, tenant_pk=None):
        log = NarukoLogging(request)
        logger = log.get_logger(__name__)
        logger.info("START: list")
        try:
            tenant = TenantModel.objects.get(id=tenant_pk)
            groups = ControlNotificationUseCase(log).fetch_groups(request.user, tenant)
            data = [NotificationGroupModelDetailSerializer(group).data for group in groups]
        except (TypeError, ValueError, ObjectDoesNotExist) as e:
            logger.exception(e)
            return Response(status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(e)
            raise
        else:
            logger.info("END: list")
            return Response(data=data, status=status.HTTP_200_OK)

    @transaction.atomic
    def create(self, request, tenant_pk=None):
        log = NarukoLogging(request)
        logger = log.get_logger(__name__)
        logger.info("START: create")
        try:
            with transaction.atomic():
                # バリデーション
                data_group = request.data
                data_group["tenant"] = tenant_pk
                serializer = NotificationGroupModelSerializer(data=data_group)
                serializer.is_valid(raise_exception=True)

                data = ControlNotificationUseCase(log).save_group(request.user, serializer.save())
        except (TypeError, ValueError, ObjectDoesNotExist) as e:
            logger.exception(e)
            return Response(status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(e)
            raise
        else:
            logger.info("END: create")
            return Response(data=NotificationGroupModelSerializer(data).data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def destroy(self, request, tenant_pk=None, pk=None):
        log = NarukoLogging(request)
        logger = log.get_logger(__name__)
        logger.info("START: destroy")
        try:
            with transaction.atomic():
                notification_group = NotificationGroupModel.objects.get(id=pk, tenant_id=tenant_pk)
                ControlNotificationUseCase(log).delete_group(request.user, notification_group)
        except (TypeError, ValueError, ObjectDoesNotExist) as e:
            logger.exception(e)
            return Response(status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(e)
            raise
        else:
            logger.info("END: destroy")
            return Response(status=status.HTTP_204_NO_CONTENT)

    @transaction.atomic
    def update(self, request, tenant_pk=None, pk=None):
        log = NarukoLogging(request)
        logger = log.get_logger(__name__)
        logger.info("START: update")
        try:
            with transaction.atomic():
                # バリデーション
                notification_group_model = NotificationGroupModel.objects.get(id=pk, tenant_id=tenant_pk)
                serializer = NotificationGroupModelSerializer(
                    instance=notification_group_model,
                    data=request.data,
                    partial=True)
                serializer.is_valid(raise_exception=True)

                data = ControlNotificationUseCase(log).save_group(request.user, serializer.save())
        except (TypeError, ValueError, ObjectDoesNotExist) as e:
            logger.exception(e)
            return Response(status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(e)
            raise
        else:
            logger.info("END: update")
            return Response(data=NotificationGroupModelSerializer(data).data, status=status.HTTP_200_OK)
