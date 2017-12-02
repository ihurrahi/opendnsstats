# opendnsstats
Sends a summary email for all blocked domains through OpenDNS

I've set this up so that the script through AWS Lambda, triggered by a timer set to 1am. The script looks at the previous day, logs in and downloads the blocked domain data (translated [this script](https://github.com/opendns/opendns-fetchstats) into Python), publishes to a topic in AWS SNS, where my email address is subscribed to.
