from src.sources.weddslist import Weddslist
from src.sources.house_of_tartan import HouseOfTartan
from src.sources.tartans_authority import TartansAuthority

# Weddslist().grab()
# HouseOfTartan().grab()
# TartansAuthority().grab()

Weddslist().parse()
HouseOfTartan().parse()
TartansAuthority().parse()
