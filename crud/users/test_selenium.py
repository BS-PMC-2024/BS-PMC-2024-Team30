from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException  # ייבוא של TimeoutException
import unittest

class UserRegistrationTest(unittest.TestCase):

    def setUp(self):
        self.driver = webdriver.Chrome()
        self.driver.get("http://127.0.0.1:8000/users/register/")

    def test_username_field(self):
        driver = self.driver
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "id_username")))
        username = driver.find_element(By.ID, "id_username")
        self.assertIsNotNone(username, "Username field is not found")

    def test_email_field(self):
        driver = self.driver
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "id_email")))
        email = driver.find_element(By.ID, "id_email")
        self.assertIsNotNone(email, "Email field is not found")

    def test_password_fields(self):
        driver = self.driver
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "id_password1")))
        password1 = driver.find_element(By.ID, "id_password1")
        password2 = driver.find_element(By.ID, "id_password2")
        self.assertIsNotNone(password1, "Password1 field is not found")
        self.assertIsNotNone(password2, "Password2 field is not found")

    def test_successful_registration(self):
        driver = self.driver
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "id_username")))

        # מילוי טופס ההרשמה
        username = driver.find_element(By.ID, "id_username")
        username.send_keys("testuser")

        email = driver.find_element(By.ID, "id_email")
        email.send_keys("testuser@example.com")

        password1 = driver.find_element(By.ID, "id_password1")
        password1.send_keys("password123")

        password2 = driver.find_element(By.ID, "id_password2")
        password2.send_keys("password123")

        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        # בדיקת קוד אימות רק אם האלמנט קיים
        try:
            verification_code = WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, "id_code")))
            verification_code.send_keys("your-verification-code")  # החלף בקוד האמיתי
            driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

            WebDriverWait(driver, 30).until(EC.title_contains("Home"))
            self.assertIn("Home", driver.title, "Did not navigate to home page after registration")
        except TimeoutException:
            # האלמנט id_code לא נמצא, ממשיכים לבדוק אם הגענו לדף הבית
            try:
                WebDriverWait(driver, 30).until(EC.title_contains("Home"))
                self.assertIn("Home", driver.title, "Did not navigate to home page after registration")
            except TimeoutException:
                self.fail("Failed to navigate to home page after registration")

    def tearDown(self):
        self.driver.quit()

if __name__ == "__main__":
    unittest.main()
