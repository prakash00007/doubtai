import { useState } from 'react'
import './ChatArea.css'

const EXAMPLES = [
  { q: "A ball thrown at 45° with 20 m/s. Find range and max height." },
  { q: "Explain Newton's 3rd law with real examples" },
  { q: "Find roots of x² + 5x + 6 = 0" },
  { q: "Explain DNA replication steps" },
]

// ── Parse structured answer into sections ─────────────────────────────────────
function parseAnswer(text) {
  const sections = []
  const lines = text.split('\n')
  let current = null

  const SECTION_HEADERS = [
    'GIVEN', 'FIND', 'SOLUTION', 'ANSWER', 'KEY CONCEPT',
    'CONCEPT', 'THEOREM', 'THEOREM/FORMULA', 'FORMULA',
    'CONCEPT OVERVIEW', 'DETAILED EXPLANATION', 'VERIFICATION',
    'COMMON MISTAKE', 'MNEMONIC', 'DIAGRAM NOTE'
  ]

  for (const raw of lines) {
    const line = raw.trim()
    if (!line) {
      if (current) current.lines.push('')
      continue
    }

    // Check if line is a section header
    const header = SECTION_HEADERS.find(h =>
      line.toUpperCase().startsWith(h + ':') || line.toUpperCase() === h
    )

    if (header) {
      if (current) sections.push(current)
      const content = line.includes(':') ? line.slice(line.indexOf(':') + 1).trim() : ''
      current = { type: header, lines: content ? [content] : [] }
    } else if (current) {
      current.lines.push(line)
    } else {
      current = { type: 'INTRO', lines: [line] }
    }
  }

  if (current) sections.push(current)
  return sections
}

// ── Format a single line of text ──────────────────────────────────────────────
function formatLine(line) {
  // Bold **text**
  line = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
  // Step N: pattern
  line = line.replace(/^(Step \d+[:.]\s*)(.*)/, '<span class="step-num">$1</span>$2')
  // Formula: line
  line = line.replace(/^(Formula:|Equation:|Result:|Calculation:|Answer:)\s*(.*)/, 
    '<span class="line-label">$1</span> <span class="line-val">$2</span>')
  // Bullet points
  line = line.replace(/^[•·]\s(.+)/, '<span class="bullet">•</span> $1')
  // ∴ therefore
  line = line.replace(/(∴\s*.+)/, '<span class="therefore">$1</span>')
  return line
}

// ── Render a section ──────────────────────────────────────────────────────────
function Section({ type, lines }) {
  const sectionMap = {
    'GIVEN':             { icon: '📋', color: 'blue',   label: 'Given' },
    'FIND':              { icon: '🎯', color: 'amber',  label: 'Find' },
    'SOLUTION':          { icon: '🔢', color: 'teal',   label: 'Solution' },
    'ANSWER':            { icon: '✅', color: 'green',  label: 'Answer' },
    'KEY CONCEPT':       { icon: '💡', color: 'gold',   label: 'Key Concept' },
    'CONCEPT':           { icon: '📖', color: 'blue',   label: 'Concept' },
    'CONCEPT OVERVIEW':  { icon: '📖', color: 'blue',   label: 'Concept Overview' },
    'THEOREM':           { icon: '📐', color: 'purple', label: 'Theorem' },
    'THEOREM/FORMULA':   { icon: '📐', color: 'purple', label: 'Theorem / Formula' },
    'FORMULA':           { icon: '📐', color: 'purple', label: 'Formula' },
    'VERIFICATION':      { icon: '🔍', color: 'teal',   label: 'Verification' },
    'COMMON MISTAKE':    { icon: '⚠️', color: 'red',    label: 'Common Mistake' },
    'MNEMONIC':          { icon: '🧠', color: 'purple', label: 'Mnemonic' },
    'DIAGRAM NOTE':      { icon: '📊', color: 'blue',   label: 'Diagram Note' },
    'DETAILED EXPLANATION':{ icon: '📝', color: 'teal', label: 'Explanation' },
    'INTRO':             { icon: null, color: 'none',   label: '' },
  }

  const meta = sectionMap[type] || { icon: '•', color: 'none', label: type }
  const content = lines.filter(l => l !== '').join('\n')
  if (!content && !lines.length) return null

  if (meta.color === 'none') {
    return (
      <div className="section-plain">
        {lines.map((line, i) => line ? (
          <div key={i} dangerouslySetInnerHTML={{ __html: formatLine(line) }} />
        ) : <br key={i} />)}
      </div>
    )
  }

  return (
    <div className={`answer-section section-${meta.color}`}>
      {meta.label && (
        <div className="section-header">
          {meta.icon && <span className="section-icon">{meta.icon}</span>}
          <span className="section-label">{meta.label}</span>
        </div>
      )}
      <div className="section-body">
        {lines.map((line, i) => {
          if (!line) return <br key={i} />
          // Detect formula lines (contains = with math)
          const isFormula = /[=+\-×÷√²³°]/.test(line) &&
                            /[A-Za-zα-ωΑ-Ω]/.test(line) &&
                            line.length < 80 &&
                            !line.startsWith('Step') &&
                            !line.startsWith('•')
          if (isFormula && type === 'SOLUTION') {
            return <div key={i} className="formula-box">{line}</div>
          }
          return (
            <div key={i} className="section-line"
              dangerouslySetInnerHTML={{ __html: formatLine(line) }} />
          )
        })}
      </div>
    </div>
  )
}

// ── Mini visualisation tool ───────────────────────────────────────────────────
function StepViz({ sections }) {
  const steps = sections
    .filter(s => s.type === 'SOLUTION')
    .flatMap(s => {
      const result = []
      let current = null
      for (const line of s.lines) {
        if (line.match(/^Step \d+/)) {
          if (current) result.push(current)
          current = { title: line.replace(/^Step \d+[:.]\s*/, ''), lines: [] }
        } else if (current && line) {
          current.lines.push(line)
        }
      }
      if (current) result.push(current)
      return result
    })

  if (steps.length < 2) return null

  return (
    <div className="step-viz">
      <div className="viz-label">Solution Flow</div>
      <div className="viz-steps">
        {steps.map((step, i) => (
          <div key={i} className="viz-step">
            <div className="viz-num">{i + 1}</div>
            <div className="viz-content">
              <div className="viz-title">{step.title}</div>
              {step.lines.slice(0, 1).map((l, j) => (
                <div key={j} className="viz-line">{l}</div>
              ))}
            </div>
            {i < steps.length - 1 && <div className="viz-arrow">→</div>}
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Bubbles ───────────────────────────────────────────────────────────────────
function UserBubble({ text }) {
  return (
    <div className="msg msg-user">
      <div className="bubble-user">{text}</div>
    </div>
  )
}

function AIBubble({ text, sources, model, fromCache, similar, onSimilarClick }) {
  const [copied, setCopied] = useState(false)
  const [showRaw, setShowRaw] = useState(false)

  const copyAnswer = () => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const sections = parseAnswer(text)

  return (
    <div className="msg msg-ai">
      {/* Header */}
      <div className="ai-header">
        <span className="ai-badge">AI Answer</span>
        {sources && sources.length > 0 && (
          <span className="src-badge">📖 {sources.slice(0,2).join(' · ')}</span>
        )}
        {model && (
          <span className="model-badge">
            {model.includes('70b') ? 'Llama 70B' :
             model.includes('8b')  ? 'Llama 8B' :
             model.includes('scout') ? 'Vision' : model}
          </span>
        )}
        {fromCache && <span className="cache-badge">⚡ Instant</span>}
        <div className="header-actions">
          <button className="icon-btn" onClick={() => setShowRaw(!showRaw)} title="Toggle view">
            {showRaw ? '📊' : '📝'}
          </button>
          <button className="copy-btn" onClick={copyAnswer}>
            {copied ? '✅' : '📋 Copy'}
          </button>
        </div>
      </div>

      {/* Answer body */}
      <div className="bubble-ai">
        {showRaw ? (
          <pre className="raw-text">{text}</pre>
        ) : (
          <>
            {sections.map((s, i) => (
              <Section key={i} type={s.type} lines={s.lines} />
            ))}
            <StepViz sections={sections} />
          </>
        )}
      </div>

      {/* Similar questions */}
      {similar && similar.length > 0 && (
        <div className="similar-section">
          <div className="similar-label">🔗 Related doubts</div>
          <div className="similar-chips">
            {similar.map((q, i) => (
              <div key={i} className="similar-chip" onClick={() => onSimilarClick(q)}>
                {q}
              </div>
            ))}
          </div>
        </div>
      )}
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
      <div className="ai-header"><span className="ai-badge">Thinking...</span></div>
      <div className="bubble-ai loading-bubble">
        <div className="dots"><span /><span /><span /></div>
        <div className="loading-steps">
          <div className="ls ls1">📖 Searching NCERT + HC Verma...</div>
          <div className="ls ls2">🧠 Understanding the question...</div>
          <div className="ls ls3">✍️ Writing step-by-step solution...</div>
        </div>
      </div>
    </div>
  )
}

function Welcome({ onExampleClick }) {
  return (
    <div className="welcome">
      <div className="welcome-icon">📚</div>
      <div className="welcome-title">Ask your doubt.</div>
      <div className="welcome-sub">
        Step-by-step answers in the style of NCERT and HC Verma.<br />
        Like having an IIT topper available 24/7.
      </div>
      <div className="example-grid">
        {EXAMPLES.map((e, i) => (
          <div key={i} className="example-chip" onClick={() => onExampleClick(e.q)}>
            <span className="chip-arrow">→</span> {e.q}
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Main export ───────────────────────────────────────────────────────────────
export default function ChatArea({ messages, loading, subject, bottomRef, onExampleClick }) {
  return (
    <div className="chat-area">
      {messages.length === 0 && !loading && (
        <Welcome onExampleClick={onExampleClick} />
      )}
      {messages.map((m, i) => {
        if (m.type === 'user')  return <UserBubble key={i} text={m.text} />
        if (m.type === 'ai')    return (
          <AIBubble
            key={i}
            text={m.text}
            sources={m.sources}
            model={m.model}
            fromCache={m.fromCache}
            similar={m.similar}
            onSimilarClick={onExampleClick}
          />
        )
        if (m.type === 'error') return <ErrorBubble key={i} text={m.text} />
        return null
      })}
      {loading && <LoadingBubble />}
      <div ref={bottomRef} />
    </div>
  )
}