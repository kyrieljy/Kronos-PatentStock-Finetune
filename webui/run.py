#!/usr/bin/env python3

import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
import sys
import subprocess
import webbrowser
import time
import socket
from pathlib import Path

def check_port_availability(host='localhost', port=7070):
    """检查端口是否可用"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((host, port))
        sock.close()
        return result != 0
    except Exception:
        return False

def check_dependencies():
    """检查依赖是否已安装"""
    required_packages = [
        'flask',
        'flask_cors', 
        'pandas',
        'numpy',
        'plotly'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少依赖: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    else:
        print("✅ 所有依赖已安装")
        return True

def install_dependencies():
    """安装依赖"""
    print("正在安装依赖...")
    try:
        requirements_path = Path(__file__).parent / "requirements.txt"
        if not requirements_path.exists():
            print("❌ 未找到 requirements.txt")
            return False
            
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(requirements_path)])
        print("✅ 依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 安装错误: {e}")
        return False

def find_app_file():
    """查找 Flask 应用文件"""
    possible_paths = [
        Path(__file__).parent / "app.py",
        Path(__file__).parent / "application.py",
        Path(__file__).parent / "main.py"
    ]
    
    for path in possible_paths:
        if path.exists():
            return str(path)
    
    return None

def main():
    """主函数"""
    print("🚀 正在启动 Kronos Web UI...")
    print("=" * 50)
    
    # 检查我们是否在正确的目录中
    current_dir = Path(__file__).parent
    print(f"工作目录: {current_dir}")
    
    # 检查依赖
    if not check_dependencies():
        print("\n自动安装依赖? (y/n): ", end="")
        if input().lower() == 'y':
            if not install_dependencies():
                return
        else:
            print("请手动安装依赖后重试")
            return
    
    # 检查模型可用性
    try:
        project_root = current_dir.parent
        sys.path.insert(0, str(project_root))
        from model import Kronos, KronosTokenizer, KronosPredictor
        print("✅ Kronos 模型库可用")
        model_available = True
    except ImportError as e:
        print(f"⚠️  Kronos 模型库不可用: {e}")
        print("将使用模拟预测模式")
        model_available = False
    
    # 查找应用文件
    app_file = find_app_file()
    if not app_file:
        print("❌ 无法找到 Flask 应用文件 (app.py, application.py, 或 main.py)")
        return
    
    print(f"找到应用文件: {app_file}")
    
    # 检查端口可用性
    port = 7070
    if not check_port_availability(port=port):
        print(f"❌ 端口 {port} 已被占用")
        print("请停止使用此端口的进程或选择其他端口")
        # 尝试备用端口
        for alt_port in [7071, 7072, 7073]:
            if check_port_availability(port=alt_port):
                port = alt_port
                print(f"使用备用端口: {port}")
                break
        else:
            print("在 7070-7073 范围内未找到可用端口")
            return
    
    # 启动 Flask 应用
    print(f"\n🌐 正在端口 {port} 上启动 Web 服务器...")
    
    # 设置环境变量
    os.environ['FLASK_APP'] = app_file
    os.environ['FLASK_ENV'] = 'development'
    
    try:
        # 切换到 webui 目录
        os.chdir(current_dir)
        
        # 导入并启动应用
        import importlib.util
        spec = importlib.util.spec_from_file_location("app", app_file)
        app_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_module)
        
        app = getattr(app_module, 'app', None)
        if app is None:
            print("❌ 在应用文件中找不到 'app' 对象")
            return
            
        print("✅ Web 服务器启动成功!")
        print(f"🌐 访问地址: http://localhost:{port}")
        print("💡 提示: 按 Ctrl+C 停止服务器")
        
        # 延迟后自动打开浏览器
        def open_browser():
            time.sleep(1)
            try:
                webbrowser.open(f'http://localhost:{port}')
                print("浏览器已自动打开")
            except Exception as e:
                print(f"无法自动打开浏览器: {e}")
        
        # 在后台启动浏览器打开
        import threading
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # 启动 Flask 应用
        app.run(debug=True, host='0.0.0.0', port=port, use_reloader=False)
        
    except KeyboardInterrupt:
        print("\n🛑 服务器已被用户停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("故障排除提示:")
        print("1. 检查端口是否被其他进程占用")
        print("2. 验证所有依赖是否已安装")
        print("3. 确保应用文件存在且有效")
        print("4. 检查控制台输出以获取更详细的错误信息")

if __name__ == "__main__":
    main()