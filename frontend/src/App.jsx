import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import Sidebar from './components/Sidebar'
import ChatArea from './components/ChatArea'
import InputBar from './components/InputBar'
import './App.css'

// Use same-origin by default (works with Vite proxy in dev + single-service deploy in prod).
// Optionally override with `VITE_BACKEND_URL` if you host API separately.
const BACKEND = import.meta.env.VITE_BACKEND_URL || ''

export default function App() {
  const [messages, setMessages]     = useState([])
  const [subject, setSubject]       = useState('Physics')
  const [loading, setLoading]       = useState(false)
  const [remaining, setRemaining]   = useState(10)
  const [history, setHistory]       = useState([])
  const [inputText, setInputText]   = useState('')
  const [chatHistory, setChatHistory] = useState([])  // conversation memory
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const sendQuestion = async (question) => {
    if (!question.trim() || loading) return

    setMessages(prev => [...prev, { type: 'user', text: question }])
    setHistory(prev => [question.slice(0, 45), ...prev.slice(0, 7)])
    setInputText('')
    setLoading(true)

    try {
      const res = await axios.post(`${BACKEND}/api/solve`, {
        question: question.trim(),
        subject:  subject,
        history:  chatHistory.slice(-8)   // send last 4 exchanges for context
      })

      // Save to conversation memory
      setChatHistory(prev => [...prev,
        { role: 'user',      content: question },
        { role: 'assistant', content: res.data.answer }
      ])

      setMessages(prev => [...prev, {
        type:      'ai',
        text:      res.data.answer,
        sources:   res.data.sources,
        model:     res.data.model,
        fromCache: res.data.from_cache,
        similar:   res.data.similar || []
      }])

      if (res.data.remaining !== null) setRemaining(res.data.remaining)

    } catch (err) {
      const msg = err.response?.data?.detail || 'Could not connect to server. Make sure the backend is running.'
      setMessages(prev => [...prev, { type: 'error', text: msg }])
    }

    setLoading(false)
  }

  const sendImage = async (file) => {
    if (!file || loading) return

    setMessages(prev => [...prev, {
      type: 'user',
      text: `📷 Reading: ${file.name}`,
      isImage: true
    }])
    setLoading(true)

    try {
      const form = new FormData()
      form.append('file', file)
      form.append('subject', subject)

      const res = await axios.post(`${BACKEND}/api/image`, form)

      // Show extracted question
      if (res.data.question) {
        setMessages(prev => [...prev, {
          type: 'user',
          text: `📝 Extracted: "${res.data.question}"`
        }])
      }

      // Save to conversation memory
      setChatHistory(prev => [...prev,
        { role: 'user',      content: res.data.question || 'Image question' },
        { role: 'assistant', content: res.data.answer }
      ])

      setMessages(prev => [...prev, {
        type:    'ai',
        text:    res.data.answer,
        sources: res.data.sources,
        model:   res.data.model,
        similar: res.data.similar || []
      }])

    } catch (err) {
      setMessages(prev => [...prev, { type: 'error', text: 'Image upload failed. Try again.' }])
    }

    setLoading(false)
  }

  // Clear conversation memory when subject changes
  const handleSubjectChange = (newSubject) => {
    setSubject(newSubject)
    setChatHistory([])
  }

  const handleExampleClick = (q) => {
    setInputText(q)
  }

  return (
    <div className="app-layout">
      <Sidebar
        subject={subject}
        setSubject={handleSubjectChange}
        history={history}
        remaining={remaining}
      />
      <div className="main-panel">
        <ChatArea
          messages={messages}
          loading={loading}
          subject={subject}
          bottomRef={bottomRef}
          onExampleClick={handleExampleClick}
        />
        <InputBar
          onSend={sendQuestion}
          onImage={sendImage}
          loading={loading}
          subject={subject}
          inputText={inputText}
          setInputText={setInputText}
        />
      </div>
    </div>
  )
}
