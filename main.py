import time
from datetime import datetime as dt

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import StaleElementReferenceException
import pyperclip


class CookieClickerPlayer:
    def __init__(self, save_data=False):
        driver = webdriver.Chrome()
        driver.get('https://orteil.dashnet.org/cookieclicker/')
        self.driver = driver
        self.products = []
        
        # wait for big cookie load.
        WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located((By.ID, 'bigCookie')))
        self.cookie = self.driver.find_element(By.ID, 'bigCookie')

        # update click cps
        self.update_clickcps()
        
        # hide ad
        self.driver.execute_script('document.getElementById("smallSupport").remove()')

        # accept cookie
        WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div/a[1]')))
        time.sleep(1)
        self.driver.find_element(By.XPATH, '/html/body/div[1]/div/a[1]').click()

        #load save data
        if save_data:
            self.load_from_clip_board()


    def load_from_clip_board(self):
        save_data = pyperclip.paste()
        if save_data == "":
            print("There's no clipboad data")
            return
        self.driver.execute_script(f'Game.ImportSaveCode("{save_data}")')


    def save_to_clip_board(self):
        self.save_data = self.driver.execute_script("return Game.WriteSave(1)")
        pyperclip.copy(self.save_data)


    def save_to_file(self):
        now = dt.now()
        file_name = f'Cookie_Clicker_Save_{now.strftime("%Y%m%d%H%M%S") }.txt'
        self.save_data = self.driver.execute_script("return Game.WriteSave(1)")
        with open(file_name, mode='w') as f:
            f.write(self.save_data)


    def update_products(self):
        products = self.driver.execute_script("""
            return Game.ObjectsById.map(p => (
                {
                    id: p.id,
                    name: p.name,
                    amount: p.amount,
                    cps: p.amount === 0 ? p.storedCps * Game.globalCpsMult : (p.storedTotalCps/p.amount) * Game.globalCpsMult,
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
            print(f"{p['name']}:", f"{ '{:,.2f}'.format(p['cost_perf'] * 10 ** 9)} / Billion", sep='\t')


    def rank3(self):
        self.update_products()
        print('>>>> Best 3 <<<<<')
        cnt = 0
        for i in range(3):
            p = self.products[i]
            print(f"{i}:", p['name'],  f"{ '{:,.2f}'.format(p['cost_perf'] * 10 ** 9)} / Billion", sep='\t')

    def show_cps(self):
        units = [
            (1000000000000000000000,'sextillion'),
            (1000000000000000000, 'quintillion'),
            (1000000000000000, 'quadrillion'),
            (1000000000000,'trillion'),
            (1000000000, 'billion'),
            (1000000,'million'),
            (1000,'thousand'),
             ]
        self.update_products()
        self.products.sort(key=lambda x: x['id'])
        for p in self.products:
            cps = p['cps']
            for number, unit_name in units:
                if cps // number > 0:
                    p['cps'] = f"{'{:,.2f}'.format(cps/number)} {unit_name}"
                    break
            else:
                p['cps'] = f"{int(cps)}"
                
        for p in self.products:
            print(f"{p['name']}:", f"{p['cps']}", sep='\t')


    def auto(self, saving=True):
        # get elements

        # start
        self.click_cps = self.bulk_click(100)
        # loop
        for i in range(10):
            
            self.update_products()
            self.rank3()

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
        end_time = time.perf_counter() + n

        while True:
            remain_seconds = int(end_time - time.perf_counter())
            hour, mod_seconds = divmod(remain_seconds, 60 * 60)
            minu, sec = divmod(mod_seconds, 60)
            if hour > 0:
                print(f"\rRemain Time is {str(hour).zfill(2)} hour {str(minu).zfill(2)} min.", end='')
            elif minu > 0:
                print(f"\rRemain Time is {str(minu).zfill(2)} min {str(sec).zfill(2)} sec.", end='')
            else:
                print(f"\rRemain Time is {str(sec).zfill(2)} sec.          ", end='')

            #click big cookies
            try:
                self.cookie.click()
            except ElementClickInterceptedException as e:
                print(e)
            
            # Golden Cookie
            self.click_shimmers_if_exist()
            
            if remain_seconds <= 0:
                hour, mod_seconds = divmod(n, 60 * 60)
                minu, sec = divmod(mod_seconds, 60)
                if hour > 0:
                    print(f"\rcomplete click {str(hour).zfill(2)} hour {str(minu).zfill(2)} min {str(sec).zfill(2)} sec.")
                elif minu > 0:
                    print(f"\rcomplete click {str(minu).zfill(2)} min {str(sec).zfill(2)} sec.")
                else:
                    print(f"\rcomplete click {str(sec).zfill(2)} sec.        ")                    
                break


    def update_clickcps(self):
        self.click_cps = self.bulk_click(100)


    def click_shimmers_if_exist(self):
        shimmers = self.driver.find_elements(By.CSS_SELECTOR, '#shimmers > .shimmer')
        for shimmer in shimmers:
            try:
                shimmer.click()
                print(": Golden Cookie was clicked!!")
            except ElementClickInterceptedException as e:
                print(e)
            except ElementNotInteractableException as e:
                print(e)
            except StaleElementReferenceException as e:
                print(e)


def test():
    player = CookieClickerPlayer()
    while True:
        player.auto()


if __name__ == '__main__':
    test()