#!/usr/bin/env python3
# File name: speedtester.py
# Description: Tests the Internet speed using Speedtest.net and posts tweet.
# Author: iamnotzerocool
# Date: 14-02-2021

from six import BytesIO
from six.moves.urllib.request import Request, urlopen

from twython import Twython, TwythonError
from speedtest import Speedtest, SpeedtestResults

#############################################################################################################################################
SERVERS = []  #set to [] if you just want to test the closest 5 servers, or set to list of server IDs to test (http://www.speedtest.net/speedtest-servers.php)
ISP_DL = 1024 #ISP advertised download speed in Mbits/s
ISP_UL = 1024 #ISP advertised upload speed in Mbits/s
TWEET_THRESHOLD = 70 #percent. When DL or UL is below X percent of above speeds then tweet is sent!
POST_IMAGE = True #Upload Speedtest result image twith tweet

TWEET = ("Hey @isp why is my internet speed {dl:0.0f} Mbps down\{ul:0.0f} Mbps up"
        " when I pay for {ISP_DL:0.0f} Mbps down\{ISP_UL:0.0f} Mbps up in Somewhere, NY, USA?"
        " #speedtest #isp")

TWITTER_CONSUMER_KEY=""
TWITTER_CONSUMER_SECRET=""
TWITTER_ACCESS_TOKEN_KEY=""
TWITTER_ACCESS_TOKEN_SECRET=""
#############################################################################################################################################

speedtest = Speedtest()
api = Twython(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET, TWITTER_ACCESS_TOKEN_KEY, TWITTER_ACCESS_TOKEN_SECRET)

avgs = {'count':0,'dl':0,'ul':0,'ping':0,'ISP_DL':ISP_DL,'ISP_UL':ISP_UL}
best = {'server':None,'dl':0}
servers = []
media_ids = []

if SERVERS:
    raw = speedtest.get_servers(SERVERS)
    for d in sorted(raw.keys()):
        servers.extend(raw[d])
else:
    servers = speedtest.get_closest_servers(5)

for server in servers:
    print("Testing: #{id} - {sponsor} ({name}) [{d:0.2f} km]".format(**server))
    try:
        server = speedtest.get_best_server([server])
        dl = speedtest.download()
        ul = speedtest.upload()
        print("Ping: {0:0.2f}ms | D/L: {1:0.2f} Mbps | U/L: {2:0.2f} Mbps\n".format(server['latency'], dl / 1000 / 1000, ul / 1000 / 1000))

        avgs['count'] += 1
        avgs['dl'] += dl
        avgs['ul'] += ul
        avgs['ping'] += server['latency']
        if dl > best['dl']:
            best = {'server':server, 'dl':dl}
    except:
        print("Error testings Server: {name}".format(**server))

if avgs['count'] == 0:
    print("No speed results")
    quit()

avgs['dl'] = avgs['dl'] / avgs['count']
avgs['ul'] = avgs['ul'] / avgs['count']
avgs['ping'] = avgs['ping'] / avgs['count']
result = SpeedtestResults(avgs['dl'], avgs['ul'], avgs['ping'], best['server'])

#Convert to Mbps
avgs['dl'] = avgs['dl'] / 1000 / 1000;
avgs['ul'] = avgs['ul'] / 1000 / 1000;

print("Completed Tests: {count}\n"
    "Average Ping: {ping:0.2f}ms\n"
    "Average D/L: {dl:0.2f} Mbps\n"
    "Average U/L: {ul:0.2f} Mbps\n"
    .format(**avgs))
    
if avgs['dl'] > (TWEET_THRESHOLD/100.0) * ISP_DL and avgs['ul'] > (TWEET_THRESHOLD/100.0) * ISP_UL:
    print("Speeds within threshold")
    quit()

TWEET = TWEET.format(**avgs)
if len(TWEET) > 140:
    print("Tweet can not be longer than 140 characters.")
    quit()

if POST_IMAGE:
    try:
        img_request = Request(result.share(), headers={'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0'})
        img_data = BytesIO(urlopen(img_request).read())
        media_ids = [api.upload_media(media=img_data)['media_id']]
    except:
        print("Error uploading Speedtest result image")
        quit()

try:
    print("Tweeting with media: {0}:\n\n{1}\n".format(media_ids, TWEET))
    result = api.update_status(status=TWEET, media_ids=media_ids)
except TwythonError as e:
    print("Error sending tweet: {0}".format(e))
else:
    print("** TWEET SENT! **")
