Cookie Clicker helper

on python IDLE
```
from main import CookieClickerPlayer
# if you have save data in click board
player = CookieClickerPlayer(save_data=True)

# you don't have save data
player = CookieClickerPlayer()

# check cps / billion
player.rank() or player.rank3()

# click big Cookie
player.click_while(<seconds>)

# save Game state to file
player.save_to_file()

# save Game state to clip board
player.save_to_clip_board()

# load Game state from clip board
player.load_to_clip_board()

```