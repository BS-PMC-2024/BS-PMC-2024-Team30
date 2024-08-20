from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.common.exceptions import TimeoutException


def test_user_registration():
    driver = webdriver.Chrome()
    driver.get("http://127.0.0.1:8000/users/register/")
    print("Navigated to the registration page.")

    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "id_username")))
        print("Registration form loaded successfully.")

        # מילוי טופס ההרשמה
        username = driver.find_element(By.ID, "id_username")
        username.send_keys("testuser")
        print("Entered username.")

        email = driver.find_element(By.ID, "id_email")
        email.send_keys("testuser@example.com")
        print("Entered email.")

        password1 = driver.find_element(By.ID, "id_password1")
        password1.send_keys("password123")
        print("Entered password.")

        password2 = driver.find_element(By.ID, "id_password2")
        password2.send_keys("password123")
        print("Confirmed password.")

        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        print("Submitted the registration form.")

        # בדיקת קוד אימות רק אם האלמנט קיים
        try:
            verification_code = WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, "id_code")))
            verification_code.send_keys("your-verification-code")  # החלף בקוד האמיתי
            driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            print("Entered verification code and submitted.")

            WebDriverWait(driver, 30).until(EC.title_contains("Home"))
            print("Registration test passed! Navigated to the home page.")
        except TimeoutException:
            # האלמנט id_code לא נמצא, ממשיכים לבדוק אם הגענו לדף הבית
            try:
                WebDriverWait(driver, 30).until(EC.title_contains("Home"))
                print("Registration test passed! Navigated to the home page without verification.")
            except TimeoutException:
                print("Registration test failed! Did not navigate to the home page.")
    
    except Exception as e:
        print(f"Test encountered an error: {e}")
    
    finally:
        driver.quit()
        print("Closed the browser.")

# הפעלת הבדיקה
test_user_registration()


def test_user_login():
    driver = webdriver.Chrome()
    driver.get("http://127.0.0.1:8000/users/login/")

    # חפש את שדה המשתמש והכנס את השם משתמש
    username_input = driver.find_element(By.NAME, 'username')
    username_input.send_keys('sharon111')

    # חפש את שדה הסיסמה והכנס את הסיסמה
    password_input = driver.find_element(By.NAME, 'password')
    password_input.send_keys('password')

    # לחץ על כפתור ההתחברות
    login_button = driver.find_element(By.XPATH, '//button[@type="submit"]')
    login_button.click()

    # וודא שההתחברות הצליחה על ידי בדיקת קיומו של האלמנט "ברוך הבא"
    try:
        welcome_text = WebDriverWait(driver, 300).until(
            EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Welcome')]"))
        )
        print("Login test passed!")
    except:
        print("Login test failed!")
    
    driver.quit()

test_user_login()


def test_create_project():
    driver = webdriver.Chrome()
    driver.get("http://127.0.0.1:8000/users/login/")

    # התחברות כמנהל
    print("Attempting to log in as manager...")
    username_input = driver.find_element(By.NAME, 'username')
    username_input.send_keys('manageruser')
    password_input = driver.find_element(By.NAME, 'password')
    password_input.send_keys('password')
    login_button = driver.find_element(By.XPATH, '//button[@type="submit"]')
    login_button.click()
    print("Logged in successfully.")

    # נווט לדף הבית של המנהל
    print("Navigating to manager home page...")
    driver.get("http://127.0.0.1:8000/users/manager/")

    # נוודא שהדף נטען לגמרי
    WebDriverWait(driver, 120).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
   

    # חפש את הכפתור 'Create Project'
    try:
        create_project_button = WebDriverWait(driver, 120).until(
            EC.presence_of_element_located((By.XPATH, '//button[text()="Create Project"]'))
        )
        print("Create Project button found.")
    except Exception as e:
        print(f"Failed to find 'Create Project' button. Error: {e}")
        driver.quit()
        return

    # מילוי הטופס ליצירת פרויקט חדש
    print("Filling out the form to create a new project...")
    project_name_input = driver.find_element(By.NAME, 'name')
    project_name_input.send_keys('Test Project1')
    project_description_input = driver.find_element(By.NAME, 'description')
    project_description_input.send_keys('This is a test project1.')
    submit_button = driver.find_element(By.XPATH, '//button[@type="submit"]')
    submit_button.click()
    print("Form submitted.")

    # וודא שהפרויקט נוצר
    try:
        project_link = WebDriverWait(driver, 120).until(
            EC.presence_of_element_located((By.LINK_TEXT, 'Test Project1'))
        )
        print("Project creation test passed! Project found in the list.")
    except:
        print("Project creation test failed! Project not found in the list.")

    driver.quit()


def test_navigate_to_create_task_page():
    driver = webdriver.Chrome()

    try:
        driver.get("http://127.0.0.1:8000/users/login/")
        print("Attempting to log in as manager...")

        username_input = driver.find_element(By.NAME, 'username')
        username_input.send_keys('sharon111')
        password_input = driver.find_element(By.NAME, 'password')
        password_input.send_keys('password')
        login_button = driver.find_element(By.XPATH, '//button[@type="submit"]')
        login_button.click()
        print("Logged in successfully.")

        WebDriverWait(driver, 120).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        print("Navigating to manager home page...")

        # Navigate to the manager home page
        driver.get("http://127.0.0.1:8000/users/manager/")

        time.sleep(60)  # המתנה כדי לוודא שהדף נטען במלואו

        print("Navigating to project page...")
        driver.get("http://127.0.0.1:8000/users/project/7/")  # וודא שהפרויקט עם ID=7 קיים
        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        
        time.sleep(10)  # המתנה נוספת לטעינת הדף במלואו

        print("Navigating to create task page...")
        try:
            create_task_link = WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.LINK_TEXT, 'Create Task'))
            )
            create_task_link.click()
            print("Navigated to Create Task page successfully.")
        except Exception as e:
            print(f"Failed to navigate to Create Task page. Error: {e}")

    except Exception as e:
        print(f"Failed to complete the test. Error: {e}")

    finally:
        driver.quit()

# הפעלת הבדיקה
test_navigate_to_create_task_page()