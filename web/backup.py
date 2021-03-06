# -*- coding: utf-8 -*- 

from flask import Flask, render_template, Response, request, jsonify, flash, g
import redis
import csv
import os, sys


lib_path = os.path.abspath(os.path.join('tools'))
sys.path.append(lib_path)

import twitter_api
# import pycountry
import wikipedia

from kafka import KafkaClient, SimpleProducer, SimpleConsumer



app = Flask(__name__)
r = redis.StrictRedis(host='127.0.0.1', port=6379, db=0)


global university_list
university_list = []
with open(os.path.join(os.path.dirname(__file__),'static', 'data', 'world-universities.csv'), 'rb') as f:
    reader = csv.reader(f)
    temp_list = list(reader)
for l in temp_list:
    university_list.append(l[1].decode('utf-8'))



@app.route('/stream', methods = ['GET'])
def kafka_stream():
    topic = request.args.get('topic')
    print topic
    kafka = KafkaClient("localhost:9092")
    consumer = SimpleConsumer(kafka, "python", topic)
    topic = None

    def gen():
        for message in consumer:
            yield 'data: %s\n\n' %str(message.message.value)

    print "DEBUG: Kafka Stream Connected"
    return Response(gen(), mimetype="text/event-stream")



@app.route('/')
@app.route('/map')
def show_map():
  #Basic d3 view = basic.html and app.js
    return render_template("world_map.html")

@app.route('/ca_map')
def ca_map():
	return render_template("ca_map.html")

@app.route('/test')
def test():
    return render_template("test.html", university_list= university_list)

@app.route('/university')
def university():
    return render_template("university.html", university_list= university_list)

@app.route('/word-cloud')
def word_cloud():
    return render_template("word-cloud.html")

@app.route('/component', methods=['GET'])
def component():
    return render_template("component.html")

@app.route('/_twitter_query')
def twitter_query():
    kafka = KafkaClient("localhost:9092")
    kafka_producer = SimpleProducer(kafka)
    query_text = request.args.get('query', "", type=str)
    # Pass the query to the web crawler or API
    
    if twitter_query != "":
        # twitter_api.search(twitter_query)
        basic_info = twitter_api.screen_name_search(query_text)
        if basic_info == {}:
            return jsonify(message = "There is no twitter account available!")
        text_list = twitter_api.user_timeline(basic_info["screen_name"])
        for text in text_list:
            #print text
            kafka_producer.send_messages("first",text)
    # if api reach its rate limits, move to web crawler
    return jsonify(message = "")

@app.route('/_twitter_area_query')
def twitter_area_query():
    lat = request.args.get('lat', "", type=str)
    lng = request.args.get('lng', "", type=str)
    radius = request.args.get('radius', "", type=int)
    print lat, lng, radius
    return jsonify()


@app.route('/_wiki_query')
def wiki_query():
    # do not indicates type, whether unicode character will lead null result
    wiki_query = request.args.get('wiki_query', "")
    
    if wiki_query != "":
        wiki_query_text = wikipedia.search(wiki_query.encode('utf-8'))[0]
        
        page = wikipedia.page(wiki_query_text)
        summary = wikipedia.summary(wiki_query_text)
        # if wiki_query_text not in university_list:
        #     pass
        if len(page.images) != 0:
            image = page.images[0]
        else:
            image = os.path.abspath(os.path.join('static/images/NoImageAvailable.jpg'))
        return jsonify(title = page.title,  summary = summary, image = image)
    else:
        print "wiki query is null"
        return jsonify(title = "",  summary = "", image = "")
    # return jsonify(title = page.title,  summary = summary, image = page.images[0], url = page.url, content = page.contentl, link = page.links[0])



@app.route('/_autocomplete', methods=['GET'])
def autocomplete():
    search = request.args.get('term')
    # app.logger.debug(search)
    return jsonify(university_list=university_list)


if __name__ == '__main__':
    app.run(threaded=True, host='0.0.0.0', debug=True)