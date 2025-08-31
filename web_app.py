#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的Web界面用于TikTok创作者评分测试
"""

from flask import Flask, render_template, request, jsonify
import logging
import argparse
from creator_score_calculator import CreatorScoreCalculator
from api_client import TiKhubAPIClient

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 初始化评分计算器
calculator = CreatorScoreCalculator()

@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')

@app.route('/calculate_score', methods=['POST'])
def calculate_score():
    """计算评分API"""
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
        creator_score = calculator.calculate_creator_score_by_user_id(sec_uid, keyword=keyword if keyword else None)
        
        # 获取详细的评分分解
        score_breakdown = calculator.get_score_breakdown(creator_score)
        
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
    print("\n按 Ctrl+C 停止服务\n")
    
    app.run(debug=args.debug, host=args.host, port=args.port)