"""TikHub API客户端单元测试"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_client import TikHubAPIClient
from models import UserProfile, VideoDetail

class TestTikHubAPIClient(unittest.TestCase):
    """TikHub API客户端测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.api_key = "test_api_key"
        self.client = TikHubAPIClient(self.api_key)
        
        # 模拟用户档案响应数据
        self.mock_user_profile_response = {
            "code": 0,
            "message": "success",
            "data": {
                "user": {
                    "uniqueId": "test_user",
                    "nickname": "Test User",
                    "followerCount": 50000,
                    "heartCount": 1000000,
                    "videoCount": 100,
                    "verified": True
                }
            }
        }
        
        # 模拟视频指标响应数据
        self.mock_video_metrics_response = {
            "code": 0,
            "message": "success",
            "data": {
                "metrics": {
                    "playCount": 100000,
                    "diggCount": 5000,
                    "commentCount": 500,
                    "collectCount": 200
                }
            }
        }
        
        # 模拟视频详情响应数据
        self.mock_video_detail_response = {
            "code": 0,
            "message": "success",
            "data": {
                "aweme_detail": {
                    "aweme_id": "video123",
                    "statistics": {
                        "play_count": 100000,
                        "digg_count": 5000,
                        "comment_count": 500,
                        "share_count": 200,
                        "download_count": 50
                    }
                }
            }
        }
    
    def test_init(self):
        """测试客户端初始化"""
        self.assertEqual(self.client.api_key, self.api_key)
        self.assertEqual(self.client.base_url, "https://api.tikhub.io")
        self.assertIsNotNone(self.client.session)
        
        # 验证请求头设置
        self.assertEqual(
            self.client.session.headers["Authorization"], 
            f"Bearer {self.api_key}"
        )
        self.assertEqual(
            self.client.session.headers["Content-Type"], 
            "application/json"
        )
    
    @patch('requests.Session.get')
    def test_get_user_profile_success(self, mock_get):
        """测试成功获取用户档案"""
        # 设置模拟响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_user_profile_response
        mock_get.return_value = mock_response
        
        # 调用方法
        user_profile = self.client.get_user_profile("test_user")
        
        # 验证结果
        self.assertIsInstance(user_profile, UserProfile)
        self.assertEqual(user_profile.username, "test_user")
        self.assertEqual(user_profile.follower_count, 50000)
        self.assertEqual(user_profile.total_likes, 1000000)
        self.assertEqual(user_profile.video_count, 100)
        
        # 验证API调用
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertIn("/api/v1/tiktok/web/fetch_user_profile", call_args[0][0])
        self.assertIn("uniqueId=test_user", call_args[1]["params"]["uniqueId"])
    
    @patch('requests.Session.get')
    def test_get_user_profile_api_error(self, mock_get):
        """测试API错误响应"""
        # 设置模拟错误响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 1001,
            "message": "User not found",
            "data": None
        }
        mock_get.return_value = mock_response
        
        # 调用方法并验证异常
        with self.assertRaises(Exception) as context:
            self.client.get_user_profile("nonexistent_user")
        
        self.assertIn("User not found", str(context.exception))
    
    @patch('requests.Session.get')
    def test_get_user_profile_http_error(self, mock_get):
        """测试HTTP错误"""
        # 设置模拟HTTP错误
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("HTTP 404")
        mock_get.return_value = mock_response
        
        # 调用方法并验证异常
        with self.assertRaises(Exception) as context:
            self.client.get_user_profile("test_user")
        
        self.assertIn("HTTP 404", str(context.exception))
    
    @patch('requests.Session.get')
    def test_get_video_metrics_success(self, mock_get):
        """测试成功获取视频指标"""
        # 设置模拟响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_video_metrics_response
        mock_get.return_value = mock_response
        
        # 调用方法
        metrics = self.client.get_video_metrics("video123")
        
        # 验证结果
        self.assertIsInstance(metrics, dict)
        self.assertEqual(metrics["playCount"], 100000)
        self.assertEqual(metrics["diggCount"], 5000)
        self.assertEqual(metrics["commentCount"], 500)
        self.assertEqual(metrics["collectCount"], 200)
        
        # 验证API调用
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertIn("/api/v1/tiktok/analytics/fetch_video_metrics", call_args[0][0])
    
    @patch('requests.Session.get')
    def test_get_video_detail_success(self, mock_get):
        """测试成功获取视频详情"""
        # 设置模拟响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_video_detail_response
        mock_get.return_value = mock_response
        
        # 调用方法
        video_detail = self.client.get_video_detail("video123")
        
        # 验证结果
        self.assertIsInstance(video_detail, VideoDetail)
        self.assertEqual(video_detail.video_id, "video123")
        self.assertEqual(video_detail.view_count, 100000)
        self.assertEqual(video_detail.like_count, 5000)
        self.assertEqual(video_detail.comment_count, 500)
        self.assertEqual(video_detail.share_count, 200)
        
        # 验证API调用
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertIn("/api/v1/tiktok/app/v3/fetch_one_video", call_args[0][0])
    
    @patch('requests.Session.get')
    def test_get_batch_video_details_success(self, mock_get):
        """测试批量获取视频详情"""
        # 设置模拟响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_video_detail_response
        mock_get.return_value = mock_response
        
        # 调用方法
        video_ids = ["video1", "video2", "video3"]
        video_details = self.client.get_batch_video_details(video_ids)
        
        # 验证结果
        self.assertEqual(len(video_details), 3)
        for detail in video_details:
            self.assertIsInstance(detail, VideoDetail)
        
        # 验证API调用次数
        self.assertEqual(mock_get.call_count, 3)
    
    @patch('requests.Session.get')
    def test_get_batch_video_details_with_errors(self, mock_get):
        """测试批量获取视频详情时的错误处理"""
        # 设置模拟响应：第一个成功，第二个失败，第三个成功
        responses = [
            Mock(status_code=200, json=lambda: self.mock_video_detail_response),
            Mock(status_code=404, raise_for_status=Mock(side_effect=Exception("Not found"))),
            Mock(status_code=200, json=lambda: self.mock_video_detail_response)
        ]
        mock_get.side_effect = responses
        
        # 调用方法
        video_ids = ["video1", "video2", "video3"]
        video_details = self.client.get_batch_video_details(video_ids)
        
        # 验证结果：应该只返回成功的两个
        self.assertEqual(len(video_details), 2)
        
        # 验证API调用次数
        self.assertEqual(mock_get.call_count, 3)
    
    def test_parse_user_profile_data(self):
        """测试用户档案数据解析"""
        user_data = self.mock_user_profile_response["data"]["user"]
        user_profile = self.client._parse_user_profile_data(user_data)
        
        self.assertIsInstance(user_profile, UserProfile)
        self.assertEqual(user_profile.username, "test_user")
        self.assertEqual(user_profile.follower_count, 50000)
        self.assertEqual(user_profile.total_likes, 1000000)
        self.assertEqual(user_profile.video_count, 100)
    
    def test_parse_video_detail_data(self):
        """测试视频详情数据解析"""
        video_data = self.mock_video_detail_response["data"]["aweme_detail"]
        video_detail = self.client._parse_video_detail_data(video_data)
        
        self.assertIsInstance(video_detail, VideoDetail)
        self.assertEqual(video_detail.video_id, "video123")
        self.assertEqual(video_detail.view_count, 100000)
        self.assertEqual(video_detail.like_count, 5000)
        self.assertEqual(video_detail.comment_count, 500)
        self.assertEqual(video_detail.share_count, 200)
    
    def test_make_request_with_retry(self):
        """测试请求重试机制"""
        with patch.object(self.client.session, 'get') as mock_get:
            # 设置前两次失败，第三次成功
            mock_get.side_effect = [
                Exception("Connection error"),
                Exception("Timeout"),
                Mock(status_code=200, json=lambda: {"code": 0, "data": {}})
            ]
            
            # 调用方法
            response = self.client._make_request_with_retry(
                "GET", "/test", 
                max_retries=3, 
                retry_delay=0.1
            )
            
            # 验证重试次数
            self.assertEqual(mock_get.call_count, 3)
            self.assertEqual(response.status_code, 200)
    
    def test_make_request_max_retries_exceeded(self):
        """测试超过最大重试次数"""
        with patch.object(self.client.session, 'get') as mock_get:
            # 设置所有请求都失败
            mock_get.side_effect = Exception("Connection error")
            
            # 调用方法并验证异常
            with self.assertRaises(Exception) as context:
                self.client._make_request_with_retry(
                    "GET", 
                    "/test", 
                    max_retries=2, 
                    retry_delay=0.1
                )
            
            # 验证重试次数
            self.assertEqual(mock_get.call_count, 3)  # 初始请求 + 2次重试
            self.assertIn("Connection error", str(context.exception))
    
    def test_rate_limiting(self):
        """测试速率限制"""
        import time
        
        with patch.object(self.client.session, 'get') as mock_get:
            mock_response = Mock(status_code=200, json=lambda: {"code": 0, "data": {}})
            mock_get.return_value = mock_response
            
            # 记录开始时间
            start_time = time.time()
            
            # 连续发送多个请求
            for _ in range(3):
                self.client._make_request_with_retry("GET", "/test")
            
            # 验证总时间（应该包含速率限制延迟）
            total_time = time.time() - start_time
            expected_min_time = 2 * self.client.rate_limit_delay  # 2个间隔
            
            # 由于测试环境的时间精度问题，使用较宽松的验证
            self.assertGreater(total_time, expected_min_time * 0.8)
    
    def test_error_handling_invalid_json(self):
        """测试无效JSON响应的错误处理"""
        with patch.object(self.client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            mock_get.return_value = mock_response
            
            # 调用方法并验证异常
            with self.assertRaises(Exception) as context:
                self.client.get_user_profile("test_user")
            
            self.assertIn("JSON", str(context.exception))
    
    def test_custom_headers(self):
        """测试自定义请求头"""
        custom_client = TikHubAPIClient(
            self.api_key, 
            custom_headers={"X-Custom-Header": "test_value"}
        )
        
        # 验证自定义头部被添加
        self.assertEqual(
            custom_client.session.headers["X-Custom-Header"], 
            "test_value"
        )
        
        # 验证默认头部仍然存在
        self.assertEqual(
            custom_client.session.headers["Authorization"], 
            f"Bearer {self.api_key}"
        )
    
    def test_timeout_configuration(self):
        """测试超时配置"""
        custom_timeout = 30
        custom_client = TikHubAPIClient(self.api_key, timeout=custom_timeout)
        
        self.assertEqual(custom_client.timeout, custom_timeout)
        
        with patch.object(custom_client.session, 'get') as mock_get:
            mock_get.return_value = Mock(
                status_code=200, 
                json=lambda: {"code": 0, "data": {}}
            )
            
            custom_client._make_request_with_retry("GET", "/test")
            
            # 验证超时参数被传递
            mock_get.assert_called_with(
                f"{custom_client.base_url}/test",
                timeout=custom_timeout,
                params=None
            )

if __name__ == '__main__':
    unittest.main()