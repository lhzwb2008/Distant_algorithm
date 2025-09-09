#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的Web界面用于TikTok创作者评分测试
"""

from flask import Flask, render_template, request, jsonify
import logging
import argparse
import threading
import uuid
import time
from datetime import datetime
from creator_score_calculator import CreatorScoreCalculator
from api_client import TiKhubAPIClient
from simple_score_api import SimpleScoreAPI

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 初始化评分计算器
calculator = CreatorScoreCalculator()

# 初始化简化API
simple_api = SimpleScoreAPI()

# 任务存储（实际项目中应该使用Redis等持久化存储）
tasks = {}

def background_calculate_score(task_id, username, keyword):
    """后台计算评分"""
    try:
        logger.info(f"任务 {task_id}: 开始计算用户 {username} 的评分，关键词: {keyword or '无'}")
        
        # 更新任务状态
        tasks[task_id]['status'] = 'processing'
        tasks[task_id]['progress'] = '正在获取用户信息...'
        
        # 获取secUid
        sec_uid = calculator.api_client.get_secuid_from_username(username)
        if not sec_uid:
            tasks[task_id]['status'] = 'failed'
            tasks[task_id]['error'] = f'无法找到用户 {username}，请检查用户名是否正确'
            return
        
        tasks[task_id]['progress'] = '正在分析视频内容...'
        
        # 计算评分
        creator_score, ai_quality_scores = calculator.calculate_creator_score_by_user_id_with_ai_scores(sec_uid, keyword=keyword if keyword else None)
        
        tasks[task_id]['progress'] = '正在生成详细报告...'
        
        # 获取详细的评分分解（包含AI质量评分）
        score_breakdown = calculator.get_score_breakdown(creator_score, ai_quality_scores)
        
        # 任务完成
        tasks[task_id]['status'] = 'completed'
        tasks[task_id]['result'] = {
            'success': True,
            'username': username,
            'keyword': keyword or '无',
            'score': round(creator_score.final_score, 2),
            'sec_uid': sec_uid,
            'breakdown': score_breakdown
        }
        tasks[task_id]['completed_at'] = datetime.now().isoformat()
        
        logger.info(f"任务 {task_id}: 计算完成，最终评分: {creator_score.final_score:.2f}")
        
    except Exception as e:
        logger.error(f"任务 {task_id}: 计算评分时发生错误: {e}")
        tasks[task_id]['status'] = 'failed'
        tasks[task_id]['error'] = f'计算评分时发生错误: {str(e)}'

@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')

@app.route('/submit_task', methods=['POST'])
def submit_task():
    """提交评分计算任务（异步）"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        keyword = data.get('keyword', '').strip()
        
        if not username:
            return jsonify({
                'success': False,
                'error': '请输入用户名'
            }), 400
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 创建任务记录
        tasks[task_id] = {
            'id': task_id,
            'status': 'pending',
            'username': username,
            'keyword': keyword or '无',
            'created_at': datetime.now().isoformat(),
            'progress': '任务已提交，等待处理...'
        }
        
        # 启动后台线程处理任务
        thread = threading.Thread(target=background_calculate_score, args=(task_id, username, keyword))
        thread.daemon = True
        thread.start()
        
        logger.info(f"任务 {task_id}: 已提交，用户: {username}，关键词: {keyword or '无'}")
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'status': 'pending',
            'message': '任务已提交，请使用task_id查询结果'
        })
        
    except Exception as e:
        logger.error(f"提交任务时发生错误: {e}")
        return jsonify({
            'success': False,
            'error': f'提交任务时发生错误: {str(e)}'
        }), 500

@app.route('/task_status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """查询任务状态"""
    if task_id not in tasks:
        return jsonify({
            'success': False,
            'error': '任务不存在'
        }), 404
    
    task = tasks[task_id]
    response = {
        'success': True,
        'task_id': task_id,
        'status': task['status'],
        'username': task['username'],
        'keyword': task['keyword'],
        'created_at': task['created_at'],
        'progress': task.get('progress', '')
    }
    
    if task['status'] == 'completed':
        response['result'] = task['result']
        response['completed_at'] = task.get('completed_at')
    elif task['status'] == 'failed':
        response['error'] = task.get('error')
    
    return jsonify(response)

@app.route('/tasks', methods=['GET'])
def list_tasks():
    """获取所有任务列表"""
    task_list = []
    for task_id, task in tasks.items():
        task_info = {
            'task_id': task_id,
            'status': task['status'],
            'username': task['username'],
            'keyword': task['keyword'],
            'created_at': task['created_at'],
            'progress': task.get('progress', '')
        }
        if task['status'] == 'completed':
            task_info['completed_at'] = task.get('completed_at')
            task_info['score'] = task.get('result', {}).get('score')
        elif task['status'] == 'failed':
            task_info['error'] = task.get('error')
        task_list.append(task_info)
    
    # 按创建时间倒序排列
    task_list.sort(key=lambda x: x['created_at'], reverse=True)
    
    return jsonify({
        'success': True,
        'tasks': task_list,
        'total': len(task_list)
    })

@app.route('/calculate_score', methods=['POST'])
def calculate_score():
    """计算评分API（保持向后兼容的同步接口）"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        keyword = data.get('keyword', '').strip()
        
        if not username:
            return jsonify({
                'success': False,
                'error': '请输入用户名'
            }), 400
        
        logger.info(f"开始计算用户 {username} 的评分，关键词: {keyword or '无'}")
        
        # 获取secUid
        sec_uid = calculator.api_client.get_secuid_from_username(username)
        if not sec_uid:
            return jsonify({
                'success': False,
                'error': f'无法找到用户 {username}，请检查用户名是否正确'
            }), 404
        
        # 计算评分
        creator_score, ai_quality_scores = calculator.calculate_creator_score_by_user_id_with_ai_scores(sec_uid, keyword=keyword if keyword else None)
        
        # 获取详细的评分分解（包含AI质量评分）
        score_breakdown = calculator.get_score_breakdown(creator_score, ai_quality_scores)
        
        return jsonify({
            'success': True,
            'username': username,
            'keyword': keyword or '无',
            'score': round(creator_score.final_score, 2),
            'sec_uid': sec_uid,
            'breakdown': score_breakdown
        })
        
    except Exception as e:
        logger.error(f"计算评分时发生错误: {e}")
        return jsonify({
            'success': False,
            'error': f'计算评分时发生错误: {str(e)}'
        }), 500

@app.route('/api/score', methods=['POST'])
def api_calculate_score():
    """简化的评分计算API（基于secUid）"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '请提供JSON格式的请求数据'
            }), 400
        
        sec_uid = data.get('sec_uid')
        if not sec_uid:
            return jsonify({
                'success': False,
                'error': '缺少必需参数: sec_uid'
            }), 400
        
        keyword = data.get('keyword')
        
        logger.info(f"简化API: 开始计算secUid {sec_uid[:20]}... 的评分，关键词: {keyword or '无'}")
        
        # 使用简化API计算评分
        result = simple_api.calculate_score_by_secuid(sec_uid, keyword)
        
        if result['success']:
            logger.info(f"简化API: 评分计算完成，总分: {result['scores']['total_score']}")
        else:
            logger.error(f"简化API: 评分计算失败: {result.get('error', '未知错误')}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"简化API调用时发生错误: {e}")
        return jsonify({
            'success': False,
            'error': f'API调用时发生错误: {str(e)}'
        }), 500

if __name__ == '__main__':
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='TikTok创作者评分系统 Web服务')
    parser.add_argument('--port', type=int, default=8080, help='Web服务端口 (默认: 8080)')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Web服务主机 (默认: 0.0.0.0)')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    args = parser.parse_args()
    
    print("\n🚀 TikTok创作者评分系统 Web界面")
    print(f"📱 访问地址: http://localhost:{args.port}")
    print(f"🌐 外部访问: http://{args.host}:{args.port}")
    print("💡 在浏览器中打开上述地址即可使用")
    
    print("\n📊 简化评分API已启动:")
    print(f"🔗 API端点: http://localhost:{args.port}/api/score")
    print("\n📋 默认curl调用示例:")
    print("curl -X POST http://localhost:{}/api/score \\".format(args.port))
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{')
    print('    "sec_uid": "MS4wLjABAAAAv7iSuuXDJGDvJkmH_vz1qkDZYo1apxgzaxdBSeIuPiM",')
    print('    "keyword": "crypto"')
    print('  }\'')
    print("\n💡 使用说明:")
    print("  - 必需参数: sec_uid (TikTok用户的secUid)")
    print("  - 可选参数: keyword (关键词筛选)")
    print("  - 只需修改sec_uid参数即可测试其他用户")
    
    print("\n按 Ctrl+C 停止服务\n")
    
    # 配置 Flask 应用的超时设置
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    
    # 运行应用
    app.run(
        debug=args.debug, 
        host=args.host, 
        port=args.port,
        threaded=True  # 启用多线程处理
    )