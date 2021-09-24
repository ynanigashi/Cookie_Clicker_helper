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
        self.facilities = []
        self.upgrades = []
        
        # wait for big cookie load.
        WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located((By.ID, 'bigCookie')))
        self.cookie = self.driver.find_element(By.ID, 'bigCookie')
        
        time.sleep(2)
        # hide ad
        self.driver.execute_script('document.getElementById("smallSupport").remove()')

        # accept cookie
        WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div/a[1]')))
        time.sleep(2)
        self.driver.find_element(By.XPATH, '/html/body/div[1]/div/a[1]').click()

        # load save data from clipboard
        if not save_data:
            user_input = self.get_yn('Do you want to load the saved data from Clipboard?')
        if save_data or user_input == 'y':
            self.load_from_clip_board()


    def get_yn(self, str, flg=''):
        yeses = ['y', 'yes', 'ｙ', 'Ｙ', 'ｙｅｓ', 'ＹＥＳ', 'Ｙｅｓ']
        noes = ['n', 'no', 'ｎ', 'Ｎ', 'ｎｏ', 'ＮＯ', 'Ｎｏ']
        ans = ''
        while ans == '':
            user_input = input(f'{str} (y/n):').lower()
            if user_input in yeses:
                ans = 'y'
            elif user_input in noes:
                ans = 'n'
            else:
                print('input [y] or [n].')
         
        if flg == '':
            return ans
        else:
            if ans == 'y': flg = True
            else: flg = False    


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


    def update_facilities(self):
        facilities = self.driver.execute_script("""
            return Game.ObjectsById.map(p => (
                {
                    id: p.id,
                    name: p.name,
                    amount: p.amount,
                    cps: p.amount === 0 ? p.storedCps * Game.globalCpsMult : (p.storedTotalCps/p.amount) * Game.globalCpsMult,
                    price: p.bulkPrice,
                }
            ))
            """)
        for p in facilities:
            p['cost_perf'] = p['cps'] / p['price']
        facilities.sort(key=lambda x: x['cost_perf'], reverse=True)
        self.facilities = facilities

    def update_upgrades(self):
        upgrades = self.driver.execute_script("""
            return Game.UpgradesById.map(u => (
                {
                    id:u.id,
                    name: u.name,
                    unlocked: u.unlocked,
                    bought: u.bought,
                    price: u.getPrice(),
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
        self.update_facilities()
        for p in self.facilities:
            print(f"{p['name']}:", f"{ '{:,.2f}'.format(p['cost_perf'] * 10 ** 9)} / Billion", sep='\t')


    def rank3(self):
        self.update_facilities()
        print('>>>> Best 3 <<<<<')
        cnt = 0
        for i in range(3):
            p = self.facilities[i]
            print(f"{i}:", p['name'],  f"{ '{:,.2f}'.format(p['cost_perf'] * 10 ** 9)} / Billion", sep='\t')

    def show_cps(self):
        units = [
            (1000000000000000000000000000000000000000,'Duodecillion'),
            (1000000000000000000000000000000000000,'Undecillion'),
            (1000000000000000000000000000000000,'Decillion'),
            (1000000000000000000000000000000,'Nonillion'),
            (1000000000000000000000000000,'Octillion'),
            (1000000000000000000000000,'Septillion'),
            (1000000000000000000000,'Sextillion'),
            (1000000000000000000, 'Quintillion'),
            (1000000000000000, 'Quadrillion'),
            (1000000000000,'Trillion'),
            (1000000000, 'Billion'),
            (1000000,'Million'),
            (1000,'Thousand'),
             ]
        self.update_facilities()
        self.facilities.sort(key=lambda x: x['id'])
        for p in self.facilities:
            cps = p['cps']
            for number, unit_name in units:
                if cps // number > 0:
                    p['cps'] = f"{'{:,.2f}'.format(cps/number)} {unit_name}"
                    break
            else:
                p['cps'] = f"{int(cps)}"
                
        for p in self.facilities:
            print(f"{p['name']}:", f"{p['cps']}", sep='\t')


    def auto(self, seconds):
        self.end_time = time.perf_counter() + seconds
        try:
            while True:
                # get cookie per click
                # mouse_cpc = self.driver.execute_script(' return Game.computedMouseCps')

                # if buffed don't purchase
                self.update_buff_status()
                if self.buffed:
                    self.click_while_buffend()
  
                # get current cookie amount
                self.update_cookie_amount()
                
                # update affordable item = self.item
                self.update_affordable_item()

                # if can't buy, so collect cookies
                if self.cookie_amount < self.item['price']:
                    self.click_while_collect_or_endtime()

                # if can buy Purchase item if endtime reached don't purchase
                if self.cookie_amount >= self.item['price']:
                    self.purchase_item()

                # check duration ends
                if self.end_time - time.perf_counter() < 0:
                    self.display_time(seconds, 'Complate')
                    print()
                    break
        # if push ctrl + c end with save state to file 
        except KeyboardInterrupt:
            self.save_to_file()
            print('[ctrl + C] has pushed. save data to file!')
    

    def click_while_buffend(self):
        while True:
            # display remaitime
            remain_seconds = int(self.end_time - time.perf_counter())
            self.display_time(remain_seconds, 'Remain', 'buffed')

            #click big cookies
            try:
                self.cookie.click()
            except ElementClickInterceptedException as e:
                pass

            #Check Golden Cookie
            self.click_shimmers_if_exist()

            # cast conjer baked cookies if mp max
            self.cast_spell_if_mp_max()

            # update buff status
            self.update_buff_status()
            #check buff status
            if not self.buffed:
                break
    

    def update_affordable_item(self):
        # get current facilities and upgrades
        self.update_facilities()
        self.update_upgrades()

        # if there are upgrades
        if len(self.upgrades) > 0 and self.upgrades[0]['price'] < self.facilities[0]['price']:
            self.item = self.upgrades[0]
            self.item['type'] = 'upgrade'
        else:
            self.item = self.facilities[0]
            self.item['type'] = 'facility'


    def click_while_collect_or_endtime(self):
        while True:
            # display remain time
            remain_seconds = int(self.end_time - time.perf_counter())
            self.display_time(remain_seconds, 'Remain', f"Collect for {self.item['name']}")

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
            self.update_cookie_amount()

            #check can buy and remain_seconds
            if self.cookie_amount >= self.item['price'] or remain_seconds < 0:
                print()
                break
    

    def purchase_item(self):
        if self.item['type'] == 'facility':
            js = f"Game.ObjectsById[{ self.item['id'] }].buy()"
        else:
            js = f"Game.UpgradesById[{ self.item['id'] }].buy()"
        try:
            self.driver.execute_script(js)
            print(f":purchased {self.item['name']}")
        except Exception as e:
            print(e)


    def display_time(self, seconds, type, msg=''):
        hour, mod_seconds = divmod(seconds, 60 * 60)
        minu, sec = divmod(mod_seconds, 60)
        print(f"\r{type}: {str(hour).zfill(2)} hour {str(minu).zfill(2)} min {str(sec).zfill(2)} sec.  : {msg}", end='')


    def update_buff_status(self):
        self.buffed = False
        buffs = self.driver.find_elements(By.CSS_SELECTOR, "#buffs > div")
        # check buff type
        for buff in buffs:
            # If something other than buff40 exists, state is buff
            try:
                mouse_over = buff.get_attribute("onmouseover")
                # buff40 is clot 
                if not 'Clot' in mouse_over:
                    self.buffed = True
            except StaleElementReferenceException as e:
                pass


    def update_cookie_amount(self):
            self.cookie_amount = int(self.driver.execute_script("""
            return Game.cookies
            """))


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
                # display remain time
                remain_seconds = int(end_time - time.perf_counter())
                self.display_time(remain_seconds, 'Remain', 'Click!!')

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
                    self.display_time(n, 'Complete', 'Clicked')
                    print()
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