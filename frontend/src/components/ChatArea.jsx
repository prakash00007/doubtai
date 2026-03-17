import './ChatArea.css'

const EXAMPLES = [
  { subj: 'Physics',   q: "Explain Newton's 3rd law with examples" },
  { subj: 'Physics',   q: "What is the work-energy theorem?" },
  { subj: 'Chemistry', q: "Explain Hess's law with example" },
  { subj: 'Maths',     q: "Explain integration by parts" },
  { subj: 'Biology',   q: "Explain DNA replication steps" },
  { subj: 'Physics',   q: "How does SHM relate to circular motion?" },
]

function formatAnswer(text) {
  // Bold **text**
  text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
  // Step headers
  text = text.replace(/^(Step \d+[:.]\s*)/gm, '<span class="step-label">$1</span>')
  // KEY CONCEPT
  text = text.replace(/(KEY CONCEPT[:\s]+)(.*)/gi,
    '<div class="key-concept"><span class="kc-label">KEY CONCEPT</span> $2</div>')
  // Newlines
  text = text.replace(/\n\n/g, '</p><p>')
  text = text.replace(/\n/g, '<br/>')
  return `<p>${text}</p>`
}

function UserBubble({ text }) {
  return (
    <div className="msg msg-user">
      <div className="bubble-user">{text}</div>
    </div>
  )
}

function AIBubble({ text, sources, model }) {
  return (
    <div className="msg msg-ai">
      <div className="ai-header">
        <span className="ai-badge">AI Answer</span>
        {sources && sources.length > 0 && (
          <span className="src-badge">📖 {sources.join(' · ')}</span>
        )}
        {model && (
          <span className="model-badge">{model.split('-').slice(0,3).join('-')}</span>
        )}
      </div>
      <div
        className="bubble-ai"
        dangerouslySetInnerHTML={{ __html: formatAnswer(text) }}
      />
    </div>
  )
}

function ErrorBubble({ text }) {
  return (
    <div className="msg msg-error">
      <div className="bubble-error">⚠️ {text}</div>
    </div>
  )
}

function LoadingBubble() {
  return (
    <div className="msg msg-ai">
      <div className="ai-header">
        <span className="ai-badge">Thinking...</span>
      </div>
      <div className="bubble-ai loading-bubble">
        <div className="dots">
          <span /><span /><span />
        </div>
        <div className="loading-steps">
          <div className="ls ls1">Searching books...</div>
          <div className="ls ls2">Understanding question...</div>
          <div className="ls ls3">Writing answer...</div>
        </div>
      </div>
    </div>
  )
}

function Welcome({ subject }) {
  return (
    <div className="welcome">
      <div className="welcome-title">
        Ask your doubt.
      </div>
      <div className="welcome-sub">
        Get step-by-step answers in the style of NCERT,<br />
        HC Verma, Cengage — like your best teacher.
      </div>
      <div className="example-grid">
        {EXAMPLES.filter(e => e.subj === subject || true).slice(0, 4).map((e, i) => (
          <div
            key={i}
            className="example-chip"
            onClick={() => onExampleClick(e.q)}
          >
            {e.q}
          </div>
        ))}
      </div>
    </div>
  )
}

export default function ChatArea({ messages, loading, subject, bottomRef }) {
  return (
    <div className="chat-area">
      {messages.length === 0 && !loading && (
        <Welcome subject={subject} />
      )}

      {messages.map((m, i) => {
        if (m.type === 'user')  return <UserBubble  key={i} text={m.text} />
        if (m.type === 'ai')    return <AIBubble    key={i} text={m.text} sources={m.sources} model={m.model} />
        if (m.type === 'error') return <ErrorBubble key={i} text={m.text} />
        return null
      })}

      {loading && <LoadingBubble />}

      <div ref={bottomRef} />
    </div>
  )
}