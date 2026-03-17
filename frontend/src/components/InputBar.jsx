import { useRef } from 'react'
import './InputBar.css'

export default function InputBar({ onSend, onImage, loading, subject, inputText, setInputText }) {
  const fileRef = useRef(null)
  const textRef = useRef(null)

  const handleSend = () => {
    if (!inputText.trim() || loading) return
    onSend(inputText.trim())
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleResize = (e) => {
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 140) + 'px'
    setInputText(e.target.value)
  }

  const handleFile = (e) => {
    const file = e.target.files?.[0]
    if (file) onImage(file)
    e.target.value = ''
  }

  const subjectColors = {
    Physics:   '#c17f24',
    Chemistry: '#1a6b5a',
    Maths:     '#1a4a8a',
    Biology:   '#5a8a1a',
  }

  return (
    <div className="input-bar">
      <div className="input-subject-tag" style={{ color: subjectColors[subject] }}>
        {subject}
      </div>

      <div className="input-box">
        <textarea
          id="q-input"
          ref={textRef}
          className="q-textarea"
          placeholder={`Ask a ${subject} doubt... (Enter to send, Shift+Enter for new line)`}
          value={inputText}
          onChange={handleResize}
          onKeyDown={handleKey}
          rows={1}
          disabled={loading}
        />

        <div className="input-actions">
          <button
            className="action-btn"
            onClick={() => fileRef.current?.click()}
            disabled={loading}
            title="Upload photo of question"
          >
            📷
          </button>
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            style={{ display: 'none' }}
            onChange={handleFile}
          />

          <button
            className={`send-btn ${inputText.trim() && !loading ? 'active' : ''}`}
            onClick={handleSend}
            disabled={!inputText.trim() || loading}
          >
            {loading ? (
              <span className="send-spin">⏳</span>
            ) : (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            )}
          </button>
        </div>
      </div>

      <div className="input-hint">
        <span>Enter to send · Shift+Enter for new line · 📷 upload photo</span>
        <span className="char-count">{inputText.length}/2000</span>
      </div>
    </div>
  )
}