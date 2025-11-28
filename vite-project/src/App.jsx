import React, { useState } from 'react';

function App() {
  const [authStatus, setAuthStatus] = useState('대기 중');
  const [analysisResult, setAnalysisResult] = useState('결과가 여기에 표시됩니다.');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [diaryText, setDiaryText] = useState('');

  // --- 유틸리티 함수 ---
  const makeApiRequest = async (endpoint, data) => {
    try {
      // 🚀 프록시 설정을 위해 상대 경로(/api/...) 사용
      const response = await fetch(`/api/${endpoint}`, { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      return await response.json();
    } catch (error) {
      console.error('Fetch Error:', error);
      return { success: false, message: `서버 통신 실패: ${error.message}` };
    }
  };

  // --- 인증 함수 ---
  const handleRegister = async () => {
    const result = await makeApiRequest('register', { username, password });
    setAuthStatus(result.success ? `✅ 성공: ${result.message}` : `❌ 실패: ${result.message}`);
  };

  const handleLogin = async () => {
    const result = await makeApiRequest('login', { username, password });
    if (result.success) {
      setAuthStatus(`✅ 로그인 성공: ${result.username}님 (ID: ${result.user_id})`);
    } else {
      setAuthStatus(`❌ 로그인 실패: ${result.message}`);
    }
  };

  // --- 분석 함수 ---
  const handleAnalyze = async () => {
    if (!diaryText.trim()) {
      alert("일기 내용을 입력해주세요.");
      return;
    }
    setAnalysisResult("분석 중...");
    
    const result = await makeApiRequest('analyze_diary', { diary_text: diaryText });
    
    if (result.success) {
      setAnalysisResult(JSON.stringify(result.analysis, null, 2));
    } else {
      setAnalysisResult(`분석 오류: ${result.message}\n${result.details || ''}`);
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>📝 Vite + Flask API 테스트</h1>

      {/* 1. 인증 구역 */}
      <div style={{ border: '1px solid #ccc', padding: '15px', marginBottom: '20px' }}>
        <h2>🔑 인증 테스트</h2>
        <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="사용자 이름" />
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="비밀번호" />
        <button onClick={handleRegister} style={{ marginLeft: '10px' }}>회원가입</button>
        <button onClick={handleLogin}>로그인</button>
        <p>상태: <span style={{ fontWeight: 'bold' }}>{authStatus}</span></p>
      </div>

      {/* 2. 분석 구역 */}
      <div style={{ border: '1px solid #ccc', padding: '15px' }}>
        <h2>📊 일기 분석 테스트 (Ollama)</h2>
        <textarea 
          value={diaryText} 
          onChange={(e) => setDiaryText(e.target.value)} 
          placeholder="오늘 일기 내용을 입력하세요..." 
          style={{ width: '100%', height: '100px', marginTop: '10px' }}
        />
        <button onClick={handleAnalyze}>분석 요청 (/api/analyze_diary)</button>
        <h3>분석 결과 (JSON)</h3>
        <pre style={{ backgroundColor: '#eee', padding: '15px' }}>{analysisResult}</pre>
      </div>
    </div>
  );
}

export default App;