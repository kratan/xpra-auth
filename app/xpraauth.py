#!flask/bin/python
# Infos from:
# https://flask-restful.readthedocs.io/en/0.3.5/
# https://blog.miguelgrinberg.com/post/designing-a-restful-api-using-flask-restful
# Stackoverflow Posts

from flask import Flask, jsonify, abort, make_response
from flask_restful import Api, Resource, reqparse, fields, marshal
from os.path import expanduser
import os
import uuid
import logging
import sys
import argparse

application = Flask(__name__, static_url_path="")
api = Api(application)


# Static
xpra_auth_file = 'xpra_auth_file'
xpra_auth_dir = '/xprafile'
xpra_auth_log = 'xpraauth.log'


# Argument Parser + Logging Stuff to current user....
parser = argparse.ArgumentParser()
parser.add_argument("--debug", help="enable debugging")
args = parser.parse_args()
if args.debug:
    logging.basicConfig(
    filename= os.path.join(xpra_auth_dir,xpra_auth_log),
    format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
    datefmt="%d-%m-%Y %H:%M:%S", stream=sys.stdout,
    level=logging.DEBUG,)
    logging.info("Xpra Authenticator started in Debug mode...")
else:
    logging.basicConfig(
        filename=os.path.join(xpra_auth_dir, xpra_auth_log),
        format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S", stream=sys.stdout,)

# Fields
TARGETHOSTS = [
]

TARGETHOST_FIELDS = {
    'targethostUUID': fields.String,
    'username': fields.String,
    'password': fields.String,
    'targethost': fields.String,
}

TARGETHOST_FIELDS_ID = {
    'id': fields.String(attribute='targethostUUID'),
}

# Read and check File before first request
@application.before_first_request
# Check if File is there
def startup_filecheck():
    result = OtherStuff.filecheck()
    if result > 0:
       logging.critical('Filechecking Error')
       abort(500)

# Read xpra_auth_file
@application.before_first_request
def startup_readxprafile():
    result = OtherStuff.read_xpra_auth_to_rest()
    if result > 0:
       logging.critical('Xpra read auth file Error')
       abort(500)


# Writing, Checking, Reading, Deleting, Updating xpra auth file
class OtherStuff(Resource):

    @classmethod
    def filecheck(self):
            try:
                if not os.path.exists(os.path.join(xpra_auth_dir,xpra_auth_file)):
                    open(os.path.join(xpra_auth_dir,xpra_auth_file), 'w').close()
                return 0
            except IOError:
                print "Error: File does not appear to exist."
                return 1

    @classmethod
    def read_xpra_auth_to_rest(self):
            try:
                with open(os.path.join(xpra_auth_dir, xpra_auth_file), 'r') as auth_file:
                    for line in auth_file:
                        if not line.count('|') == 6:
                            logging.warning("No lines in " + xpra_auth_file)
                            return 1

                        #Delemiter Line
                        line_splitted = line.split('|', )

                        # splitted should be count 6
                        if len(line_splitted) != 7:
                            logging.warning("Line found, but not right formatted")
                            return 2

                        else:
                            # ['test2', 'pw1', '', '', '12.12.12.12:1111', 'target_hostUUID=4fffaaec-254a-425b-bc9a-5ccf0845b6fb', '\n']
                            target_username = line_splitted[0]
                            if not len(target_username) > 0:
                                logging.warning("Username is length 0, cant be!")
                                return 3

                            target_password = line_splitted[1]
                            if not len(target_password) > 0:
                                logging.warning("Password is length 0, cant be!")
                                return 4

                            target_host = line_splitted[4]
                            if not len(target_password) > 0:
                                logging.warning("Targethost is length 0, cant be!")
                                return 5

                            target_hostUUID = line_splitted[5].split('=',1)[1]
                            targethost = {
                                'targethostUUID': target_hostUUID,
                                'username': target_username,
                                'password': target_password,
                                'targethost': target_host,
                            }
                            targethost = marshal(targethost,TARGETHOST_FIELDS)
                            TARGETHOSTS.append(targethost)
                            logging.info("Added to TARGETHOST: " + str(targethost))

                auth_file.close()
                return 0
            except IOError as e:
                logging.critical("I/O error({0}): {1}".format(e.errno, e.strerror) + xpra_auth_file)
                return 6


    @classmethod
    def write_xpra_file(self,target_username,target_password,connectionstring,target_hostUUID):
            try:
                with open(os.path.join(xpra_auth_dir, xpra_auth_file), 'a') as auth_file:
                    string_to_write = '%s|%s|||%s|target_hostUUID=%s|' % (target_username, target_password, connectionstring,target_hostUUID)
                    auth_file.write(string_to_write + os.linesep)
                    auth_file.close()
                    logging.info(string_to_write + ' to ' + os.environ['HOME'] + '/ ' + xpra_auth_file)
                    return 0
            except IOError as e:
                logging.critical("I/O error({0}): {1}".format(e.errno, e.strerror) + ' ' + xpra_auth_file)
                return 1

    @classmethod
    def delete_item_xpra_file(self,target_hostUUID):
        try:
            # Open First Time to read lines
            with open(os.path.join(xpra_auth_dir, xpra_auth_file), 'r') as auth_file:
                lines = auth_file.readlines()
                auth_file.close()
                # Open Second Time to write lines without target_hostUUID
                auth_file = open(os.path.join(xpra_auth_dir, xpra_auth_file), 'w')
                for line in lines:
                    if not target_hostUUID in line:
                        auth_file.write(line)
                auth_file.close()
                logging.info('Deleted ' + target_hostUUID + ' from ' + os.path.join(xpra_auth_dir, xpra_auth_file))
                return 0
        except IOError as e:
            logging.critical("I/O error({0}): {1}".format(e.errno, e.strerror) + ' ' + xpra_auth_file)
            return 1


    @classmethod
    def update_item_xpra(self,target_hostUUID,target_username,target_password,connectionstring):
            result = OtherStuff.delete_item_xpra_file(target_hostUUID)
            if result > 0:
                abort(500)
            OtherStuff.write_xpra_file(target_username,target_password,connectionstring,target_hostUUID)
            if result > 0:
                abort(500)



class TargethostListAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('username', type=str, required=True,
                                   location='json')
        self.reqparse.add_argument('password', type=str, required=True,
                                   location='json')
        self.reqparse.add_argument('targethost', type=str, required=True,
                                   location='json')
        super(TargethostListAPI, self).__init__()

    def get(self):
        targethost = [ targethost['targethostUUID'] for targethost in TARGETHOSTS ]
        if len(targethost) == 0:
            abort(404)
            logging.warning("Not found!")
        logging.info("GET: " + str(targethost))
        return [marshal(targethost, TARGETHOST_FIELDS_ID) for targethost in TARGETHOSTS],201

    def post(self):
        args = self.reqparse.parse_args()
        tempuuid = str(uuid.uuid4())
        targethost = {
            'targethostUUID': tempuuid,
            'username': args['username'],
            'password': args['password'],
            'targethost': args['targethost'],
        }
        TARGETHOSTS.append(targethost)
        OtherStuff.write_xpra_file(args['username'], args['password'], args['targethost'], tempuuid)
        logging.info("POST: " + str(targethost))
        return marshal(targethost, TARGETHOST_FIELDS_ID), 201


class TargethostAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('targethostUUID', type=str, location='json')
        self.reqparse.add_argument('username', type=str, location='json')
        self.reqparse.add_argument('password', type=str, location='json')
        self.reqparse.add_argument('targethost', type=str, location='json')
        super(TargethostAPI, self).__init__()

    def get(self, targethostuuid):
        targethost = [targethost for targethost in TARGETHOSTS if targethost['targethostUUID'] == targethostuuid]
        if len(targethost) == 0:
            abort(404)
            logging.warning("GET Not found: " + targethostuuid)
        return marshal(targethost[0], TARGETHOST_FIELDS),201


    def post(self, targethostuuid):
        targethost = [targethost for targethost in TARGETHOSTS if targethost['targethostUUID'] == targethostuuid]
        if len(targethost) == 0:
            abort(404)
            logging.warning("POST/PUT Not found: " + targethostuuid)
        targethost = targethost[0]
        args = self.reqparse.parse_args()
        for k, v in args.items():
            if v is not None:
                if k == 'username':
                    username = v
                if k == 'password':
                    password = v
                if k == 'targethost':
                    target_host = v
                targethost[k] = v
        OtherStuff.update_item_xpra(targethostuuid,username,password,target_host)
        logging.info("POST: " + str(targethost))
        return marshal(targethost, TARGETHOST_FIELDS_ID),201

    def delete(self, targethostuuid):
        targethost = [targethost for targethost in TARGETHOSTS if targethost['targethostUUID'] == targethostuuid]
        if len(targethost) == 0:
            abort(404)
            logging.warning("DELETE Not found: " + targethostuuid)
        OtherStuff.delete_item_xpra_file(targethostuuid)
        logging.info("DELETE: " + str(targethost))
        TARGETHOSTS.remove(targethost[0])
        return "No Data", 201

    def __format__(self, format_spec):
        return super(TargethostAPI, self).__format__(format_spec)

    def put(self, targethostuuid):
        return TargethostAPI.post(self,targethostuuid),201


api.add_resource(TargethostListAPI, '/api/1/targethosts', endpoint='targethosts')
api.add_resource(TargethostAPI, '/api/1/targethosts/<targethostuuid>', endpoint='targethost')


if __name__ == '__main__':

    # Start Program
    application.run()


