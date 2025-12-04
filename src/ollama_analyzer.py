import ollama
import json
import re
from typing import Dict, Any

# 커스텀 모델 이름을 상수로 정의
CUSTOM_MODEL_NAME = 'diary-analyzer'


def analyze_diary_with_custom_model(diary_text: str) -> Dict[str, Any]:
    """
    Ollama에 빌드된 'diary-analyzer' 커스텀 모델을 호출하여 일기를 분석합니다.
    JSON만 정확히 추출하도록 안정성 향상 버전.
    """

    prompt = f"다음 일기를 분석하고 JSON 객체만 반환하세요. 일기 내용: \"{diary_text}\""

    print(f"모델({CUSTOM_MODEL_NAME})에 일기 분석 요청 중...")

    try:
        # Ollama 호출
        response = ollama.chat(
            model=CUSTOM_MODEL_NAME,
            messages=[
                {'role': 'user', 'content': prompt},
            ]
        )

        raw = response['message']['content']

        # 공백 제거
        cleaned = raw.strip()

        # ```json 시작, ``` 끝 제거
        cleaned = cleaned.replace("```json", "").replace("```", "").strip()

        # JSON 블록만 정규식으로 추출
        match = re.search(r"\{[\s\S]*\}", cleaned)
        if not match:
            raise ValueError("JSON 블록을 찾을 수 없습니다.")

        json_text = match.group(0)

        # JSON 파싱
        return json.loads(json_text)

    except Exception as e:
        print("\n--- JSON 파싱 오류 발생 ---")
        print(f"오류: {e}")
        print(f"\n--- 모델이 반환한 원본 텍스트 ---\n{raw}")
        return {"error": "JSON 파싱 실패"}
