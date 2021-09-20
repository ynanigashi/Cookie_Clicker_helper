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


class CookieClickerHelper:
    def __init__(self, save_data=False):
        driver = webdriver.Chrome()
        driver.get('https://orteil.dashnet.org/cookieclicker/')
        self.driver = driver
        self.products = []
        self.max_price = 10**100
        
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

    def update_upgrades(self):
        upgrades = self.driver.execute_script("""
            return Game.UpgradesById.map(u => (
                {
                    id:u.id,
                    name: u.name,
                    unlocked: u.unlocked,
                    bought: u.bought,
                    price: u.basePrice,
                    pool: u.pool,
                }))
                .filter(obj => obj.unlocked == 1)
                .filter(obj => obj.bought == 0)
                .filter(obj => obj.pool !== "toggle")
                .filter(obj => obj.pool !== "tech")
                """)
        upgrades.sort(key=lambda u: u['price'])
        self.upgrades = upgrades

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


    def auto(self, seconds):
        end_time = time.perf_counter() + seconds
        try:
            while True:
                # get cookie per click
                mouse_cpc = self.driver.execute_script(' return Game.computedMouseCps')
                # get current cookie amount
                cookie_amount = self.get_cookie_amount()
                
                # get current products
                self.update_products()

                # get upgrades
                self.update_upgrades()

                product = self.products[0]
                product_price = product['bulkPrice']

                if len(self.upgrades) > 0:
                    upgrade = self.upgrades[0]
                    upgrade_price = upgrade['price']
                else:
                    upgrade_price = self.max_price

                price = product_price if product_price < upgrade_price else upgrade_price 

                # check buff state
                self.is_buffed()
                
                # if buffed don't purchase
                if self.buffed:
                    check_point = time.perf_counter()
                    while True:
                        remain_seconds = int(end_time - time.perf_counter())
                        hour, mod_seconds = divmod(remain_seconds, 60 * 60)
                        minu, sec = divmod(mod_seconds, 60)
                        if hour > 0:
                            print(f"\rAuto remain Time is {str(hour).zfill(2)} hour {str(minu).zfill(2)} min. : buffed", end='')
                        elif minu > 0:
                            print(f"\rAuto remain Time is {str(minu).zfill(2)} min {str(sec).zfill(2)} sec. : buffed", end='')
                        else:
                            print(f"\rAuto remain Time is {str(sec).zfill(2)} sec.: buffed          ", end='')

                        #click big cookies
                        try:
                            self.cookie.click()
                        except ElementClickInterceptedException as e:
                            pass

                        #Check Golden Cookie
                        self.click_shimmers_if_exist()

                        # cast conjer baked cookies if mp max
                        self.cast_spell_if_mp_max()

                        #check past time from start this loop
                        if time.perf_counter() - check_point >= 20:
                            break
                    
                elif cookie_amount < price:
                    while True:
                        remain_seconds = int(end_time - time.perf_counter())
                        hour, mod_seconds = divmod(remain_seconds, 60 * 60)
                        minu, sec = divmod(mod_seconds, 60)
                        if hour > 0:
                            print(f"\rAuto remain Time is {str(hour).zfill(2)} hour {str(minu).zfill(2)} min. : collect for {product['name']}", end='')
                        elif minu > 0:
                            print(f"\rAuto remain Time is {str(minu).zfill(2)} min {str(sec).zfill(2)} sec. : collect for {product['name']}", end='')
                        else:
                            print(f"\rAuto remain Time is {str(sec).zfill(2)} sec. : collect for {product['name'] if product_price < upgrade_price else upgrade['name'] }          ", end='')

                        #click big cookies
                        try:
                            self.cookie.click()
                        except ElementClickInterceptedException as e:
                            pass

                        #Check Golden Cookie
                        self.click_shimmers_if_exist()

                        # cast conjer baked cookies if mp max
                        self.cast_spell_if_mp_max()

                        # get current cookie amount
                        cookie_amount = self.get_cookie_amount()

                        #check can buy and remain_seconds
                        if cookie_amount >= price or remain_seconds < 0:
                            print()
                            break
                else:
                    # buy product
                    try:
                        if product_price < upgrade_price:
                            self.driver.execute_script(f"Game.ObjectsById[{ product['id'] }].buy()")
                            print(f" : bought {product['name']}")
                        else:
                            self.driver.execute_script(f"Game.UpgradesById[{upgrade['id']}].buy()")
                            print(f" : bought {upgrade['name']}")
                    except ElementClickInterceptedException as e:
                        pass
                # check duration
                if end_time - time.perf_counter() < 0:
                    hour, mod_seconds = divmod(seconds, 60 * 60)
                    minu, sec = divmod(mod_seconds, 60)
                    if hour > 0:
                        print(f"\rcomplete auto {str(hour).zfill(2)} hour {str(minu).zfill(2)} min {str(sec).zfill(2)} sec.")
                    elif minu > 0:
                        print(f"\rcomplete auto {str(minu).zfill(2)} min {str(sec).zfill(2)} sec.")
                    else:
                        print(f"\rcomplete auto {str(sec).zfill(2)} sec.        ")                    
                    break

        except KeyboardInterrupt:
            self.save_to_file()
            print('[ctrl + C] has pushed. save data to file!')

    def is_buffed(self):
        self.buffed = False
        buffs = self.driver.find_elements(By.CSS_SELECTOR, "#buffs > div")
        # check buff type
        for buff in buffs:
            # If something other than buff40 exists, state is buff
            buff_id = buff.get_attribute("id")
            # buff40 is clot 
            if buff_id != 'buff40':
                self.buffed = True


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
        try:
            while True:
                remain_seconds = int(end_time - time.perf_counter())
                hour, mod_seconds = divmod(remain_seconds, 60 * 60)
                minu, sec = divmod(mod_seconds, 60)
                if hour > 0:
                    print(f"\rClick Remain Time is {str(hour).zfill(2)} hour {str(minu).zfill(2)} min.", end='')
                elif minu > 0:
                    print(f"\rClick Remain Time is {str(minu).zfill(2)} min {str(sec).zfill(2)} sec.", end='')
                else:
                    print(f"\rClick Remain Time is {str(sec).zfill(2)} sec.          ", end='')

                #click big cookies
                try:
                    self.cookie.click()
                except ElementClickInterceptedException as e:
                    pass
                
                # Golden Cookie
                self.click_shimmers_if_exist()

                # cast conjer baked cookies if mp max
                self.cast_spell_if_mp_max()
                
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
        except KeyboardInterrupt:
            self.save_to_file()
            print('[ctrl + C] has pushed. save data to file!')

    def update_clickcps(self):
        self.click_cps = self.bulk_click(100)


    def click_shimmers_if_exist(self):
        shimmers = self.driver.find_elements(By.CSS_SELECTOR, '#shimmers > .shimmer')
        for shimmer in shimmers:
            try:
                shimmer.click()
                print(": Golden Cookie was clicked!!")
            except ElementClickInterceptedException as e:
                pass
            except ElementNotInteractableException as e:
                pass
            except StaleElementReferenceException as e:
                pass

    def cast_spell_if_mp_max(self):
        grimoire = self.driver.execute_script('return Game.ObjectsById[7].minigameLoaded')

        if grimoire:
            # get max mp
            max_mp = self.driver.execute_script('return Game.ObjectsById[7].minigame.magicM')
            mp = self.driver.execute_script('return Game.ObjectsById[7].minigame.magic')

            if max_mp != 0 and max_mp == mp:
                self.driver.execute_script("""
                let M = Game.ObjectsById[7].minigame;
                M.castSpell(M.spellsById[0]);
                """)

def start():
    return CookieClickerHelper()
    
def start_with_save():
    return CookieClickerHelper(save_data=True)

if __name__ == '__main__':
    start()