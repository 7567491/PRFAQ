"""字体安装和配置脚本"""
import os
import shutil
import platform
from pathlib import Path
import subprocess
import logging
from typing import List, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FontInstaller:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.fonts_dir = self.project_root / "assets" / "fonts"
        self.fonts_dir.mkdir(parents=True, exist_ok=True)
        
    def get_system_font_dir(self) -> Path:
        """获取系统字体目录"""
        system = platform.system()
        if system == "Windows":
            return Path(os.environ["WINDIR"]) / "Fonts"
        elif system == "Linux":
            return Path("/usr/share/fonts/chinese")
        elif system == "Darwin":  # macOS
            return Path("/Library/Fonts")
        else:
            raise OSError(f"Unsupported operating system: {system}")
            
    def install_system_fonts(self) -> bool:
        """安装系统字体"""
        try:
            system = platform.system()
            if system == "Linux":
                logger.info("在Linux系统上安装字体...")
                try:
                    # 更新包管理器
                    subprocess.run(["apt-get", "update"], check=True)
                    
                    # 安装字体包
                    subprocess.run([
                        "apt-get", "install", "-y",
                        "fonts-wqy-microhei",
                        "fonts-wqy-zenhei"
                    ], check=True)
                    
                    logger.info("系统字体安装成功")
                    return True
                except subprocess.CalledProcessError as e:
                    logger.error(f"安装系统字体失败: {e}")
                    return False
                    
            logger.info(f"在 {system} 系统上无需安装额外的系统字体")
            return True
            
        except Exception as e:
            logger.error(f"安装系统字体时出错: {e}")
            return False
            
    def copy_builtin_fonts(self) -> bool:
        """复制内置字体到项目目录"""
        try:
            # 定义内置字体列表
            builtin_fonts = [
                ("msyh.ttf", "微软雅黑"),
                ("msyhbd.ttf", "微软雅黑粗体"),
                ("simsun.ttc", "宋体")
            ]
            
            # 检查并复制每个字体
            for font_file, font_name in builtin_fonts:
                # 尝试从系统字体目录复制
                system_font = self.get_system_font_dir() / font_file
                target_font = self.fonts_dir / font_file
                
                if system_font.exists():
                    shutil.copy2(system_font, target_font)
                    logger.info(f"已复制 {font_name} ({font_file})")
                else:
                    logger.warning(f"未找到 {font_name} ({font_file})")
                    
            return True
            
        except Exception as e:
            logger.error(f"复制内置字体时出错: {e}")
            return False
            
    def verify_fonts(self) -> bool:
        """验证字体文件"""
        required_fonts = ["msyh.ttf", "simsun.ttc"]
        missing_fonts = []
        
        for font in required_fonts:
            font_path = self.fonts_dir / font
            if not font_path.exists():
                missing_fonts.append(font)
                
        if missing_fonts:
            logger.warning(f"缺少以下字体文件: {', '.join(missing_fonts)}")
            return False
            
        logger.info("字体文件验证完成")
        return True
        
    def setup(self) -> bool:
        """完整的字体设置流程"""
        try:
            logger.info("开始设置字体...")
            
            # 1. 安装系统字体
            if not self.install_system_fonts():
                logger.warning("系统字体安装失败")
            
            # 2. 复制内置字体
            if not self.copy_builtin_fonts():
                logger.warning("复制内置字体失败")
            
            # 3. 验证字体
            if not self.verify_fonts():
                logger.warning("字体验证失败，但将继续使用可用字体")
            
            logger.info("字体设置完成")
            return True
            
        except Exception as e:
            logger.error(f"字体设置失败: {e}")
            return False

if __name__ == "__main__":
    installer = FontInstaller()
    installer.setup() 