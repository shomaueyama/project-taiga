from taiga.config import get_settings


def main() -> None:
    settings = get_settings()
    if settings.local_auth_enabled and settings.app_env != "local":
        raise SystemExit("LOCAL_AUTH_ENABLED can only be true in local APP_ENV")
    print("Validation passed.")


if __name__ == "__main__":
    main()
