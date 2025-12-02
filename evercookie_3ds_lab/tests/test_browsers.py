import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By

DOMAIN_URL = "http://domain1.local:8000"
IDENTSERVER_URL = "http://identserver.local:8001"


def save_test_result(browser: str, stand: str, uid1: str, uid2: str) -> None:
    """
    Отправляет результат теста на identserver, чтобы потом
    показывать красивую таблицу и график.
    """
    requests.post(f"{IDENTSERVER_URL}/save-test-result", json={
        "browser": browser,
        "stand": stand,
        "uid1": uid1,
        "uid2": uid2,
    })


def wait_for_uid(driver, path: str, timeout: float = 15.0) -> str:
    """
    Открывает страницу стенда и ждёт, пока UID перестанет быть 'жду…'.
    """
    driver.get(f"{DOMAIN_URL}{path}")
    deadline = time.time() + timeout
    last = ""
    while time.time() < deadline:
        span = driver.find_element(By.ID, "uid-value")
        text = span.text.strip()
        last = text
        if text and text != "жду…":
            return text
        time.sleep(0.3)
    return last


def test_safari_cross_and_proxy():
    driver = webdriver.Safari()
    try:
        uid1_cross = wait_for_uid(driver, "/test-cross")
        uid1_proxy = wait_for_uid(driver, "/test-proxy")

        driver.quit()
        time.sleep(2)

        driver = webdriver.Safari()

        uid2_cross = wait_for_uid(driver, "/test-cross")
        uid2_proxy = wait_for_uid(driver, "/test-proxy")

        print("Safari CROSS:", uid1_cross, "=>", uid2_cross)
        print("Safari PROXY:", uid1_proxy, "=>", uid2_proxy)

        save_test_result("Safari", "cross", uid1_cross, uid2_cross)
        save_test_result("Safari", "proxy", uid1_proxy, uid2_proxy)

    finally:
        driver.quit()


def test_chrome_cross_and_proxy():
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options=options)
    try:
        uid1_cross = wait_for_uid(driver, "/test-cross")
        uid1_proxy = wait_for_uid(driver, "/test-proxy")

        driver.quit()
        time.sleep(2)

        driver = webdriver.Chrome(options=options)

        uid2_cross = wait_for_uid(driver, "/test-cross")
        uid2_proxy = wait_for_uid(driver, "/test-proxy")

        print("Chrome CROSS:", uid1_cross, "=>", uid2_cross)
        print("Chrome PROXY:", uid1_proxy, "=>", uid2_proxy)

        save_test_result("Chrome", "cross", uid1_cross, uid2_cross)
        save_test_result("Chrome", "proxy", uid1_proxy, uid2_proxy)

    finally:
        driver.quit()
