import './Sidebar.css'

const SUBJECTS = [
  { id: 'Physics',   icon: '⚡', books: 'NCERT + HC Verma + Irodov' },
  { id: 'Chemistry', icon: '🧪', books: 'NCERT + N Awasthi' },
  { id: 'Maths',     icon: '📐', books: 'NCERT + Cengage' },
  { id: 'Biology',   icon: '🌿', books: 'NCERT + Dr Ali' },
]

export default function Sidebar({ subject, setSubject, history, remaining }) {
  return (
    <aside className="sidebar">

      {/* Logo */}
      <div className="sidebar-logo">
        <div className="logo-mark">D</div>
        <div>
          <div className="logo-name">DoubtAI</div>
          <div className="logo-sub">JEE · NEET · Class 11/12</div>
        </div>
      </div>

      {/* Subject selector */}
      <div className="sidebar-section">
        <div className="section-label">Subject</div>
        {SUBJECTS.map(s => (
          <button
            key={s.id}
            className={`subj-btn ${subject === s.id ? 'active' : ''}`}
            onClick={() => setSubject(s.id)}
          >
            <span className="subj-icon">{s.icon}</span>
            <div className="subj-info">
              <div className="subj-name">{s.id}</div>
              <div className="subj-books">{s.books}</div>
            </div>
          </button>
        ))}
      </div>

      {/* Free quota */}
      <div className="quota-box">
        <div className="quota-label">Free doubts today</div>
        <div className="quota-bar-wrap">
          <div
            className="quota-bar"
            style={{ width: `${(remaining / 10) * 100}%` }}
          />
        </div>
        <div className="quota-count">{remaining} / 10 remaining</div>
      </div>

      {/* History */}
      {history.length > 0 && (
        <div className="sidebar-section" style={{ flex: 1 }}>
          <div className="section-label">Recent</div>
          {history.map((h, i) => (
            <div key={i} className="hist-item">
              {h}{h.length >= 45 ? '...' : ''}
            </div>
          ))}
        </div>
      )}

      {/* Footer */}
      <div className="sidebar-footer">
        <div className="powered">Powered by Groq · Llama 3.3</div>
      </div>

    </aside>
  )
}