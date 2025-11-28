import ollama
import json
from typing import Dict, Any

# 커스텀 모델 이름을 상수로 정의 (필요에 따라 변경 용이)
CUSTOM_MODEL_NAME = 'diary-analyzer'

def analyze_diary_with_custom_model(diary_text: str) -> Dict[str, Any]:
    """
    Ollama에 빌드된 'diary-analyzer' 커스텀 모델을 호출하여 일기를 분석합니다.
    """
    
    # Modelfile에 시스템 역할과 JSON 스키마가 정의되어 있으므로,
    # 사용자 프롬프트는 분석할 텍스트만 전달합니다.
    prompt = f"다음 일기를 분석하고 정의된 JSON 스키마에 따라 결과를 반환하세요. 일기 내용: \"{diary_text}\""

    print(f"모델({CUSTOM_MODEL_NAME})에 일기 분석 요청 중...")
    
    try:
        response = ollama.chat(
            model=CUSTOM_MODEL_NAME,
            messages=[
                # Modelfile 덕분에 별도로 'role': 'system'을 지정하지 않아도 됩니다.
                {'role': 'user', 'content': prompt},
            ]
        )
        
        # 모델 응답에서 JSON 문자열 추출 및 파싱
        content = response['message']['content'].strip()
        
        # Ollama는 보통 JSON만 반환하도록 잘 학습되지만, 
        # 혹시 '```json ... ```' 블록이 포함될 경우를 대비한 처리
        if content.startswith("```json"):
            # '```json'과 '```' 태그 제거
            content = content.replace("```json", "", 1)
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

        # JSON 문자열을 파이썬 딕셔너리로 변환
        return json.loads(content)
    
    except json.JSONDecodeError as e:
        print("\n--- JSON 파싱 오류 발생 ---")
        print(f"오류: {e}")
        # 오류 발생 시 디버깅을 위해 모델이 반환한 원본 텍스트를 출력
        print(f"모델이 반환한 원본 텍스트:\n{response.get('message', {}).get('content', '원본 응답 없음')}")
        return {"error": "분석 결과를 JSON으로 변환하지 못했습니다."}
        
    except Exception as e:
        print(f"\n--- Ollama 통신 오류 발생 ---")
        print(f"오류: {e}")
        return {"error": "Ollama 서버와 통신할 수 없습니다. 서버가 실행 중인지 확인하세요."}