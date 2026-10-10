from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """환경변수/.env 에서 읽는 설정. 비밀값은 코드에 두지 않는다.

    아래 속도·우회계수는 baseline 알고리즘용 "임시 가정치"다. 실측 데이터가 쌓이면
    (Phase 3) 학습 모델/실제 경로 질의로 대체한다.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"

    # 인지적 이동취약자 보행 속도 가정 (일반 성인 ~1.3 m/s 보다 느리게 잡음)
    walk_speed_mps: float = 0.9
    # 직선거리 → 실제 보행거리 보정 (골목·횡단보도 우회)
    walk_detour_factor: float = 1.2
    # 도심 차량 평균 속도 가정 (km/h)
    vehicle_speed_kmh: float = 25.0
    # 직선거리 → 실제 도로거리 보정 (일방통행·유턴 등)
    vehicle_detour_factor: float = 1.4

    # 대기시간 baseline 의 기준값(분). 공공데이터 학습 전까지 쓰는 가정치
    base_wait_min: float = 30.0


settings = Settings()
