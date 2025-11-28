import json
from DiaryVomit.src.ai.ollama_analyzer import analyze_diary_with_custom_model


def run_tests():
    # 긍정적인 일기 테스트
    diary_positive = "오랜만에 친구들과 만나서 실컷 웃고 맛있는 것도 먹었다. 그동안 스트레스가 많았는데, 싹 날아가는 기분이다. 내일도 오늘처럼 행복했으면 좋겠다."
    
    analysis_result_1 = analyze_diary_with_custom_model(diary_positive)
    
    print("\n====================================")
    print("1. 긍정 일기 분석 결과:")
    # JSON 형식으로 출력
    print(json.dumps(analysis_result_1, indent=4, ensure_ascii=False))
    print("====================================\n")


    # 부정적인 일기 테스트
    diary_negative = "오늘 아침부터 중요한 보고서 작업에 실수가 많아서 상사에게 크게 질책을 받았다. 하루 종일 기분이 침체되었고, 내가 일을 제대로 하고 있는 건지 자신감마저 떨어졌다. 다음 주에는 꼭 만회해야 할 텐데 불안하다."
    
    analysis_result_2 = analyze_diary_with_custom_model(diary_negative)
    
    print("\n====================================")
    print("2. 부정 일기 분석 결과:")
    # JSON 형식으로 출력
    print(json.dumps(analysis_result_2, indent=4, ensure_ascii=False))
    print("====================================\n")

if __name__ == "__main__":
    run_tests()