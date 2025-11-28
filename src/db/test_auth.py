from user_manager import register_user, login_user

def run_auth_test():
    # 테스트에 사용할 고정 사용자 정보
    test_username = "diary_master"
    test_password = "my_strong_password_123"
    
    print("====================================")
    print("      🔑 사용자 인증 테스트 시작     ")
    print("====================================")
    
    # --- 1. 회원가입 시도 (DB에 사용자 등록) ---
    print("\n[1. 회원가입 시도]")
    register_user(test_username, test_password)
    
    # --- 2. 중복 회원가입 시도 (IntegrityError 확인) ---
    print("\n[2. 중복 회원가입 시도 (실패 예상)]")
    register_user(test_username, test_password) 

    # --- 3. 로그인 성공 테스트 ---
    print("\n[3. 로그인 성공 시도]")
    user_data = login_user(test_username, test_password)
    if user_data:
        # 로그인 성공 시 반환되는 사용자 데이터 확인
        print(f"   조회된 사용자 ID: {user_data['id']}, 이름: {user_data['username']}")
        
    # --- 4. 비밀번호 오류 로그인 테스트 ---
    print("\n[4. 비밀번호 오류 로그인 시도 (실패 예상)]")
    login_user(test_username, "wrong_password")
    
    # --- 5. 존재하지 않는 사용자 로그인 테스트 ---
    print("\n[5. 존재하지 않는 사용자 로그인 시도 (실패 예상)]")
    login_user("ghost_user", test_password)
    
    print("\n====================================")
    print("      ✅ 사용자 인증 테스트 완료     ")
    print("====================================")

if __name__ == "__main__":
    run_auth_test()