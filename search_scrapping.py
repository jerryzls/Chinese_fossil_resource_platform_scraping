# 2025.6.29
# 爬取国家岩矿化石标本资源共享平台的图片，以资源名称命名图片
# 需要修改的参数：url，img_folder

from selenium.webdriver.common.by import By
from time import sleep
import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import os
import requests

# 国家岩矿化石标本网站（带搜索）地址
url = "http://www.nimrf.net.cn/yk/zhcx"

# 用于记录每个 resource_name 出现的次数
resource_name_counter = {}

# 配置 Chrome 选项
chrome_options = Options()
chrome_options.add_argument("--disable-popup-blocking")  # 禁用弹出窗口阻止功能

# 创建 Chrome 浏览器实例并传入选项
browser = uc.Chrome(options=chrome_options)
# 打开网页
browser.get(url=url)
browser.set_window_size(920, 480)  # 改变页面大小

# 等待一段时间，避免访问过快
sleep(5)

# 选择搜索框
searching = browser.find_element(By.XPATH,
                                 '//input[@type="text" and @class="el-input__inner" and @placeholder="    请输入产地"]')
# 输入搜索关键词
searching.send_keys("黄半吉")

# 点击搜索按钮
search_button = browser.find_element(By.XPATH,
                                     '//button[@class="el-button el-button--primary el-button--mini" and @type="button"]')
search_button.click()

# 等待搜索结果加载
sleep(5)

# 确保图片保存文件夹存在
img_folder = 'extracted_images'
os.makedirs(img_folder, exist_ok=True)

try:
    while True:
        # 查找所有符合条件的 <tr> 元素
        tr_elements = WebDriverWait(browser, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tr.el-table__row, tr.el-table__row.el-table__row--striped'))
        )

        for tr in tr_elements:
            try:
                # 查找 <a> 标签
                a_tag = tr.find_element(By.CSS_SELECTOR, 'td.el-table_1_column_2.is-center.el-table__cell div.cell.el-tooltip a')
                link = a_tag.get_attribute('href')

                if link:
                    # 记录当前窗口句柄
                    original_window = browser.current_window_handle
                    # 打开新标签页
                    browser.execute_script("window.open('', '_blank');")
                    sleep(2)
                    # 切换到新窗口
                    browser.switch_to.window([window for window in browser.window_handles if window != original_window][0])

                    browser.get(link)

                    # 等待新页面加载
                    sleep(5)

                    # 提取资源名称
                    try:
                        resource_name_element = WebDriverWait(browser, 10).until(
                            EC.presence_of_element_located((By.XPATH,
                                                            '//div[@class="el-col el-col-4" and @data-v-c58f6974]//label[text()=" 资源名称： "]/../following-sibling::div[@class="el-col el-col-20"]//p'))
                        )
                        resource_name = resource_name_element.text.strip()
                        # 处理文件名中的非法字符
                        invalid_chars = '<>:"/\\|?*'
                        for char in invalid_chars:
                            resource_name = resource_name.replace(char, '_')
                    except Exception as e:
                        print(f"提取资源名称失败: {e}")
                        resource_name = "unknown"

                    # 检查 resource_name 是否重复
                    if resource_name in resource_name_counter:
                        resource_name_counter[resource_name] += 1
                        resource_name = f"{resource_name}_{resource_name_counter[resource_name]}"
                    else:
                        resource_name_counter[resource_name] = 1

                    print('化石名字:', resource_name)

                    # 查找目标 <img> 标签
                    img_element = WebDriverWait(browser, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'img.el-image__inner.el-image__preview'))
                    )
                    img_url = img_element.get_attribute('src')

                    if img_url:
                        if not img_url.startswith('http'):
                            base_url = url.rsplit('/', 1)[0]
                            img_url = f"{base_url}/{img_url.lstrip('/')}"

                        # 确定图片扩展名
                        img_extension = os.path.splitext(img_url)[1]
                        # 构建图片保存路径
                        img_name = f"{resource_name}{img_extension}"
                        img_path = os.path.join(img_folder, img_name)
                        try:
                            img_response = requests.get(img_url)
                            if img_response.status_code == 200:
                                with open(img_path, 'wb') as f:
                                    f.write(img_response.content)
                                print(f'已保存图片: {img_path}')
                        except Exception as e:
                            print(f'保存图片 {img_url} 失败: {e}')

                    # 关闭当前标签页
                    browser.close()
                    # 切换回原始窗口
                    browser.switch_to.window(original_window)
            except Exception as e:
                print(f'处理 <tr> 元素时出错: {e}')

        # 查找下一页按钮
        try:
            next_page_button = WebDriverWait(browser, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-v-0cb0b5e4].el-pagination.is-background button.btn-next'))
            )
            if next_page_button.is_enabled():
                next_page_button.click()
                sleep(5)  # 等待下一页加载
            else:
                break  # 下一页按钮不可用，退出循环
        except Exception:
            break  # 找不到下一页按钮，退出循环

except Exception as e:
    print(f'发生错误: {e}')
finally:
    # 关闭浏览器
    browser.quit()
