import { useState } from 'react'
import './App.css'

function App() {
  const [currentView, setCurrentView] = useState('menu')
  const [diaryText, setDiaryText] = useState('')
  const [analysisResult, setAnalysisResult] = useState(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [diaries, setDiaries] = useState([])

  const MainMenu = () => (
    <div className="main-menu">
      <header className="header">
        <h1 className="title">DiaryVomit</h1>
        <p className="subtitle">감정을 기록하고, 마음을 분석하는 일기장</p>
      </header>
      <div className="menu-container">
        <MenuButton 
          emoji="✍️" 
          title="일기 작성"
          description="새로운 일기를 작성하고 감정을 분석합니다"
          onClick={() => setCurrentView('write')}
        />
        <MenuButton 
          emoji="📚" 
          title="작성된 일기 목록"
          description="지금까지 작성한 일기를 확인합니다"
          onClick={() => setCurrentView('list')}
        />
        <MenuButton 
          emoji="📊" 
          title="주간별/월간별 감정 분석 차트"
          description="감정 변화를 차트로 확인합니다"
          onClick={() => setCurrentView('chart')}
        />
      </div>
    </div>
  )

  const MenuButton = ({ emoji, title, description, onClick }) => (
    <div className="menu-button-container">
      <button className="menu-button" onClick={onClick}>
        <span className="menu-button-text">{emoji}  {title}</span>
      </button>
      <p className="menu-description">{description}</p>
    </div>
  )

  const WriteDiary = () => (
    <div className="write-diary">
      <header className="header">
        <button className="back-button" onClick={() => setCurrentView('menu')}>
          ← 메인 메뉴
        </button>
        <h1 className="page-title">📝 일기 작성</h1>
      </header>
      <div className="content-container">
        <p className="date-label">📅 {new Date().toLocaleDateString('ko-KR', { 
          year: 'numeric', 
          month: 'long', 
          day: 'numeric', 
          weekday: 'long' 
        })}</p>
        
        <div className="input-shadow">
          <textarea
            className="diary-input"
            placeholder="여기에 일기를 작성해주세요..."
            value={diaryText}
            onChange={(e) => setDiaryText(e.target.value)}
          />
        </div>

        <div className="button-group">
          <button className="action-button primary" onClick={handleAnalyze}>
            🔍  감정 분석하기
          </button>
          <button className="action-button secondary" onClick={handleSave}>
            💾  저장하기
          </button>
        </div>

        {isAnalyzing && (
          <p className="loading-text">⏳ 분석 중입니다... 잠시만 기다려주세요.</p>
        )}

        <div className="result-shadow">
          <div className="result-container">
            <h3 className="result-title">📊 분석 결과</h3>
            <div className="result-content">
              {analysisResult ? (
                <AnalysisResult result={analysisResult} />
              ) : (
                <p className="placeholder-text">분석 결과가 여기에 표시됩니다</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )

  const AnalysisResult = ({ result }) => (
    <div className="analysis-result">
      <div className="result-item">
        <span className="result-label">🎭 주된 감정:</span>
        <span className="result-value">{result.primary_emotion}</span>
      </div>
      <div className="result-item">
        <span className="result-label">💫 보조 감정:</span>
        <span className="result-value">{result.secondary_emotions?.join(', ')}</span>
      </div>
      <div className="result-item">
        <span className="result-label">📊 감정 강도:</span>
        <span className="result-value">{result.emotion_intensity}/100</span>
        <div className="intensity-bar">
          <div 
            className="intensity-fill" 
            style={{ width: `${result.emotion_intensity}%` }}
          />
        </div>
      </div>
      <div className="result-item">
        <span className="result-label">🎯 긍부정 점수:</span>
        <span className="result-value">{result.analysis_score > 0 ? '+' : ''}{result.analysis_score}/10</span>
      </div>
      <div className="result-item">
        <span className="result-label">🔑 핵심 키워드:</span>
        <span className="result-value">{result.keywords?.join(', ')}</span>
      </div>
      <div className="result-item">
        <span className="result-label">📝 요약:</span>
        <p className="result-summary">{result.summary}</p>
      </div>
    </div>
  )

  const DiaryList = () => (
    <div className="diary-list">
      <header className="header">
        <button className="back-button" onClick={() => setCurrentView('menu')}>
          ← 메인 메뉴
        </button>
        <h1 className="page-title">📚 작성된 일기 목록</h1>
      </header>
      <div className="list-container">
        {diaries.length === 0 ? (
          <div className="empty-state">
            <p>아직 작성된 일기가 없습니다.</p>
            <p>일기를 작성하고 감정을 기록해보세요!</p>
          </div>
        ) : (
          diaries.map((diary, index) => (
            <div key={index} className="diary-card">
              <p className="diary-date">📅 {diary.date}</p>
              <p className="diary-preview">{diary.content.substring(0, 150)}...</p>
              {diary.analysis && (
                <span className="emotion-tag">🎭 {diary.analysis.primary_emotion}</span>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )

  const EmotionChart = () => (
    <div className="emotion-chart">
      <header className="header">
        <button className="back-button" onClick={() => setCurrentView('menu')}>
          ← 메인 메뉴
        </button>
        <h1 className="page-title">📊 감정 분석 차트</h1>
      </header>
      <div className="chart-container">
        <div className="coming-soon">
          <h2>📊 감정 분석 차트</h2>
          <p>주간별/월간별 감정 통계 기능은</p>
          <p>곧 제공될 예정입니다.</p>
          <br />
          <p>지속적으로 일기를 작성하고</p>
          <p>감정을 기록해주세요!</p>
        </div>
      </div>
    </div>
  )

  const handleAnalyze = () => {
    if (!diaryText.trim()) {
      alert('일기를 작성해주세요!')
      return
    }
    
    setIsAnalyzing(true)
    // 시뮬레이션 데이터 (실제로는 API 호출)
    setTimeout(() => {
      setAnalysisResult({
        primary_emotion: '기쁨',
        secondary_emotions: ['만족', '희망', '성취감'],
        emotion_intensity: 75,
        analysis_score: 8,
        keywords: ['친구', '즐거움', '행복'],
        emotion_tags: ['긍정', '사교', '휴식'],
        summary: '친구들과의 즐거운 시간을 통해 긍정적인 감정을 경험한 하루입니다.'
      })
      setIsAnalyzing(false)
    }, 2000)
  }

  const handleSave = () => {
    if (!diaryText.trim()) {
      alert('일기를 작성해주세요!')
      return
    }

    const newDiary = {
      date: new Date().toLocaleString('ko-KR'),
      content: diaryText,
      analysis: analysisResult
    }

    setDiaries([...diaries, newDiary])
    alert('일기가 저장되었습니다!')
    setDiaryText('')
    setAnalysisResult(null)
  }

  return (
    <div className="app">
      {currentView === 'menu' && <MainMenu />}
      {currentView === 'write' && <WriteDiary />}
      {currentView === 'list' && <DiaryList />}
      {currentView === 'chart' && <EmotionChart />}
    </div>
  )
}

export default App
