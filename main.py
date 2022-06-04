import time
from datetime import datetime as dt

from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pyperclip


class CookieClickerHelper:
    def __init__(self, save_data=None, auto_grandmapocalypse=None, auto_dragontrain=None):
        driver = webdriver.Chrome()
        driver.get('https://orteil.dashnet.org/cookieclicker/')
        self.driver = driver

        self.auto_grandmapocalypse = False
        self.pledge_time = None
        self.auto_dragontrain =False
        
        # wait for big cookie load.
        WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located((By.ID, 'bigCookie')))
        self.big_cookie = self.driver.find_element(By.ID, 'bigCookie')
        
        time.sleep(2)
        # hide ad
        self.driver.execute_script('document.getElementById("smallSupport").remove()')

        # Click accept cookie button
        WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div/a[1]')))
        time.sleep(2)
        self.driver.find_element(By.XPATH, '/html/body/div[1]/div/a[1]').click()

        # load save data from clipboard
        user_input = ''
        if save_data is None:
            msg = 'Do you want to load the saved data from Clipboard?'
            user_input = self.get_yn_from_user_input(msg)
        if save_data is True or user_input == 'y':
            self.load_from_clip_board()

        # check auto_grandmapocalypse
        # init user_input
        user_input = ''
        if auto_grandmapocalypse is None:
            msg = 'Do you want to auto play Grandmapocalypse?'
            user_input = self.get_yn_from_user_input(msg)
        if auto_grandmapocalypse is True or user_input == 'y':
            self.auto_grandmapocalypse = True


        # Check auto_dragontrain
        # init user_input
        user_input = ''
        if auto_dragontrain is None:
            msg = 'Do you want to auto play Dragon train?'
            user_input = self.get_yn_from_user_input(msg)
        if auto_dragontrain is True or user_input == 'y':
            self.auto_dragontrain = True


    def set_pledge_time(self):
        # kill Wrinklers every 3 hours
        pledge_duration = 60 * 60 * 3

        # if game has Elder Pact, so state is granmapocalypse
        has_elderPact = int(self.driver.execute_script('return Game.Has("Elder Pact")'))

        if has_elderPact == 1:
            self.pledge_time = time.perf_counter() + pledge_duration
        else:
            self.pledge_time = None


    def get_yn_from_user_input(self, str, flg=''):
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
        save_data = self.driver.execute_script("return Game.WriteSave(1)")
        pyperclip.copy(save_data)


    def save_to_file(self, str=''):
        now = dt.now()
        if str == '':
            str = 'Cookie_Clicker_Save'
        file_name = f'{str}_{now.strftime("%Y%m%d%H%M%S") }.txt'
        save_data = self.driver.execute_script("return Game.WriteSave(1)")
        with open(file_name, mode='w') as f:
            f.write(save_data)


    def get_facilities(self):
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
        return facilities


    def get_upgrades(self):
        upgrades = self.driver.execute_script("""
            return Object.keys(Game.UpgradesById)
                .map(i => Game.UpgradesById[i])
                .map(u => (
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
                """)
        # for auto grandmapocalipse exclude tech from upgrades
        if self.auto_grandmapocalypse is False:
            # exclude tech item from upgrades
            upgrades = [u for u in upgrades if u['pool'] != 'tech']
        
        elif self.pledge_time is not None and self.pledge_time < time.perf_counter():
            # pledge time is valid and over add elder pledge to upgrade,
            # so purchese elder pledge 
            upgrades.append(self.get_elder_pledge())

        upgrades.sort(key=lambda u: u['price'])
        return upgrades


    def get_elder_pledge(self):
        elder_pledge = self.driver.execute_script("""
            return Object.keys(Game.UpgradesById)
                .map(i => Game.UpgradesById[i])
                .map(u => (
                    {
                        id:u.id,
                        name: u.name,
                        unlocked: u.unlocked,
                        bought: u.bought,
                        price: u.getPrice(),
                        pool: u.pool,
                    }))
                .filter(obj => obj.unlocked == 1)
                .filter(obj => obj.name === "Elder Pledge")
                """)[0]
        return elder_pledge


    def rank(self):
        facilities = self.get_facilities()
        for p in facilities:
            print(f"{p['name']}:", f"{ '{:,.2f}'.format(p['cost_perf'] * 10 ** 9)} / Billion", sep='\t')


    def rank3(self):
        facilities = self.get_facilities()
        print('>>>> Best 3 <<<<<')
        cnt = 0
        for i in range(3):
            p = facilities[i]
            print(f"{i}:", p['name'],  f"{ '{:,.2f}'.format(p['cost_perf'] * 10 ** 9)} / Billion", sep='\t')


    def transform_readable_number(self, number):
        units = [
            (1000000000000000000000000000000000000000000000000000000000000000000,'Unvigintillion'),
            (1000000000000000000000000000000000000000000000000000000000000000,'Vigintillion'),
            (1000000000000000000000000000000000000000000000000000000000000,'Novemdecillion'),
            (1000000000000000000000000000000000000000000000000000000000,'octodecillion'),
            (1000000000000000000000000000000000000000000000000000000,'septendecillion'),
            (1000000000000000000000000000000000000000000000000000,'Sexdecillion'),
            (1000000000000000000000000000000000000000000000000,'Quindecillion'),
            (1000000000000000000000000000000000000000000000,'Quattuordecillion'),
            (1000000000000000000000000000000000000000000,'Tredecillion'),
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
        for i, unit_name in units:
            if number // i > 0:
                display_str = f"{'{:,.2f}'.format(number/i)} {unit_name}"
                break
        else:
            display_str = f"{int(number)}"

        return display_str


    def show_cps(self):
        facilities = self.get_facilities()
        facilities.sort(key=lambda x: x['id'])
        for p in facilities:
            p['cps'] = self.transform_readable_number(p['cps'])
                
        for p in facilities:
            print(f"{p['name']}:", f"{p['cps']}", sep='\t')


    def auto(self, seconds):
        end_time = time.perf_counter() + seconds
        
        # set pledge time
        if self.auto_grandmapocalypse is True and self.pledge_time is None:
            self.set_pledge_time()
        try:
            while True:
                # auto dragon train
                if self.auto_dragontrain:
                    self.train_dragon()
                # get cookie per click
                # mouse_cpc = self.driver.execute_script(' return Game.computedMouseCps')

                # if buffed don't purchase
                if self.is_buffed():
                    self.click_while_buffend(end_time)
                
                # get affordable item
                item = self.get_affordable_item()
                item_price = item['price']

                # if can't buy, so collect cookies
                if self.get_cookies_in_bank() < item_price:
                    self.click_while_collect_or_endtime(item, end_time)

                # if can buy Purchase item if endtime reached don't purchase
                if self.get_cookies_in_bank() >= item_price:
                    self.purchase_item(item)

                # check duration ends
                current_height =  self.driver.get_window_size()['height']
                remain_time = end_time - time.perf_counter()
                if remain_time <= 0 or current_height <= 200:
                    if remain_time<= 0:
                        self.display_time(seconds, 'Complate')
                    else:
                        self.display_time(seconds - remain_time, 'Stopped', 'Clicked')
                    print()
                    break
        # if push ctrl + c end with save state to file 
        except KeyboardInterrupt:
            self.save_to_file()
            print('[ctrl + C] has pushed. save data to file!')
    

    def train_dragon(self):
        def has_crumbly_egg():
            # gema has crumbly egg so, Dragon is available
            crumbly_egg = False
            res = self.driver.execute_script('return Game.Has("A crumbly egg")')
            if res == 1:
                crumbly_egg =True
            return crumbly_egg
        

        def get_amount_of_facility(name):
            facilities = self.get_facilities()
            return [x['amount'] for x in facilities if x['name'] == name ][0]


        def level_up_dragon():
            self.driver.execute_script('Game.UpgradeDragon()')

        # check dragon training is enable
        if not has_crumbly_egg():
            return

        # display dragon tooltip(special tab)
        self.driver.execute_script('Game.specialTab = "dragon"')

        confirm_button_id = 'promptOption0'
        level = int(self.driver.execute_script('return Game.dragonLevel'))
        number_of_prism = get_amount_of_facility('Prism')
        number_of_ideleverse = get_amount_of_facility('Idleverse')

        if level <= 3:
            level_up_dragon()

        elif level == 4:
            level_up_dragon()
            # set DragonAura 1 ( 'Breath of Milk') to 0 (slot 1)
            self.driver.execute_script('Game.SetDragonAura(1, 0)')
            # Click Confirm button
            WebDriverWait(self.driver, 5).until(EC.presence_of_all_elements_located((By.ID, confirm_button_id)))
            self.driver.find_element(By.ID, confirm_button_id).click()
            
        elif level <= 17 and number_of_prism >= 100:
            level_up_dragon()

        elif level == 18 and number_of_prism >= 100:
            level_up_dragon()
            
            # set DragonAura 15 ("Radiant Appetite") to 0 (slot 1)
            self.driver.execute_script('Game.SetDragonAura(15, 0)')
            # Click Confirm button
            WebDriverWait(self.driver, 5).until(EC.presence_of_all_elements_located((By.ID, confirm_button_id)))
            self.driver.find_element(By.ID, confirm_button_id).click()

        elif level <= 23 and number_of_ideleverse >= 200:
            level_up_dragon()

        elif level == 24 and number_of_ideleverse >= 200:
            level_up_dragon()

            # set DragonAura, 1 ('Breath of Milk') to 1 (slot 2)
            self.driver.execute_script('Game.SetDragonAura(1, 1)')
            # Click Confirm button
            WebDriverWait(self.driver, 5).until(EC.presence_of_all_elements_located((By.ID, confirm_button_id)))
            self.driver.find_element(By.ID, confirm_button_id).click()

        elif level == 25:
            print('Your Dragon is fully trained!!')
            # turn off auto_train
            self.auto_dragontrain = False
            # close special tab
            # self.driver.execute_script('Game.ToggleSpecialMenu(0)')


    def click_while_buffend(self, end_time):
        while True:
            # display remaitime
            remain_seconds = int(end_time - time.perf_counter())
            self.display_time(remain_seconds, 'Remain', 'buffed')

            #click big cookies
            try:
                self.big_cookie.click()
            except ElementClickInterceptedException as e:
                pass

            #Check Golden Cookie
            self.click_shimmers_if_exist()

            # cast conjer baked cookies if mp max
            self.cast_spell_if_mp_max()

            #check buff status
            if not self.is_buffed():
                break
    

    def get_affordable_item(self):
        # get current facilities and upgrades
        facilities = self.get_facilities()
        upgrades = self.get_upgrades()

        # if there are upgrades
        if len(upgrades) > 0 and upgrades[0]['price'] < facilities[0]['price']:
            item = upgrades[0]
            item['type'] = 'upgrade'
        else:
            item = facilities[0]
            item['type'] = 'facility'
        
        item['display_price'] = self.transform_readable_number(item['price'])

        return item


    def click_while_collect_or_endtime(self, item, end_time):
        while True:
            # if big cookie is hidden end loop
            if not self.big_cookie.is_displayed():
                break

            # display remain time
            remain_seconds = int(end_time - time.perf_counter())
            self.display_time(remain_seconds, 'Remain', f"Collect for {item['name']} / {item['display_price']}")

            #click big cookies 10 times
            for _ in range(100):
                try:
                    self.big_cookie.click()
                except ElementClickInterceptedException as e:
                    pass

            #Check Golden Cookie
            self.click_shimmers_if_exist()

            # cast conjer baked cookies if mp max
            self.cast_spell_if_mp_max()

            #check can buy or time or current_htight is less than 200px
            current_height =  self.driver.get_window_size()['height']
            if self.get_cookies_in_bank() >= item['price'] or remain_seconds <= 0 or current_height < 200:
                print()
                break
    

    def purchase_item(self, item):
        # one mind needs argment
        arg = ''
        if item['name'] == 'One mind':
            arg = '1'
        # purchase facility
        if item['type'] == 'facility':
            js = f"Game.ObjectsById[{ item['id'] }].buy()"
        # purchase Upgrades
        else:
            js = f"Game.UpgradesById[{ item['id'] }].buy({arg})"
        try:
            self.driver.execute_script(js)
            print(f":purchased {item['name']}")

            # if success purchase and item name is Elder Pact or Elder Pledge set pledge time
            if item['name'] in ['Elder Pact', 'Elder Pledge']:
                self.set_pledge_time()
        except Exception as e:
            print(e)


    def display_time(self, seconds, type, msg=''):
        hour, mod_seconds = divmod(seconds, 60 * 60)
        minu, sec = divmod(mod_seconds, 60)
        print(f"\r{type}: {str(hour).zfill(2)} hour {str(minu).zfill(2)} min {str('{:.0f}'.format(sec)).zfill(2)} sec.  : {msg}", end='')


    def is_buffed(self):
        buffed = False
        buffs = self.driver.find_elements(By.CSS_SELECTOR, "#buffs > div")
        # check buff type
        for buff in buffs:
            # If something other than buff40 exists, state is buff
            try:
                mouse_over = buff.get_attribute("onmouseover")
                # buff40 is clot 
                if not ('Clot' in mouse_over or 'Loan' in mouse_over):
                    buffed = True
            except StaleElementReferenceException as e:
                pass
        return buffed


    def get_cookies_in_bank(self):
        cookies_in_bank = int(self.driver.execute_script("""
            return Game.cookies
            """))
        return cookies_in_bank


    def bulk_click(self, n):
        before = time.perf_counter()
        for _ in range(n):
            self.big_cookie.click()
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
                    self.big_cookie.click()
                except ElementClickInterceptedException as e:
                    pass
                
                # Golden Cookie
                self.click_shimmers_if_exist()

                # cast conjer baked cookies if mp max
                self.cast_spell_if_mp_max()
                
                current_height =  self.driver.get_window_size()['height']
                if remain_seconds <= 0 or current_height <= 200:
                    if remain_seconds <= 0:
                        self.display_time(n, 'Complete', 'Clicked')
                    else:
                        self.display_time(n - remain_seconds, 'Stopped', 'Clicked')
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