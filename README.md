# synthetic-parallel-selenium
Boosting selenium’s data scraping speed with a partially parallel approach. 

# Project Goal:
Scraping hundreds of GB of traffic data from an online SQL GDOT database.

# Methods
This GDOT system features a GUI which is highly inefficient with respect to time, sustaining large loading times between each data selection. This project required collecting two years’ worth of data from across 1,800 stations. Additionally, data draws were limited to selecting a maximum of 4 days of data at a time, allowing only one station per instance.  Therefore, a rapid web-scraping process would need to be deployed. 
There exist is a hierarchy of efficiency among scraping web libraries. Some of the swifter methods include:

•	Scarpy 
•	Mechanize
•	BS4

However, to avoid interacting with the slow GUI, it was found that the SQL URL was formulaic in nature allowing for fast manipulation effectively averting the GUI all together. However, this online database features an **apache httpd .htaccess** configuration.

![]( https://i.ibb.co/S0qxp4K/hatachsm375.png)

This item cannot be accessed with the above methods. Subsequentially, bounding me to initially “force enter” the password and username via the combination Selenium and PyAutoGUI. 

![](https://media4.giphy.com/media/bwEChFLphBvZJtjAug/giphy.gif)

However, this standard selenium-based method was not sufficient. To boost the speed of selenium, I sought to address the constant time lost at each data request. This loss occurred regardless of my own internet speed. To fix this issue I developed an iterative, faux parallel method. In which, you can choose your own number of “workers”. I found that managing 6 simultaneous drivers increased my scraping speed by a multiple of 5.

![]( https://i.giphy.com/media/ynuD2sv5jzlCI5Ce9k/giphy.webp)


