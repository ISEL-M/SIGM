# to use accented characters in the code
# -*- coding: cp1252 -*-
# ===============================
# author: Paulo Trigo Silva (PTS)
# ver: v01 (Python3.7.2)
# ===============================


#______________________________________________________________________________
# Imported modules
import http.server
import urllib.parse as urlparse
import socketserver
import re
import psycopg2
import json


# ______________________________________________________________________________
# Utility Constants
# HTTP server information
HOST = 'localhost'
PORT = 8080


# ______________________________________________________________________________
# Connectivity Constants
# database to connect to
DATABASE = {
  'user':     'postgres',
  'password': 'postgres',
  'host':     'localhost',
  'port':     '5432',
  'database': 'my_gis'
  }

# what to include in the tiles:
# - table and columns
# 
# also 'layer_name', which is any name but:
# - must be the same as the one used in MapLibre (Web client)
#
# to get 'srid' and 'geom_column' value - just ask the database!
# e.g., at pgAdmin go to the database and execute:
# - SELECT * FROM geometry_columns
KEY_TABLE_NAME =  'table_name'
KEY_LAYER_NAME =  'layer_name'
KEY_GEOM_COLUMN = 'geom_column'
KEY_SRID =        'srid'
KEY_PROPERTIES =  'properties'

TABLE_DEFAULT = {
  KEY_TABLE_NAME:   'public.ne_50m_admin_0_countries',
  KEY_LAYER_NAME:   'public.ne_50m_admin_0_countries',
  KEY_GEOM_COLUMN:  'geom',
  KEY_SRID:         '4326',
  KEY_PROPERTIES:   'formal_en,name_pt,pop_est'
  }  



#______________________________________________________________________________
#______________________________________________________________________________
# Classes

# ______________________________________________________________________________
# 
class Database:
  __connection = None

  # get and hold a connection to the database
  @classmethod
  def getConnection(cls):
    if cls.__connection:
      if not cls.__connection.closed:
        return cls.__connection
    try:
      cls.__connection = psycopg2.connect(**DATABASE)
      print( "\nPTS| database connection OK: %s" % (cls.__connection))
    except (Exception, psycopg2.Error) as error:
      print( "\nPTS| database connection: ERROR: %s" % (str(error)))
    return cls.__connection


  # run tile query SQL and return error on failure
  # return the first row and column in cursor
  # (the vector-tile is all condensed in a single row)
  # returns a tuple of (error, data)
  @classmethod
  def execute(cls, sql):
    error = 0; data = 1
    result = [None, None]
    # get connection to database
    connection = cls.getConnection()
    if not connection:
      result[error] = "PTS| cannot-connect: %s" % (str(DATABASE))
      return tuple(result)
    
    # execute SQL and return first row (and column)
    # connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    # (the above line may substitute the explicit commit/rollback implemented below)
    with connection.cursor() as cursor:
      try:
        cursor.execute(sql)
        if cursor:
          row = cursor.fetchone()
          if len(row) > 0:
            result[data] = row[0]
          connection.commit()
      except (Exception, psycopg2.Error) as e:
        result[error] = "PTS| sql-query problem: %s" % (e)
        connection.rollback()
    
    return tuple(result)


  # close database connection
  @classmethod
  def disconnect(cls):
    if cls.__connection:
      if not cls.__connection.closed:
        cls.__connection.close()
        cls.__connection = None
        print( "PTS| database connection is now closed!" )
        return
    cls.__connection = None
    print("PTS| database connection was already closed!")



# ______________________________________________________________________________
class Table:
  def __init__(self, path):
    self.__setAllDefault()
    self.__parse(path)


  def __setAllDefault(self):
    self.tableName =  TABLE_DEFAULT[KEY_TABLE_NAME]
    self.layerName =  TABLE_DEFAULT[KEY_LAYER_NAME]
    self.geomColumn = TABLE_DEFAULT[KEY_GEOM_COLUMN]
    self.srid =       TABLE_DEFAULT[KEY_SRID]
    self.properties = TABLE_DEFAULT[KEY_PROPERTIES]


  # get "table data" from path pattern:
  # /table_name/{z}/{x}/{y}.{format}?properties=attr1,...,attrN & geom_column=name & srid=srid
  def __parse(self, path):
    # update "tableName" from url-path
    regExp = '^\/([0-9a-zA-Z_\-\.]+)' + TileXYZ.regExp
    result = re.search(regExp, path)
    if result:
      self.tableName = result.group(1)
      self.layerName = self.tableName

    # update "geomColumn", "srid", "properties" from url-query-parameters
    url_parsed = urlparse.urlparse(path)
    url_query = urlparse.parse_qs(url_parsed.query)
    # print(url_parsed)
    # print(url_query)

    self.geomColumn = self.__getValue(url_query, KEY_GEOM_COLUMN, self.geomColumn)
    self.srid = self.__getValue(url_query, KEY_SRID, self.srid)
    self.properties = self.__getValue(url_query, KEY_PROPERTIES, self.properties)


  def __getValue(self, dictionary, key, defaultValue):
    value = dictionary.get(key, None)
    if (value): return value[0]
    return defaultValue


  # string representation of class instances
  def __str__(self):
    result = ""
    result += "PTS| self.tableName=#%s#" % (self.tableName) + "\n"
    result += "PTS| self.layerName=#%s#" % (self.layerName) + "\n"
    result += "PTS| self.geomColumn=#%s#" % (self.geomColumn) + "\n"
    result += "PTS| self.srid=#%s#" % (self.srid) + "\n"
    result += "PTS| self.properties=#%s#" % (self.properties) + "\n"
    return result



# ______________________________________________________________________________
class TileXYZ:
  regExp = '\/(\d+)\/(\d+)\/(\d+)\.(\w+)'

  def __init__(self, path):
    self.__setAllNone()
    self.__parse(path)
    if not self.isValid(): self.__setAllNone()


  # assign None to all instance variables
  def __setAllNone(self):
    self.x = self.y = self.z = self.format = None


  # is defined if there are no None values
  def __isDefined(self):
    return ((None != self.x) and (None != self.y) and 
            (None != self.z) and (None != self.format))


  # get "x, y, z, format" tile info from url-path pattern:
  # /{z}/{x}/{y}.{format}
  def __parse(self, path):
    # check at:
    # https://pythex.org/
    result = re.search(TileXYZ.regExp, path)
    if not result: return

    self.z =      int(result.group(1))
    self.x =      int(result.group(2))
    self.y =      int(result.group(3))
    self.format = result.group(4)


  # validate tileXYZ:
  # - x, y, z, format are not missing
  # - x, y coordinates make sense at this zoom level
  # - format, admissible if 'pbf' or 'mvt'
  def isValid(self):
    if not self.__isDefined(): return False
    if self.format not in ['pbf', 'mvt']: return False
    <your-code-here>


  # string representation of class instances
  def __str__(self):
    if not self.__isDefined(): return "PTS|tileXYZ-undefined"
    return "/" + str(self.z) + "/" + str(self.x) + "/" + str(self.y) + "." + self.format



# ______________________________________________________________________________
class TileEnvelope:
  # width (=height) of world in EPSG:3857 (Mercator)
  maxWorldMercator = 20037508.3427892
  minWorldMercator = -1 * maxWorldMercator
  widthWorldMercator = maxWorldMercator - minWorldMercator

  # calculate envelope in
  # - Spherical Mercator, or, Pseudo-Mercator, or, WGS 84
  # also used by: Google Maps, OpenStreetMap, Bing, ArcGIS, ESRI
  #
  # PostGIS offers ST_TileEnvelope function, but:
  # - we implement it here as an academical goal
  # cf., https://postgis.net/docs/ST_TileEnvelope.html
  # cf., https://epsg.io/3857
  def __init__(self, tile):
    # width (=height) if world in tiles at "zoom" level
    # i.e., number of tiles per side at a zoom-level
    widthWorldTile = 2 ** tile.z

    # width (=height) of tile in EPSG:3857 (Mercator)
    widthTileMercator = TileEnvelope.widthWorldMercator / widthWorldTile

    # from tile coordinates (x and y) calculate geographic envelope (bounding-box)
    # notice that XYZ tile coordinates are in "image space", so:
    # - origin is top-left (not bottom-right)
    <your-code-here>


# ______________________________________________________________________________
class SQL:
  # get SQL to query PostGIS for a tile from the (configured) table
  # "Map Vector Tile" = MVT
  def SELECTmapVectorTile(table, tileEnvelope):
    # build a dictionary of parameters to be used in the SELECT:
    # - the "table" instance variables, and
    # - the sql that generates the envelope
    parameterData = vars(table)
    parameterData['envelope'] = SQL.SELECTenvelope(tileEnvelope)

    # build the 'envelope' (bounding-box)
    # select geometry and clip to 'envelope' ( bounding-box)
    # convert geometry to MVT (Map Vector Tile) format
    # assign 'layerName' that must also be used by Web client (e.g., MapLibre)
    # (the 'layerName' is assumed to be the same as the 'tableName')
    sql = \
    """
      WITH

      bounding_box AS (
        SELECT {envelope} AS geom, {envelope}::box2d AS b2d
      ),

      geom_mvt AS (
        SELECT ST_AsMVTGeom(ST_Transform(t.{geomColumn}, 3857), bounding_box.b2d) AS geom, 
               {properties}
        FROM {tableName} t, bounding_box
        WHERE ST_Intersects(t.{geomColumn}, ST_Transform(bounding_box.geom, {srid}))
      ) 

      <your-code-here>
    """
    sql = sql.format(**parameterData)
    return sql



  # SQL to get the boundingBox of geometry in EPSG:3857 (Mercator)
  # densify (a little) the edges so that the envelope:
  # - can be safely converted to other coordinate systems
  def SELECTenvelope(tileEnvelope):
    DENSIFY_FACTOR = 1.0/4.0
    parameterData = vars(tileEnvelope)
    parameterData['sizeSegment'] = (tileEnvelope.xMax - tileEnvelope.xMin) * DENSIFY_FACTOR
    sql = \
    """
      <your-code-here>
    """
    sql = sql.format(**parameterData)
    return sql




# ______________________________________________________________________________
class TileMapRequestHandler( http.server.BaseHTTPRequestHandler ):
  # handle HTTP GET request
  # cf., https://docs.python.org/3/library/http.server.html
  def do_GET(self):
    print("PTS| GET <<<")

    # from the request (get) url (path) parse the XYZ format
    self.log_message("PTS| url-path: #%s#" % (self.path))
    tileXYZ = TileXYZ(self.path)
    self.log_message("PTS| tileXYZ: #%s#" % (tileXYZ))

    if not tileXYZ.isValid():
      self.send_error(400, "PTS| invalid tileXYZ: %s" % (self.path))
      return

    # build SQL to get MVT using table setup and titleEnvelope
    table = Table(self.path)
    tileEnvelope = TileEnvelope(tileXYZ)
    sql = SQL.SELECTmapVectorTile(table, tileEnvelope)
    print(table)
    print(sql)

    # execute SQL-query
    (error, data) = Database.execute(sql)
    if error or not data:
      self.send_error(500, error)
      return

    # send-reply
    self.send_response(200)
    self.send_header("Access-Control-Allow-Origin", "*")
    self.send_header("Content-type", "application/vnd.mapbox-vector-tile")
    self.end_headers()
    self.wfile.write(data)
    #self.replyTest()


  # test of a simple reply of a pre-defined text
  def replyTest(self):
    self.send_response(200)
    self.send_header("Content-type", "text/html")
    self.end_headers()
    self.wfile.write(bytes("<html><head><title>PTS|test</title></head>", "utf-8"))
    self.wfile.write(bytes("<p>Request: %s</p>" % self.path, "utf-8"))
    self.wfile.write(bytes("<body>", "utf-8"))
    self.wfile.write(bytes("<p>PTS| a Web-Server example!</p>", "utf-8"))
    self.wfile.write(bytes("</body></html>", "utf-8"))



#______________________________________________________________________________
#______________________________________________________________________________
def serveForever():
  webServer = http.server.HTTPServer((HOST, PORT), TileMapRequestHandler)
  print("\nPTS: | server-started | http://%s:%s" % (HOST, PORT))

  try: webServer.serve_forever()
  except KeyboardInterrupt: pass

  webServer.socket.close()
  webServer.server_close()
  print("\nPTS: server stopped!")



#______________________________________________________________________________
#______________________________________________________________________________
def main():
  # print(Database.getConnection())
  # Database.disconnect()
  # Database.disconnect()
  serveForever()



#_______________________________________________________________________________
#_______________________________________________________________________________
# the main of this module (in case this module is imported from another module)
if __name__=="__main__":
   main()
