import { useState, useRef, useCallback } from 'react'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import TextStyle from '@tiptap/extension-text-style'
import { Color } from '@tiptap/extension-color'
import Underline from '@tiptap/extension-underline'
import TextAlign from '@tiptap/extension-text-align'
import Highlight from '@tiptap/extension-highlight'
import axios from 'axios'
import {
  Upload, Zap, Download, FileText, ChevronDown,
  Bold, Italic, UnderlineIcon, AlignLeft, AlignCenter,
  AlignRight, List, RotateCcw, CheckCircle, XCircle,
  TrendingUp, Tag, Eye, Loader2, AlertCircle, Sparkles,
  FileDown, BarChart3, ChevronUp, X, Info
} from 'lucide-react'

const API = '/api'

// ═══════════════════════════════════════════════════════
// ATS Score Ring Component
// ═══════════════════════════════════════════════════════
function ATSScoreRing({ score, before, grade }) {
  const radius = 42
  const circumference = 2 * Math.PI * radius
  const filled = (score / 100) * circumference
  const color = score >= 80 ? '#22c55e' : score >= 65 ? '#f59e0b' : score >= 45 ? '#f97316' : '#ef4444'

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="ats-ring-container">
        <svg width="100" height="100" className="drop-shadow-sm">
          <circle cx="50" cy="50" r={radius} fill="none" stroke="#e2e8f0" strokeWidth="8" />
          <circle
            cx="50" cy="50" r={radius}
            fill="none" stroke={color} strokeWidth="8"
            strokeDasharray={circumference}
            strokeDashoffset={circumference - filled}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 1s ease', transform: 'rotate(-90deg)', transformOrigin: '50% 50%' }}
          />
        </svg>
        <div className="absolute text-center" style={{ transform: 'rotate(0deg)' }}>
          <div className="text-2xl font-bold" style={{ color }}>{score}</div>
          <div className="text-xs text-slate-400 font-medium">ATS</div>
        </div>
      </div>
      <div className="flex gap-3 text-xs">
        <span className="text-slate-400">Before: <strong className="text-slate-600">{before}</strong></span>
        <span className="text-slate-400">After: <strong style={{ color }}>{score}</strong></span>
      </div>
      <span
        className="px-2 py-0.5 rounded-full text-xs font-bold text-white"
        style={{ background: color }}
      >
        Grade {grade}
      </span>
    </div>
  )
}

// ═══════════════════════════════════════════════════════
// Editor Toolbar
// ═══════════════════════════════════════════════════════
function EditorToolbar({ editor }) {
  if (!editor) return null

  const ToolBtn = ({ onClick, active, children, title }) => (
    <button
      onMouseDown={(e) => { e.preventDefault(); onClick() }}
      title={title}
      className={`
        p-1.5 rounded text-sm transition-all
        ${active
          ? 'bg-blue-100 text-blue-700'
          : 'text-slate-600 hover:bg-slate-100 hover:text-slate-800'}
      `}
    >
      {children}
    </button>
  )

  return (
    <div className="flex items-center gap-0.5 px-2 py-1.5 bg-white border-b border-slate-200 flex-wrap">
      <ToolBtn
        onClick={() => editor.chain().focus().toggleBold().run()}
        active={editor.isActive('bold')}
        title="Bold"
      ><Bold size={14} /></ToolBtn>

      <ToolBtn
        onClick={() => editor.chain().focus().toggleItalic().run()}
        active={editor.isActive('italic')}
        title="Italic"
      ><Italic size={14} /></ToolBtn>

      <ToolBtn
        onClick={() => editor.chain().focus().toggleUnderline().run()}
        active={editor.isActive('underline')}
        title="Underline"
      ><UnderlineIcon size={14} /></ToolBtn>

      <div className="w-px h-4 bg-slate-200 mx-1" />

      <ToolBtn
        onClick={() => editor.chain().focus().setTextAlign('left').run()}
        active={editor.isActive({ textAlign: 'left' })}
        title="Align Left"
      ><AlignLeft size={14} /></ToolBtn>

      <ToolBtn
        onClick={() => editor.chain().focus().setTextAlign('center').run()}
        active={editor.isActive({ textAlign: 'center' })}
        title="Align Center"
      ><AlignCenter size={14} /></ToolBtn>

      <ToolBtn
        onClick={() => editor.chain().focus().setTextAlign('right').run()}
        active={editor.isActive({ textAlign: 'right' })}
        title="Align Right"
      ><AlignRight size={14} /></ToolBtn>

      <div className="w-px h-4 bg-slate-200 mx-1" />

      <ToolBtn
        onClick={() => editor.chain().focus().toggleBulletList().run()}
        active={editor.isActive('bulletList')}
        title="Bullet List"
      ><List size={14} /></ToolBtn>

      <div className="w-px h-4 bg-slate-200 mx-1" />

      <ToolBtn
        onClick={() => editor.chain().focus().undo().run()}
        active={false}
        title="Undo"
      ><RotateCcw size={14} /></ToolBtn>

      <div className="flex-1" />

      <span className="text-xs text-slate-400 px-2">Live Editor</span>
    </div>
  )
}

// ═══════════════════════════════════════════════════════
// Keywords Panel
// ═══════════════════════════════════════════════════════
function KeywordsPanel({ added, existing, jdSkills }) {
  const [open, setOpen] = useState(true)
  return (
    <div className="border border-slate-200 rounded-xl overflow-hidden bg-white shadow-sm">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-4 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
      >
        <span className="flex items-center gap-2"><Tag size={14} className="text-blue-500" /> Keyword Intelligence</span>
        {open ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>

      {open && (
        <div className="px-4 pb-4 space-y-3">
          {added.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-emerald-600 mb-1.5 uppercase tracking-wide">✨ Inserted Keywords</p>
              <div className="flex flex-wrap gap-1">
                {added.map(kw => (
                  <span key={kw} className="keyword-pill bg-emerald-50 text-emerald-700 border border-emerald-200">
                    + {kw}
                  </span>
                ))}
              </div>
            </div>
          )}
          {existing.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-blue-600 mb-1.5 uppercase tracking-wide">✓ Already Had</p>
              <div className="flex flex-wrap gap-1">
                {existing.slice(0, 10).map(kw => (
                  <span key={kw} className="keyword-pill bg-blue-50 text-blue-700 border border-blue-100">
                    {kw}
                  </span>
                ))}
              </div>
            </div>
          )}
          {jdSkills && jdSkills.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-slate-500 mb-1.5 uppercase tracking-wide">JD Requires</p>
              <div className="flex flex-wrap gap-1">
                {jdSkills.slice(0, 12).map(kw => (
                  <span key={kw} className="keyword-pill bg-slate-100 text-slate-600">
                    {kw}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ═══════════════════════════════════════════════════════
// JD Analysis Panel
// ═══════════════════════════════════════════════════════
function JDAnalysisPanel({ analysis }) {
  const [open, setOpen] = useState(false)
  if (!analysis) return null

  return (
    <div className="border border-slate-200 rounded-xl overflow-hidden bg-white shadow-sm">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-4 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50"
      >
        <span className="flex items-center gap-2"><BarChart3 size={14} className="text-purple-500" /> JD Deep Analysis</span>
        {open ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-3 text-xs">
          <div className="grid grid-cols-2 gap-2">
            <div className="bg-slate-50 rounded-lg p-2">
              <p className="text-slate-400 font-medium">Domain</p>
              <p className="text-slate-700 font-semibold mt-0.5">{analysis.domain || '—'}</p>
            </div>
            <div className="bg-slate-50 rounded-lg p-2">
              <p className="text-slate-400 font-medium">Level</p>
              <p className="text-slate-700 font-semibold mt-0.5 capitalize">{analysis.experience_level || '—'}</p>
            </div>
          </div>
          {analysis.job_title && (
            <div className="bg-blue-50 rounded-lg p-2">
              <p className="text-blue-400 font-medium">Detected Role</p>
              <p className="text-blue-700 font-semibold mt-0.5">{analysis.job_title}</p>
            </div>
          )}
          {analysis.technical_skills?.length > 0 && (
            <div>
              <p className="font-semibold text-slate-500 mb-1 uppercase tracking-wide">Top Tech Skills Required</p>
              <div className="flex flex-wrap gap-1">
                {analysis.technical_skills.slice(0, 12).map(s => (
                  <span key={s} className="keyword-pill bg-violet-50 text-violet-700 border border-violet-100">{s}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ═══════════════════════════════════════════════════════
// MAIN APP
// ═══════════════════════════════════════════════════════
export default function App() {
  // ── State ──────────────────────────────────────────
  const [jdText, setJdText] = useState('')
  const [resumeFile, setResumeFile] = useState(null)
  const [resumeData, setResumeData] = useState(null)  // cached parsed data
  const [optimizedData, setOptimizedData] = useState(null)
  const [atsScore, setAtsScore] = useState(null)
  const [keywordsAdded, setKeywordsAdded] = useState([])
  const [keywordsExisting, setKeywordsExisting] = useState([])
  const [jdAnalysis, setJdAnalysis] = useState(null)
  const [status, setStatus] = useState('idle') // idle | parsing | optimizing | done | error
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState('editor') // editor | compare
  const [originalHtml, setOriginalHtml] = useState('')

  const fileInputRef = useRef(null)

  // ── TipTap Editor ──────────────────────────────────
  const editor = useEditor({
    extensions: [
      StarterKit,
      TextStyle,
      Color,
      Underline,
      TextAlign.configure({ types: ['heading', 'paragraph'] }),
      Highlight.configure({ multicolor: true }),
    ],
    content: '',
    editorProps: {
      attributes: {
        class: 'tiptap-resume-editor',
      },
    },
  })

  // ── File Upload Handler ────────────────────────────
  const handleFileChange = useCallback(async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setResumeFile(file)
    setError('')

    // Parse immediately on upload
    setStatus('parsing')
    try {
      const fd = new FormData()
      fd.append('file', file)
      const res = await axios.post(`${API}/parse-resume`, fd)
      if (res.data.success) {
        setResumeData(res.data.data)
        setStatus('idle')
      }
    } catch (err) {
      setResumeData(null)
      setStatus('idle')
      // Silently fail parse preview - will parse again on optimize
    }
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    const file = e.dataTransfer.files?.[0]
    if (file && (file.name.endsWith('.docx') || file.name.endsWith('.pdf'))) {
      fileInputRef.current.files = e.dataTransfer.files
      handleFileChange({ target: { files: e.dataTransfer.files } })
    }
  }, [handleFileChange])

  // ── Optimize Handler ───────────────────────────────
  const handleOptimize = useCallback(async () => {
    if (!jdText.trim() || jdText.trim().length < 50) {
      setError('Please paste a complete job description (at least 50 characters).')
      return
    }
    if (!resumeFile && !resumeData) {
      setError('Please upload your resume (.docx or .pdf).')
      return
    }

    setStatus('optimizing')
    setError('')

    try {
      const fd = new FormData()
      fd.append('jd_text', jdText)

      if (resumeFile) {
        fd.append('file', resumeFile)
      } else if (resumeData) {
        fd.append('resume_json', JSON.stringify(resumeData))
      }

      const res = await axios.post(`${API}/optimize`, fd, {
        timeout: 60000
      })

      if (res.data.success) {
        const html = res.data.html
        setOptimizedData(res.data.optimized_data)
        setAtsScore(res.data.ats)
        setKeywordsAdded(res.data.keywords_added || [])
        setKeywordsExisting(res.data.keywords_existing || [])
        setJdAnalysis(res.data.jd_analysis)

        // Load into editor
        if (editor) {
          editor.commands.setContent(html)
        }

        // Save original for comparison
        if (!originalHtml && resumeData) {
          // Build simple original HTML
          setOriginalHtml(buildSimpleHtml(resumeData))
        }

        setStatus('done')
        setActiveTab('editor')
      }
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Optimization failed'
      setError(msg)
      setStatus('error')
    }
  }, [jdText, resumeFile, resumeData, editor, originalHtml])

  // ── Download Handlers ──────────────────────────────
  const handleDownloadDocx = useCallback(async () => {
    if (!optimizedData) return
    try {
      const res = await axios.post(`${API}/download-docx`,
        { resume_data: optimizedData },
        { responseType: 'blob', timeout: 30000 }
      )
      const url = URL.createObjectURL(new Blob([res.data]))
      const a = document.createElement('a')
      a.href = url
      a.download = `${optimizedData.name || 'Resume'}_Optimized.docx`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      setError('DOCX download failed: ' + (err.response?.data?.detail || err.message))
    }
  }, [optimizedData])

  const handleDownloadPdf = useCallback(async () => {
    if (!optimizedData) return
    try {
      const res = await axios.post(`${API}/download-pdf`,
        { resume_data: optimizedData },
        { responseType: 'blob', timeout: 30000 }
      )
      const url = URL.createObjectURL(new Blob([res.data]))
      const a = document.createElement('a')
      a.href = url
      a.download = `${optimizedData.name || 'Resume'}_Optimized.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      setError('PDF download failed: ' + (err.response?.data?.detail || err.message))
    }
  }, [optimizedData])

  // ── Re-optimize from editor content ───────────────
  const handleReOptimize = useCallback(async () => {
    if (!jdText.trim()) {
      setError('Please provide a job description first.')
      return
    }
    if (!optimizedData) return
    // Re-run optimization with same JD
    handleOptimize()
  }, [jdText, optimizedData, handleOptimize])

  function buildSimpleHtml(data) {
    let html = ''
    if (data?.summary) html += `<p>${data.summary}</p>`
    if (data?.skills?.length) html += `<p>Skills: ${data.skills.join(' • ')}</p>`
    return html
  }

  // ── Status Indicator ───────────────────────────────
  const isLoading = status === 'parsing' || status === 'optimizing'

  // ═══════════════════════════════════════════════════
  // RENDER
  // ═══════════════════════════════════════════════════
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 via-blue-50 to-slate-100">

      {/* ── TOP HEADER ────────────────────────────── */}
      <header className="bg-white border-b border-slate-200 shadow-sm sticky top-0 z-50">
        <div className="max-w-[1600px] mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 to-blue-800 flex items-center justify-center shadow-sm">
              <Sparkles size={16} className="text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold text-slate-800 leading-tight">ResumeAI Pro</h1>
              <p className="text-xs text-slate-400 leading-tight">Smart Resume Optimizer • Personal Edition</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {status === 'done' && (
              <span className="flex items-center gap-1.5 text-xs text-emerald-600 font-medium bg-emerald-50 border border-emerald-200 px-3 py-1 rounded-full">
                <CheckCircle size={12} />
                Optimized
              </span>
            )}
            {atsScore && (
              <span className="text-xs font-bold px-3 py-1 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                ATS Score: {atsScore.after}/100
              </span>
            )}
          </div>
        </div>
      </header>

      {/* ── MAIN LAYOUT ───────────────────────────── */}
      <div className="max-w-[1600px] mx-auto px-4 py-4 flex gap-4 h-[calc(100vh-56px)]">

        {/* ═══════════ LEFT PANEL ═══════════════════ */}
        <div className="w-[400px] flex-shrink-0 flex flex-col gap-3 overflow-y-auto pr-1">

          {/* ─ JD Input ─────────────────────────── */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="px-4 py-3 border-b border-slate-100 flex items-center gap-2">
              <FileText size={15} className="text-blue-500" />
              <span className="text-sm font-semibold text-slate-700">Job Description</span>
              {jdText.length > 50 && (
                <span className="ml-auto text-xs text-emerald-500 font-medium flex items-center gap-1">
                  <CheckCircle size={11} /> Ready
                </span>
              )}
            </div>
            <textarea
              value={jdText}
              onChange={e => setJdText(e.target.value)}
              placeholder="Paste the complete job description here...&#10;&#10;Include: responsibilities, requirements, skills needed, about the company..."
              className="w-full h-56 px-4 py-3 text-sm text-slate-700 resize-none focus:outline-none placeholder-slate-300 leading-relaxed"
              style={{ fontFamily: 'Inter, sans-serif' }}
            />
            <div className="px-4 py-2 bg-slate-50 border-t border-slate-100 flex justify-between items-center">
              <span className="text-xs text-slate-400">{jdText.length} characters</span>
              {jdText.length > 0 && (
                <button
                  onClick={() => setJdText('')}
                  className="text-xs text-slate-400 hover:text-red-400 flex items-center gap-1 transition-colors"
                >
                  <X size={11} /> Clear
                </button>
              )}
            </div>
          </div>

          {/* ─ Resume Upload ────────────────────── */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="px-4 py-3 border-b border-slate-100 flex items-center gap-2">
              <Upload size={15} className="text-blue-500" />
              <span className="text-sm font-semibold text-slate-700">Your Resume</span>
            </div>

            <div
              onDrop={handleDrop}
              onDragOver={e => e.preventDefault()}
              className="mx-4 my-3"
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".docx,.pdf"
                onChange={handleFileChange}
                className="hidden"
                id="resume-upload"
              />

              {!resumeFile ? (
                <label
                  htmlFor="resume-upload"
                  className="flex flex-col items-center justify-center gap-2 border-2 border-dashed border-slate-200 rounded-xl p-6 cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition-all group"
                >
                  <div className="w-10 h-10 rounded-full bg-slate-100 group-hover:bg-blue-100 flex items-center justify-center transition-colors">
                    <Upload size={18} className="text-slate-400 group-hover:text-blue-500" />
                  </div>
                  <div className="text-center">
                    <p className="text-sm font-medium text-slate-600">Drop or click to upload</p>
                    <p className="text-xs text-slate-400 mt-0.5">.docx or .pdf supported</p>
                  </div>
                </label>
              ) : (
                <div className="flex items-center gap-3 p-3 bg-emerald-50 border border-emerald-200 rounded-xl">
                  <div className="w-9 h-9 rounded-lg bg-emerald-100 flex items-center justify-center flex-shrink-0">
                    <FileText size={16} className="text-emerald-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-emerald-700 truncate">{resumeFile.name}</p>
                    <p className="text-xs text-emerald-500">
                      {(resumeFile.size / 1024).toFixed(1)} KB
                      {status === 'parsing' && ' · Parsing...'}
                      {resumeData && status === 'idle' && ' · Parsed ✓'}
                    </p>
                  </div>
                  <button
                    onClick={() => { setResumeFile(null); setResumeData(null); fileInputRef.current.value = '' }}
                    className="text-emerald-400 hover:text-red-400 transition-colors"
                  >
                    <X size={15} />
                  </button>
                </div>
              )}
            </div>

            {resumeData && (
              <div className="mx-4 mb-3 text-xs text-slate-500 bg-slate-50 rounded-lg px-3 py-2 flex gap-3 flex-wrap">
                {resumeData.name && <span className="font-medium text-slate-700">{resumeData.name}</span>}
                {resumeData.years_experience > 0 && <span>~{resumeData.years_experience}yr exp</span>}
                {resumeData.skills?.length > 0 && <span>{resumeData.skills.length} skills detected</span>}
                {resumeData.experience?.length > 0 && <span>{resumeData.experience.length} jobs</span>}
              </div>
            )}
          </div>

          {/* ─ OPTIMIZE BUTTON ─────────────────── */}
          <button
            onClick={handleOptimize}
            disabled={isLoading || !jdText.trim() || (!resumeFile && !resumeData)}
            className={`
              w-full py-3.5 px-6 rounded-2xl font-semibold text-sm transition-all flex items-center justify-center gap-2.5
              shadow-lg
              ${isLoading
                ? 'bg-blue-400 text-white cursor-wait'
                : (!jdText.trim() || (!resumeFile && !resumeData))
                  ? 'bg-slate-200 text-slate-400 cursor-not-allowed shadow-none'
                  : 'bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white cursor-pointer hover:shadow-blue-200 active:scale-[0.98]'
              }
            `}
          >
            {isLoading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                {status === 'parsing' ? 'Parsing Resume...' : 'Optimizing...'}
              </>
            ) : (
              <>
                <Zap size={16} />
                Optimize Resume
              </>
            )}
          </button>

          {/* ─ Error ───────────────────────────── */}
          {error && (
            <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-600">
              <AlertCircle size={14} className="flex-shrink-0 mt-0.5" />
              <span>{error}</span>
              <button onClick={() => setError('')} className="ml-auto flex-shrink-0 text-red-400 hover:text-red-600">
                <X size={12} />
              </button>
            </div>
          )}

          {/* ─ ATS Score ───────────────────────── */}
          {atsScore && (
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-4 fade-in">
              <h3 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
                <TrendingUp size={14} className="text-blue-500" /> ATS Match Score
              </h3>
              <ATSScoreRing
                score={atsScore.after}
                before={atsScore.before}
                grade={atsScore.grade}
              />
            </div>
          )}

          {/* ─ Keywords Panel ──────────────────── */}
          {status === 'done' && (
            <div className="fade-in">
              <KeywordsPanel
                added={keywordsAdded}
                existing={keywordsExisting}
                jdSkills={jdAnalysis?.technical_skills}
              />
            </div>
          )}

          {/* ─ JD Analysis ─────────────────────── */}
          {jdAnalysis && (
            <div className="fade-in">
              <JDAnalysisPanel analysis={jdAnalysis} />
            </div>
          )}

          {/* ─ Download ─────────────────────────── */}
          {status === 'done' && (
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-4 fade-in">
              <h3 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
                <Download size={14} className="text-blue-500" /> Export Resume
              </h3>
              <div className="space-y-2">
                <button
                  onClick={handleDownloadDocx}
                  className="w-full flex items-center gap-2.5 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-medium transition-colors"
                >
                  <FileDown size={15} />
                  Download .DOCX
                  <span className="ml-auto text-xs text-blue-200">Word</span>
                </button>
                <button
                  onClick={handleDownloadPdf}
                  className="w-full flex items-center gap-2.5 px-4 py-2.5 bg-slate-700 hover:bg-slate-800 text-white rounded-xl text-sm font-medium transition-colors"
                >
                  <FileDown size={15} />
                  Download .PDF
                  <span className="ml-auto text-xs text-slate-300">PDF</span>
                </button>
              </div>
            </div>
          )}

          {/* ─ Re-optimize ─────────────────────── */}
          {status === 'done' && (
            <button
              onClick={handleReOptimize}
              className="w-full py-2.5 px-4 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-sm font-medium text-slate-600 transition-colors flex items-center justify-center gap-2"
            >
              <RotateCcw size={13} /> Re-Optimize
            </button>
          )}

        </div>

        {/* ═══════════ RIGHT PANEL ══════════════════ */}
        <div className="flex-1 min-w-0 flex flex-col">

          {/* ─ Panel Header & Tabs ─────────────── */}
          <div className="bg-white rounded-t-2xl border border-slate-200 border-b-0 px-4 py-2 flex items-center gap-2">
            <button
              onClick={() => setActiveTab('editor')}
              className={`
                flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors
                ${activeTab === 'editor'
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-500 hover:bg-slate-100'}
              `}
            >
              <FileText size={12} /> Live Editor
            </button>
            {originalHtml && (
              <button
                onClick={() => setActiveTab('compare')}
                className={`
                  flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors
                  ${activeTab === 'compare'
                    ? 'bg-purple-600 text-white'
                    : 'text-slate-500 hover:bg-slate-100'}
                `}
              >
                <Eye size={12} /> Before/After
              </button>
            )}

            <div className="flex-1" />

            {/* Word page indicator */}
            <span className="text-xs text-slate-400 flex items-center gap-1">
              <Info size={11} />
              Edit freely • Changes auto-saved
            </span>
          </div>

          {/* ─ Editor Toolbar ──────────────────── */}
          {activeTab === 'editor' && (
            <div className="border-x border-slate-200">
              <EditorToolbar editor={editor} />
            </div>
          )}

          {/* ─ Editor / Compare Content ────────── */}
          <div className="flex-1 bg-white rounded-b-2xl border border-slate-200 border-t-0 overflow-hidden flex flex-col">

            {activeTab === 'editor' && (
              <div className="flex-1 overflow-y-auto">
                {/* Word-style page wrapper */}
                <div className="min-h-full bg-slate-100 py-6 px-4 flex justify-center">
                  <div
                    className="bg-white shadow-lg w-full max-w-[750px] min-h-[1000px]"
                    style={{
                      padding: '1in 1in',
                      fontFamily: 'Calibri, "Segoe UI", Arial, sans-serif'
                    }}
                  >
                    {!editor?.getText() && status !== 'optimizing' && (
                      <div className="flex flex-col items-center justify-center h-64 text-center">
                        <div className="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center mb-4">
                          <Sparkles size={28} className="text-slate-300" />
                        </div>
                        <h3 className="text-slate-400 font-medium text-sm">Your optimized resume will appear here</h3>
                        <p className="text-slate-300 text-xs mt-1 max-w-xs">
                          Paste a job description, upload your resume, and click Optimize
                        </p>
                      </div>
                    )}

                    {status === 'optimizing' && (
                      <div className="flex flex-col items-center justify-center h-64 gap-4">
                        <Loader2 size={36} className="animate-spin text-blue-400" />
                        <div className="text-center">
                          <p className="text-slate-600 font-medium text-sm">Analyzing & Optimizing...</p>
                          <p className="text-slate-400 text-xs mt-1">Extracting JD requirements • Matching skills • Enhancing bullets</p>
                        </div>
                        <div className="w-48 bg-slate-100 rounded-full h-1.5 overflow-hidden">
                          <div className="bg-blue-500 h-full rounded-full animate-pulse" style={{ width: '65%' }} />
                        </div>
                      </div>
                    )}

                    <EditorContent editor={editor} />
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'compare' && (
              <div className="flex-1 overflow-y-auto p-4">
                <div className="grid grid-cols-2 gap-4 h-full">
                  <div className="flex flex-col">
                    <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2 flex items-center gap-1.5">
                      <XCircle size={12} className="text-red-400" /> Original
                    </div>
                    <div className="flex-1 border border-slate-200 rounded-xl p-4 text-xs text-slate-600 overflow-y-auto bg-red-50/30"
                      dangerouslySetInnerHTML={{ __html: originalHtml }}
                    />
                  </div>
                  <div className="flex flex-col">
                    <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2 flex items-center gap-1.5">
                      <CheckCircle size={12} className="text-emerald-400" /> Optimized
                    </div>
                    <div className="flex-1 border border-emerald-200 rounded-xl p-4 text-xs text-slate-600 overflow-y-auto bg-emerald-50/30 tiptap-resume-editor"
                      dangerouslySetInnerHTML={{ __html: editor?.getHTML() || '' }}
                    />
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  )
}
