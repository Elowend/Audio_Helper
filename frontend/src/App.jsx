import { useState, useRef } from 'react'
import axios from 'axios'
import './App.css'

function App() {
  const [isRecording, setIsRecording] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [statusMessage, setStatusMessage] = useState('点击开始录音，描述你和朋友的位置')
  const [audioUrl, setAudioUrl] = useState(null)
  const [recommendationAudio, setRecommendationAudio] = useState(null)
  
  const mediaRecorderRef = useRef(null)
  const audioChunksRef = useRef([])
  const audioRef = useRef(null)

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
        await uploadAudio(audioBlob)
        stream.getTracks().forEach(track => track.stop())
      }

      mediaRecorder.start()
      setIsRecording(true)
      setStatusMessage('录音中... 再次点击停止录音')
    } catch (error) {
      console.error('录音启动失败:', error)
      setStatusMessage('无法访问麦克风，请检查权限设置')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      setStatusMessage('正在处理中，请稍候...')
    }
  }

  const uploadAudio = async (audioBlob) => {
    setIsProcessing(true)
    const formData = new FormData()
    formData.append('audio', audioBlob, 'recording.webm')

    try {
      // 调用完整处理流程：ASR + DeepSeek + 高德MCP
      const response = await axios.post('/api/process-audio-with-location', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      console.log('✅ 处理成功:', response.data)
      
      const asrText = response.data.asr_result?.text || '未识别到内容'
      const audioSize = response.data.audio_file?.size || 0
      const addresses = response.data.addresses || {}
      const locations = response.data.locations || {}
      const recommendation = response.data.recommendation || null
      
      // 构建显示消息
      let message = `✅ 处理完成！\n\n📝 识别结果：\n${asrText}\n\n`
      
      // 显示地址提取结果
      if (addresses.origin || addresses.destination) {
        message += `📍 地址提取：\n`
        if (addresses.origin) {
          message += `起点: ${addresses.origin}\n`
        }
        if (addresses.destination) {
          message += `终点: ${addresses.destination}\n`
        }
        message += `\n`
      }
      
      // 显示地理编码结果
      if (locations.origin || locations.destination) {
        message += `🗺️ 地理编码：\n`
        if (locations.origin) {
          message += `起点坐标: (${locations.origin.lng}, ${locations.origin.lat})\n`
          if (locations.origin.formatted_address) {
            message += `详细地址: ${locations.origin.formatted_address}\n`
          }
        }
        if (locations.destination) {
          message += `终点坐标: (${locations.destination.lng}, ${locations.destination.lat})\n`
          if (locations.destination.formatted_address) {
            message += `详细地址: ${locations.destination.formatted_address}\n`
          }
        }
        message += `\n`
      }
      
      // 显示推荐信息
      if (recommendation && recommendation.text) {
        message += `💡 智能推荐：\n${recommendation.text}\n\n`
        
        // 设置语音推荐 URL
        if (recommendation.audio_file) {
          const audioUrl = `/api/audio/${recommendation.audio_file}`
          setRecommendationAudio(audioUrl)
          message += `🔊 点击下方播放语音推荐\n\n`
        }
      }
      
      message += `📦 音频大小: ${(audioSize / 1024).toFixed(2)} KB\n`
      message += `🆔 请求ID: ${response.data.request_id}`
      
      setStatusMessage(message)
      
    } catch (error) {
      console.error('音频处理失败:', error)
      setStatusMessage('❌ 处理失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setIsProcessing(false)
    }
  }

  const handleRecordClick = () => {
    if (isRecording) {
      stopRecording()
    } else {
      startRecording()
    }
  }

  return (
    <div className="app-container">
      <div className="card">
        <h1>🎤 Audio Helper</h1>
        <p className="subtitle">描述你和朋友的位置，我来推荐相遇地点</p>
        
        <div className="status-section">
          <p className="status-message">{statusMessage}</p>
        </div>

        <div className="controls">
          <button 
            className={`record-button ${isRecording ? 'recording' : ''}`}
            onClick={handleRecordClick}
            disabled={isProcessing}
          >
            {isRecording ? '⏹ 停止录音' : '🎙 开始录音'}
          </button>
        </div>

        {recommendationAudio && (
          <div className="audio-player">
            <p>🔊 语音推荐</p>
            <audio controls src={recommendationAudio} autoPlay>
              您的浏览器不支持音频播放
            </audio>
          </div>
        )}

        {isProcessing && (
          <div className="loading">
            <div className="spinner"></div>
            <p>正在处理中...</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
