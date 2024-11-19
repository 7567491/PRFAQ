#!/usr/bin/env python3
"""
AWS Marketplace Integration Setup Script
This script automates the setup of required AWS resources for Marketplace integration.
"""

import boto3
import json
import time
from botocore.exceptions import ClientError
import logging
import sys
import os
from pathlib import Path
import streamlit as st
from modules.utils import add_log

class MarketplaceSetup:
    def __init__(self, region="cn-northwest-1", profile=None):
        """初始化AWS客户端"""
        try:
            self.session = boto3.Session(profile_name=profile, region_name=region)
            self.sqs = self.session.client('sqs')
            self.sns = self.session.client('sns')
            self.logger = self._setup_logger()
            add_log("info", f"AWS客户端初始化成功，区域: {region}")
        except Exception as e:
            add_log("error", f"AWS客户端初始化失败: {str(e)}")
            raise
        
    def _setup_logger(self):
        """配置日志"""
        logger = logging.getLogger('MarketplaceSetup')
        logger.setLevel(logging.INFO)
        
        # 创建日志目录
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # 文件处理器
        file_handler = logging.FileHandler('logs/aws_setup.log')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(file_handler)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(levelname)s: %(message)s'
        ))
        logger.addHandler(console_handler)
        
        return logger

    def create_sqs_queue(self, queue_name):
        """创建SQS队列"""
        try:
            add_log("info", f"开始创建SQS队列: {queue_name}")
            
            # 检查队列是否已存在
            existing_queues = self.sqs.list_queues(QueueNamePrefix=queue_name)
            if 'QueueUrls' in existing_queues:
                queue_url = existing_queues['QueueUrls'][0]
                add_log("info", f"队列已存在: {queue_url}")
                
                # 获取队列ARN
                queue_attrs = self.sqs.get_queue_attributes(
                    QueueUrl=queue_url,
                    AttributeNames=['QueueArn']
                )
                queue_arn = queue_attrs['Attributes']['QueueArn']
                return queue_url, queue_arn
            
            # 创建新队列
            response = self.sqs.create_queue(
                QueueName=queue_name,
                Attributes={
                    'VisibilityTimeout': '300',  # 5分钟
                    'MessageRetentionPeriod': '345600',  # 4天
                    'ReceiveMessageWaitTimeSeconds': '20',  # 长轮询
                    'DelaySeconds': '0',  # 无延迟
                    'MaximumMessageSize': '262144'  # 256KB
                }
            )
            queue_url = response['QueueUrl']
            add_log("info", f"SQS队列创建成功: {queue_url}")
            
            # 获取队列ARN
            queue_attrs = self.sqs.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=['QueueArn']
            )
            queue_arn = queue_attrs['Attributes']['QueueArn']
            
            return queue_url, queue_arn
            
        except ClientError as e:
            error_msg = f"创建SQS队列失败: {str(e)}"
            add_log("error", error_msg)
            raise

    def create_sns_topic(self, topic_name):
        """创建SNS主题"""
        try:
            add_log("info", f"开始创建SNS主题: {topic_name}")
            
            # 检查主题是否已存在
            topics = self.sns.list_topics()
            for topic in topics['Topics']:
                if topic_name in topic['TopicArn']:
                    add_log("info", f"主题已存在: {topic['TopicArn']}")
                    return topic['TopicArn']
            
            # 创建新主题
            response = self.sns.create_topic(Name=topic_name)
            topic_arn = response['TopicArn']
            add_log("info", f"SNS主题创建成功: {topic_arn}")
            return topic_arn
            
        except ClientError as e:
            error_msg = f"创建SNS主题失败: {str(e)}"
            add_log("error", error_msg)
            raise

    def setup_sqs_policy(self, queue_url, queue_arn, topic_arn):
        """设置SQS访问策略"""
        try:
            add_log("info", "开始设置SQS访问策略...")
            
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "AllowSNSPublish",
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "sns.amazonaws.com"
                        },
                        "Action": "sqs:SendMessage",
                        "Resource": queue_arn,
                        "Condition": {
                            "ArnEquals": {
                                "aws:SourceArn": topic_arn
                            }
                        }
                    }
                ]
            }
            
            self.sqs.set_queue_attributes(
                QueueUrl=queue_url,
                Attributes={
                    'Policy': json.dumps(policy)
                }
            )
            add_log("info", "SQS访问策略设置成功")
            
        except ClientError as e:
            error_msg = f"设置SQS策略失败: {str(e)}"
            add_log("error", error_msg)
            raise

    def subscribe_sqs_to_sns(self, topic_arn, queue_arn):
        """将SQS订阅到SNS"""
        try:
            add_log("info", "开始设置SNS订阅...")
            
            # 检查是否已订阅
            subscriptions = self.sns.list_subscriptions_by_topic(TopicArn=topic_arn)
            for sub in subscriptions['Subscriptions']:
                if sub['Endpoint'] == queue_arn:
                    add_log("info", f"订阅已存在: {sub['SubscriptionArn']}")
                    return sub['SubscriptionArn']
            
            # 创建新订阅
            response = self.sns.subscribe(
                TopicArn=topic_arn,
                Protocol='sqs',
                Endpoint=queue_arn
            )
            add_log("info", f"SNS订阅创建成功: {response['SubscriptionArn']}")
            return response['SubscriptionArn']
            
        except ClientError as e:
            error_msg = f"设置SNS订阅失败: {str(e)}"
            add_log("error", error_msg)
            raise

    def create_config_file(self, queue_url, topic_arn):
        """创建配置文件"""
        try:
            add_log("info", "开始创建配置文件...")
            
            config = {
                'AWS_SQS_QUEUE_URL': queue_url,
                'AWS_SNS_TOPIC_ARN': topic_arn
            }
            
            # 确保config目录存在
            config_dir = Path("config")
            config_dir.mkdir(exist_ok=True)
            
            config_path = config_dir / "aws_marketplace_config.json"
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
                
            add_log("info", f"配置文件创建成功: {config_path}")
            
            # 更新.env文件
            env_path = Path(".env")
            env_content = f"""
            # AWS Marketplace Configuration
            AWS_SQS_QUEUE_URL="{queue_url}"
            AWS_SNS_TOPIC_ARN="{topic_arn}"
            """
            
            with open(env_path, 'a') as f:
                f.write(env_content)
                
            add_log("info", "环境变量已更新")
            
        except IOError as e:
            error_msg = f"创建配置文件失败: {str(e)}"
            add_log("error", error_msg)
            raise

def show_setup_panel():
    """显示设置面板"""
    st.title("AWS Marketplace 资源设置")
    
    st.markdown("""
    此工具用于自动创建AWS Marketplace集成所需的资源：
    1. SQS队列 - 用于接收通知消息
    2. SNS主题 - 用于发布订阅更新
    3. 相关权限和订阅设置
    """)
    
    # 配置选项
    st.subheader("配置选项")
    col1, col2 = st.columns(2)
    
    with col1:
        region = st.selectbox(
            "选择区域",
            ["cn-northwest-1", "cn-north-1"],
            index=0
        )
        
    with col2:
        base_name = st.text_input(
            "资源名称前缀",
            value="marketplace-notifications",
            help="用于创建的SQS队列和SNS主题的名称前缀"
        )
    
    # 创建按钮
    if st.button("创建资源", key="create_resources"):
        try:
            with st.spinner("正在创建AWS资源..."):
                # 显示进度
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # 初始化设置工具
                status_text.text("正在初始化AWS客户端...")
                setup = MarketplaceSetup(region=region)
                progress_bar.progress(20)
                
                # 创建SQS队列
                status_text.text("正在创建SQS队列...")
                queue_url, queue_arn = setup.create_sqs_queue(base_name)
                progress_bar.progress(40)
                
                # 创建SNS主题
                status_text.text("正在创建SNS主题...")
                topic_arn = setup.create_sns_topic(base_name)
                progress_bar.progress(60)
                
                # 设置权限
                status_text.text("正在设置访问权限...")
                setup.setup_sqs_policy(queue_url, queue_arn, topic_arn)
                progress_bar.progress(80)
                
                # 创建订阅
                status_text.text("正在设置SNS订阅...")
                setup.subscribe_sqs_to_sns(topic_arn, queue_arn)
                
                # 创建配置文件
                status_text.text("正在创建配置文件...")
                setup.create_config_file(queue_url, topic_arn)
                progress_bar.progress(100)
                
                # 显示结果
                st.success("AWS资源创建成功!")
                
                st.subheader("创建的资源")
                st.json({
                    "SQS队列URL": queue_url,
                    "SNS主题ARN": topic_arn,
                    "配置文件": "config/aws_marketplace_config.json"
                })
                
                # 显示后续步骤
                st.subheader("后续步骤")
                st.markdown("""
                1. 配置已自动添加到 .env 文件
                2. 配置已保存到 config/aws_marketplace_config.json
                3. 可以开始使用通知处理功能
                """)
                
        except Exception as e:
            st.error(f"创建资源失败: {str(e)}")
            add_log("error", f"资源创建失败: {str(e)}")

if __name__ == "__main__":
    show_setup_panel()