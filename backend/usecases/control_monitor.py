from django.db.models.base import ObjectDoesNotExist
from django.core.exceptions import PermissionDenied
from backend.logger import NarukoLogging
from backend.models import AwsEnvironmentModel, UserModel, Resource
from backend.models.monitor import MonitorGraph
from backend.externals.cloudwatch import CloudWatch
from backend.externals.sns import Sns


class ControlMonitorUseCase:

    def __init__(self, naruko_logger: NarukoLogging):
        self.logger = naruko_logger.get_logger(__name__)

    def fetch_monitors(self, request_user: UserModel, aws: AwsEnvironmentModel, resource: Resource):
        self.logger.info("START: fetch_monitors")

        # 使用できるAWSアカウントか
        if not request_user.has_aws_env(aws):
            raise PermissionDenied("request user can't use aws account. user_id: {}, aws_id: {}"
                                   .format(request_user.id, aws.id))

        monitors = CloudWatch(aws, resource.region).describe_resource_monitors(resource)

        self.logger.info("END: fetch_monitors")
        return monitors

    def save_monitor(self, request_user: UserModel, resource: Resource, aws: AwsEnvironmentModel) -> Resource:
        self.logger.info("START: save_monitor")

        # 使用できるAWSアカウントか
        if not request_user.has_aws_env(aws):
            raise PermissionDenied("request user can't use aws account. user_id: {}, aws_id: {}"
                                   .format(request_user.id, aws.id))

        # SNS連携許可
        self.logger.info("sns add permission... aws: {}".format(aws.id))
        sns = Sns(resource.region)
        sns.add_permission(aws)
        self.logger.info("sns add permission... DONE")

        # アラーム作成
        self.logger.info("cloudwatch put metric alarms ...")
        CloudWatch(aws, resource.region).put_metric_alarms(resource, sns.arn)
        self.logger.info("cloudwatch put metric alarms ... DONE")

        self.logger.info("END: save_monitor")
        return resource

    def graph(self, request_user: UserModel, resource: Resource, aws: AwsEnvironmentModel, monitor_graph: MonitorGraph):
        self.logger.info("START: graph")

        # 使用できるAWSアカウントか
        if not request_user.has_aws_env(aws):
            raise PermissionDenied("request user can't use aws account. user_id: {}, aws_id: {}"
                                   .format(request_user.id, aws.id))

        if monitor_graph.metric_name not in resource.get_metrics():
            raise ObjectDoesNotExist("service doesn't have metric service_type: {} metric: {}"
                                     .format(resource.get_service_name(), monitor_graph.metric_name))

        monitor_graph = CloudWatch(aws, resource.region).get_chart(monitor_graph, resource)

        self.logger.info("END: graph")
        return monitor_graph
