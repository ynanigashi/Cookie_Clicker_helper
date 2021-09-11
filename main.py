from itertools import product
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import ElementNotInteractableException

class CookieClickerPlayer:
    def __init__(self):
        driver = webdriver.Chrome()
        driver.get('https://orteil.dashnet.org/cookieclicker/')
        self.driver = driver
        
        # wait for big cookie load.
        WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located((By.ID, 'bigCookie')))
        self.cookie = self.driver.find_element(By.ID, 'bigCookie')
        self.products = []
        
        # update click cps
        self.update_clickcps()


    def update_products(self):
        products = self.driver.execute_script("""
            return Game.ObjectsById.map(p => (
                {
                    id: p.id,
                    name: p.name,
                    amount: p.amount,
                    cps: p.cps(p),
                    bulkPrice: p.bulkPrice,
                }
            ))
            """)
        for p in products:
            p['cost_perf'] = p['cps'] / p['bulkPrice']
        products.sort(key=lambda x: x['cost_perf'], reverse=True)
        self.products = products
    
    def rank(self):
        self.update_products()
        for p in self.products:
            print(f"{p['name']} : {round(p['cost_perf'] * 10 ** 8, 2)} / Billion")
    
    def rank3(self):
        self.update_products()
        print('>>>> Best 3 <<<<<')
        cnt = 0
        for i in range(3):
            p = self.products[i]
            print(f"{i}: {p['name']} : {round(p['cost_perf'] * 10 ** 8, 2)} / Billion")


    def auto(self, saving=True):
        # get elements

        # start
        self.click_cps = self.bulk_click(100)
        # loop
        for i in range(10):
            
            self.update_products()
            self.print_products_best3()

            # Golden Cookie
            self.click_shimmers_if_exist()

            # 今現在のクッキー
            cookies = self.get_cookie_amount()

            if saving:
                product = self.products[0]
                if cookies >= product['bulkPrice']:
                    #買う処理
                    self.driver.find_element(By.ID, f"product{product['id']}").click()
            else:
                # 買える奴を買う
                for product in self.products:
                    if cookies >= product['bulkPrice']:
                        #買う処理
                        self.driver.find_element(By.ID, f"product{product['id']}").click()
                        break
            # 次に買いたいやつ
            # クリックしたらどのくらいかかるか
            if False:
                pass
            else:
                self.click_cps = self.bulk_click(100)

    def get_cookie_amount(self):
            cookies = self.driver.execute_script("""
            return Game.cookies
            """)
            return cookies

    def bulk_click(self, n):
        before = time.perf_counter()
        for _ in range(n):
            self.cookie.click()
        after = time.perf_counter()
        return n / (after - before)

    def click_while(self, n):
        cps = int(self.click_cps)
        total, cnt = cps * n, n
        for i in range(total):
            current_cnt = (total - i) // cps
            if not cnt ==  current_cnt:
                cnt = current_cnt
                if cnt <= 10:
                    print(f"Remain Time is {cnt} sec.")
                elif cnt <= 60 and cnt % 10 == 0:
                    print(f"Remain Time is {cnt} sec.")
                elif cnt % 30 == 0:
                    print(f"Remain Time is {round(cnt / 60, 2)} min.")

            self.cookie.click()
            # Golden Cookie
            self.click_shimmers_if_exist()
    
    def update_clickcps(self):
        self.click_cps = self.bulk_click(100)

    def click_shimmers_if_exist(self):
        shimmers = self.driver.find_elements(By.CSS_SELECTOR, '#shimmers > .shimmer')
        for shimmer in shimmers:
            try:
                shimmer.click()
                print("Golden Cookie was clicked!!")
            except ElementClickInterceptedException as e:
                print(e)
            except ElementNotInteractableException as e:
                print(e)

def test():
    player = CookieClickerPlayer()
    while True:
        player.auto()


if __name__ == '__main__':
    test()
