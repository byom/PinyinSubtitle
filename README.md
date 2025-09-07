# PinyinSubtitle

一个基于Flask的中文视频字幕拼音烧录服务，可以将SRT字幕文件转换为带拼音注音的双层字幕，并烧录到视频文件中。

## 功能特性

- 支持SRT字幕文件解析和处理
- 自动生成中文拼音注音
- 双层字幕显示（中文 + 拼音）
- 字幕硬编码烧录到视频
- 使用思源黑体字体确保中文显示效果
- 支持多种视频格式处理

## 系统要求

### 必需软件
- Python 3.7+
- FFmpeg（需要在系统PATH中可用）

### Python依赖
- Flask - Web框架
- pypinyin - 中文转拼音库
- requests - HTTP请求库（测试用）

## 安装说明

### 1. 安装系统依赖

**Windows:**
- 下载并安装 [FFmpeg](https://ffmpeg.org/download.html)
- 确保FFmpeg可执行文件在系统PATH中

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt-get install ffmpeg  # Ubuntu/Debian
sudo yum install ffmpeg      # CentOS/RHEL
```

### 2. 安装Python环境

运行项目提供的安装脚本：
```bash
Install.bat
```

这将自动：
- 创建Python虚拟环境
- 安装所有必需的依赖包

## 使用方法

### 启动服务

运行启动脚本：
```bash
start-subtitle-service.bat
```

服务将在 `http://127.0.0.1:5050` 启动

### API调用

**端点:** `POST /burn_subtitle`

**参数:**
- `video_file` (文件): 需要处理的视频文件
- `subtitle_file` (文件): SRT格式的字幕文件

**响应:** 返回烧录了字幕的视频文件

### 使用示例

#### Python客户端示例
```python
import requests

url = "http://127.0.0.1:5050/burn_subtitle"

with open("video.mp4", 'rb') as video, open("subtitles.srt", 'rb') as subtitle:
    files = {
        'video_file': ('video.mp4', video, 'video/mp4'),
        'subtitle_file': ('subtitles.srt', subtitle, 'application/x-subrip')
    }
    
    response = requests.post(url, files=files)
    
    if response.status_code == 200:
        with open("output_with_subtitles.mp4", 'wb') as f:
            f.write(response.content)
        print("视频处理完成!")
    else:
        print(f"处理失败: {response.status_code}")
```

#### cURL示例
```bash
curl -X POST \
  -F "video_file=@video.mp4" \
  -F "subtitle_file=@subtitles.srt" \
  -o output.mp4 \
  http://127.0.0.1:5050/burn_subtitle
```

### 测试

运行项目自带的测试：
```bash
python test/test.py
```

确保服务正在运行，测试将使用示例文件验证功能。

## 技术实现

### 字幕处理流程
1. **文件上传**: 接收视频文件和SRT字幕文件
2. **格式转换**: 将SRT转换为ASS格式
3. **拼音生成**: 使用pypinyin为中文字符生成拼音
4. **双层字幕**: 创建中文字符和拼音的双层显示
5. **视频烧录**: 使用FFmpeg将字幕硬编码到视频
6. **文件清理**: 自动清理临时处理文件

### 字幕样式
- **中文字幕**: 60像素，白色，底部显示
- **拼音注音**: 30像素，黄色，中文上方显示
- **字体**: 思源黑体（Source Han Sans SC）

## 项目结构

```
PinyinSubtitle/
├── app.py                    # 主应用文件
├── Install.bat              # 安装脚本
├── start-subtitle-service.bat # 启动脚本
├── requirements.txt         # Python依赖
├── fonts/                   # 字体文件目录
│   └── SourceHanSansSC-*.otf
├── test/                    # 测试文件
│   ├── test.py             # 测试客户端
│   ├── test_video.mp4      # 示例视频
│   └── test_subs.srt       # 示例字幕
├── burn_service/           # 临时文件处理目录
└── venv/                   # Python虚拟环境
```

## 常见问题

### Q: FFmpeg命令执行失败
A: 确保FFmpeg已正确安装并在系统PATH中。可以在命令行运行 `ffmpeg -version` 验证。

### Q: 中文字体显示异常
A: 检查fonts目录中是否包含思源黑体字体文件，确保字体路径正确。

### Q: 字幕时间轴不同步
A: 检查SRT文件格式是否标准，确保时间格式为 `HH:MM:SS,mmm --> HH:MM:SS,mmm`。

### Q: 处理大视频文件时间过长
A: 这是正常现象，视频编码是CPU密集型操作。可以调整FFmpeg参数中的preset设置来平衡速度和质量。

## 开发说明

### 修改字体
编辑 `app.py` 中的 `FONT_PATH` 变量指向不同的字体文件。

### 调整字幕样式
修改 `create_ass_from_srt` 函数中的样式定义：
- 字体大小：修改 `Fontsize` 参数
- 颜色：修改 `PrimaryColour` 参数
- 位置：修改 `MarginV` 参数

## 许可证

此项目仅用于学习和个人使用。请确保遵守相关字体和第三方库的许可证要求。