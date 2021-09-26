Cookie Clicker helper

on python IDLE
```
from main import CookieClickerHelper as helper
# if you have save data in click board
h = helper(save_data=True)
or
h = helper(True)

# if you want to use auto granmapocalypse
h = helper(auto_granmapocalypse=True)
or
h = helper((True | False) , True)

# if you don't set any args, helper confirms options to you.
h = helper()

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
TODO
    - Pantheon
    - season event