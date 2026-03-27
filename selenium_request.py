from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


def is_challenge_complete(driver):
    """检测挑战是否完成的综合方法"""
    # 检查挑战容器
    try:
        challenge_container = driver.find_element(By.ID, "challenge-container")
        if challenge_container.is_displayed():
            # 挑战仍在进行
            return False
    except:
        pass

    # 检查挑战脚本是否仍在运行
    try:
        if driver.execute_script('return typeof AwsWafIntegration !== "undefined"'):
            # 挑战仍在进行
            return False
    except:
        pass

    # 检查挑战脚本是否消失
    page_source = driver.page_source.lower()
    if "challenge.js" not in page_source:
        # 挑战可能已完成
        return True

    # 检查页面标题
    title = driver.title.lower()
    if title and "aws waf" not in title and "challenge" not in title:
        # 挑战完成
        return True

    return False


def bypass_aws_waf(url):
    """使用 Selenium 可靠地处理 AWS WAF 挑战并获取页面内容"""
    # 配置 Chrome 选项
    chrome_options = Options()

    # 无头模式配置
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # 模拟真实浏览器指纹
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
    chrome_options.add_argument("--window-size=1920,1080")

    # 禁用自动化检测标志
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')

    # 创建持久化用户数据目录（可选）
    # user_data_dir = os.path.join(os.getcwd(), "chrome_profile")
    # chrome_options.add_argument(f"user-data-dir={user_data_dir}")

    # 创建 WebDriver
    chrome_service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

    try:
        # 执行 JavaScript 修改 navigator 属性
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        # 访问目标 URL
        driver.get(url)
        print(f"初始页面标题: {driver.title}")

        # 等待挑战完成 - 使用显式等待
        try:
            WebDriverWait(driver, 60).until(
                lambda d: is_challenge_complete(d)
            )
            print("AWS WAF 挑战确认完成")
        except Exception as e:
            print(f"等待挑战完成超时或出错: {e}")

        # 获取最终页面内容
        final_html = driver.page_source

        # 验证内容是否有效
        if len(final_html) < 1000:
            print("警告: 获取的内容过短，可能未完全通过挑战")
        elif "challenge.js" in final_html.lower():
            print("警告: 挑战脚本仍在页面中，可能未完全通过挑战")

        return final_html

    except Exception as e:
        print(f"处理过程中出错: {e}")
        # 出错时返回当前页面内容
        return driver.page_source if 'driver' in locals() else None

    finally:
        try:
            driver.quit()
        except:
            pass
