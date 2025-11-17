"""
Flask API服务 - 为OA系统前端提供RAG问答接口
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from rag_system.api.qa_api import QAService
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 初始化RAG服务
qa_service = None

def init_qa_service():
    """初始化问答服务"""
    global qa_service
    try:
        qa_service = QAService()
        if qa_service.is_ready():
            logger.info("RAG服务初始化成功，索引已加载")
            return True
        else:
            logger.warning("RAG服务初始化，但索引未准备好")
            return False
    except ValueError as e:
        logger.error(f"RAG服务初始化失败: {e}")
        print("\n" + "=" * 60)
        print("❌ 索引未初始化！")
        print("=" * 60)
        print(str(e))
        print("=" * 60)
        return False
    except Exception as e:
        logger.error(f"RAG服务初始化失败: {e}")
        print(f"\n错误: {e}")
        return False

@app.route('/', methods=['GET'])
def index():
    """API首页"""
    html = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>财务助手 RAG API 服务</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            .container {
                background: white;
                border-radius: 16px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                max-width: 800px;
                width: 100%;
                padding: 40px;
            }
            h1 {
                color: #2563eb;
                margin-bottom: 10px;
                font-size: 2em;
            }
            .subtitle {
                color: #6b7280;
                margin-bottom: 30px;
            }
            .status {
                display: inline-block;
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 14px;
                font-weight: 500;
                margin-bottom: 30px;
            }
            .status.ok {
                background: #d1fae5;
                color: #065f46;
            }
            .status.error {
                background: #fee2e2;
                color: #991b1b;
            }
            .endpoint {
                background: #f9fafb;
                border-left: 4px solid #2563eb;
                padding: 20px;
                margin: 20px 0;
                border-radius: 8px;
            }
            .endpoint h3 {
                color: #1f2937;
                margin-bottom: 10px;
            }
            .endpoint code {
                background: #e5e7eb;
                padding: 2px 6px;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
            }
            .method {
                display: inline-block;
                background: #2563eb;
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                margin-right: 8px;
            }
            .method.get { background: #10b981; }
            .method.post { background: #2563eb; }
            pre {
                background: #1f2937;
                color: #f9fafb;
                padding: 15px;
                border-radius: 8px;
                overflow-x: auto;
                margin-top: 10px;
                font-size: 13px;
            }
            .footer {
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #e5e7eb;
                color: #6b7280;
                font-size: 14px;
                text-align: center;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>💰 财务助手 RAG API 服务</h1>
            <p class="subtitle">基于 LlamaIndex + LangChain 的企业知识库检索问答系统</p>
            
            <div class="status {{ status_class }}">
                {{ status_text }}
            </div>
            
            <h2 style="color: #1f2937; margin: 30px 0 20px 0;">📡 API 接口</h2>
            
            <div class="endpoint">
                <h3>
                    <span class="method get">GET</span>
                    <code>/api/health</code>
                </h3>
                <p style="color: #6b7280; margin: 10px 0;">健康检查接口，检查服务状态</p>
                <pre>curl http://localhost:5000/api/health</pre>
            </div>
            
            <div class="endpoint">
                <h3>
                    <span class="method post">POST</span>
                    <code>/api/qa</code>
                </h3>
                <p style="color: #6b7280; margin: 10px 0;">问答接口，输入问题获取AI回答</p>
                <pre>curl -X POST http://localhost:5000/api/qa \\
  -H "Content-Type: application/json" \\
  -d '{"question": "差旅费报销的标准是什么？"}'</pre>
            </div>
            
            <div class="footer">
                <p>💡 提示：在浏览器中打开 <code>design/OA系统原型.html</code> 使用完整的问答界面</p>
                <p style="margin-top: 10px;">服务运行在: <code>http://localhost:5000</code></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # 检查服务状态
    service_ready = qa_service is not None
    status_class = "ok" if service_ready else "error"
    status_text = "✓ 服务运行正常" if service_ready else "⚠ RAG服务未初始化"
    
    return render_template_string(html, status_class=status_class, status_text=status_text)

@app.route('/api/health', methods=['GET'])
def health():
    """健康检查"""
    service_ready = qa_service is not None
    index_ready = False
    if service_ready:
        try:
            index_ready = qa_service.is_ready()
        except:
            pass
    
    return jsonify({
        'status': 'ok' if service_ready and index_ready else 'error',
        'service': 'RAG QA Service',
        'qa_service_ready': service_ready,
        'index_ready': index_ready,
        'message': '服务正常' if (service_ready and index_ready) else '索引未初始化，请先构建索引'
    })

@app.route('/api/qa', methods=['POST'])
def qa():
    """问答接口"""
    if qa_service is None:
        return jsonify({
            'success': False,
            'error': 'RAG服务未初始化',
            'message': '请先构建索引：python -m rag_system.main index'
        }), 503
    
    if not qa_service.is_ready():
        return jsonify({
            'success': False,
            'error': '索引未初始化',
            'message': '请先运行以下命令构建索引：\npython -m rag_system.main index\n或运行：python quick_start.py'
        }), 503
    
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({
                'success': False,
                'error': '问题不能为空'
            }), 400
        
        logger.info(f"收到问题: {question}")
        
        # 调用RAG服务
        result = qa_service.ask(question)
        
        # 格式化返回结果
        response = {
            'success': True,
            'question': question,
            'answer': result.get('answer', ''),
            'sources': []
        }
        
        # 格式化引用来源
        for source in result.get('sources', []):
            doc_name = source.get('document', '未知文档')
            excerpt = source.get('excerpt', '')
            response['sources'].append({
                'document': doc_name,
                'excerpt': excerpt,
                'score': source.get('score')
            })
        
        logger.info(f"回答生成成功，包含 {len(response['sources'])} 个引用来源")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"处理问题时出错: {e}")
        return jsonify({
            'success': False,
            'error': f'处理问题时出错: {str(e)}'
        }), 500

@app.route('/api/qa/stream', methods=['POST'])
def qa_stream():
    """流式问答接口（可选，用于实时显示回答）"""
    # 这里可以实现流式响应，暂时返回普通响应
    return qa()

if __name__ == '__main__':
    # 初始化服务
    if init_qa_service():
        print("=" * 50)
        print("RAG API服务启动成功！")
        print("=" * 50)
        print("API地址: http://localhost:5000")
        print("健康检查: http://localhost:5000/api/health")
        print("问答接口: http://localhost:5000/api/qa")
        print("=" * 50)
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        print("=" * 50)
        print("RAG服务初始化失败！")
        print("请确保:")
        print("1. 已生成文档: python -m rag_system.main generate")
        print("2. 已构建索引: python -m rag_system.main index")
        print("=" * 50)

