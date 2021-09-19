Cookie Clicker helper

on python IDLE
```
from main import CookieClickerHelper
# if you have save data in click board
h = CookieClickerHelper(save_data=True)

# you don't have save data
h = CookieClickerHelper()

# check cps / billion
h.rank() or player.rank3()

# click big Cookie while n seconds
h.click_while(n)

# auto play while n seconds
h.auto(n)

# save Game state to file
h.save_to_file()

# save Game state to clip board
h.save_to_clip_board()

# load Game state from clip board
h.load_to_clip_board()

```