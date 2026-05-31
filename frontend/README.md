# Audio Helper Frontend

基于 React + Vite 的前端应用，用于录音并获取相遇地点推荐。

## 安装依赖

```bash
cd frontend
npm install
```

## 启动开发服务器

```bash
npm run dev
```

服务将运行在 `http://localhost:5175`

## 功能说明

1. **录音**：点击「开始录音」按钮，通过麦克风描述你和朋友的位置
2. **上传**：录音结束后自动上传到后端 API (`/api/process-audio`)
3. **播放**：后端处理完成后，自动播放推荐结果的语音

## 后端接口

前端会调用后端 API：
- 地址：`http://localhost:8007/api/process-audio`
- 方法：`POST`
- 请求格式：`multipart/form-data`
- 请求体：音频文件 (字段名: `audio`)
- 响应格式：音频文件 (audio/mpeg 或其他音频格式)

## 构建生产版本

```bash
npm run build
```

构建产物将输出到 `dist` 目录。
