import json
# 이미 정의된 핵심 분석 함수를 import 합니다.
from ollama_analyzer import analyze_diary_with_custom_model

def analyze_user_diary():
    """
    사용자의 콘솔 입력을 받아 Mistral 모델로 일기를 분석합니다.
    """
    print("\n=============================================")
    print("      ✍️ 사용자 일기 입력 및 분석 프로그램     ")
    print("=============================================")
    print("분석할 일기 내용을 입력하세요 (입력 후 Enter):")
    
    # 사용자로부터 일기 내용을 입력받습니다.
    user_diary_text = input(">> ")
    
    if not user_diary_text.strip():
        print("경고: 입력된 내용이 없습니다. 프로그램을 종료합니다.")
        return

    # Ollama 분석 함수를 호출합니다.
    analysis_result = analyze_diary_with_custom_model(user_diary_text)

    print("\n---------------------------------------------")
    print("      📊 Mistral 모델 분석 결과      ")
    print("---------------------------------------------")
    
    # 결과를 보기 쉽게 출력합니다.
    if "error" in analysis_result:
        print(f"오류: {analysis_result['error']}")
    else:
        print(f"✅ 주된 감정: {analysis_result.get('emotion', '분석 불가')}")
        print(f"🔑 핵심 키워드: {', '.join(analysis_result.get('keywords', []))}")
        print(f"⭐ 긍정/부정 점수: {analysis_result.get('analysis_score', 'N/A')}")
        
        print("\n[전체 JSON 출력]")
        print(json.dumps(analysis_result, indent=4, ensure_ascii=False))
        
    print("=============================================")


if __name__ == "__main__":
    # Ollama 서버가 켜져 있는지 확인 후 실행하세요.
    analyze_user_diary()