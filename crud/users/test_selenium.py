from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException  # ייבוא של TimeoutException
import unittest

class UserIntegrationTest(unittest.TestCase):

    def setUp(self):
        self.driver = webdriver.Chrome()
        self.driver.get("http://127.0.0.1:8000/users/login/")

    def test_successful_login(self):
        driver = self.driver
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "id_username")))

        # מילוי טופס ההתחברות
        username = driver.find_element(By.ID, "id_username")
        username.send_keys("testuser")

        password = driver.find_element(By.ID, "id_password")
        password.send_keys("password123")

        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        # וידוא שהמשתמש הגיע לדף הבית
        try:
            WebDriverWait(driver, 30).until(EC.title_contains("Dashboard"))
            self.assertIn("Dashboard", driver.title, "Failed to navigate to dashboard after login")
        except TimeoutException:
            self.fail("Failed to navigate to dashboard after login")

    def test_navigation_to_project_list(self):
        self.test_successful_login()  # התחברות מצליחה כדי לגשת לדף הדשבורד

        driver = self.driver
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.LINK_TEXT, "Projects")))
        driver.find_element(By.LINK_TEXT, "Projects").click()

        # וידוא שהמשתמש הגיע לדף רשימת הפרויקטים
        try:
            WebDriverWait(driver, 30).until(EC.title_contains("Project List"))
            self.assertIn("Project List", driver.title, "Failed to navigate to project list")
        except TimeoutException:
            self.fail("Failed to navigate to project list")

    def test_view_project_details(self):
        self.test_navigation_to_project_list()  # מעבר לרשימת פרויקטים

        driver = self.driver
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.LINK_TEXT, "Project Name")))  # החלף בשם הפרויקט האמיתי
        driver.find_element(By.LINK_TEXT, "Project Name").click()

        # וידוא שהמשתמש הגיע לדף הפרטים של הפרויקט
        try:
            WebDriverWait(driver, 30).until(EC.title_contains("Project Details"))
            self.assertIn("Project Details", driver.title, "Failed to navigate to project details")
        except TimeoutException:
            self.fail("Failed to navigate to project details")

    def tearDown(self):
        self.driver.quit()

if __name__ == "__main__":
    unittest.main()
